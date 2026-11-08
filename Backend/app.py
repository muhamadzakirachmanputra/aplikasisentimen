# Backend/app.py
import os
import sys
import joblib

# Pastikan folder Backend dan Root masuk sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import uuid
import pandas as pd
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from math import ceil
from config import APP_SECRET_KEY
from ml_pipeline import preprocess_detail, train_and_evaluate, predict_with_model
from pdf_generator import generate_pdf_report
from db_service import (
    get_db,save_upload_record, save_data_raw, save_data_preprocessing,
    save_model_result, save_prediksi, get_prediksi_stats,
    log_activity, get_comparison_report, get_model_results,
    get_data_raw, get_data_preprocessing, get_prediksi, get_latest_upload,
    save_tfidf_features, get_tfidf_features, get_tfidf_for_document,
    get_data_raw_paged, delete_model_results
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")

TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "Website", "html")
STATIC_DIR = os.path.join(PROJECT_ROOT, "Website", "static")

try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
except OSError:
    # Lingkungan serverless Vercel (read-only filesystem)
    UPLOAD_DIR = "/tmp/uploads"
    PROCESSED_DIR = "/tmp/processed"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = APP_SECRET_KEY

# Konfigurasi cookie session agar aman & tidak hilang saat redirect di HTTPS Vercel
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def require_login():
    return session.get("login") is True

def require_admin():
    return session.get("role") == "admin"


def load_processed_df():
    """Ambil dataframe hasil preprocess dari file berdasarkan proc_id di session."""
    proc_id = session.get("proc_id")
    if not proc_id:
        return None

    proc_path = os.path.join(PROCESSED_DIR, f"{proc_id}.csv")
    if not os.path.exists(proc_path):
        return None

    return pd.read_csv(proc_path)


@app.route("/auto-login")
def auto_login():
    session["login"] = True
    session["username"] = "admin"
    session["role"] = "admin"
    latest_upload = get_latest_upload()
    if latest_upload:
        upload_id = latest_upload["upload_id"]
        session["upload_id"] = upload_id
        session["csv_filename"] = latest_upload["filename"]
        try:
            processed_files = os.listdir(PROCESSED_DIR)
            for file in sorted(processed_files, reverse=True):
                if file.endswith(".csv"):
                    session["proc_id"] = file.replace(".csv", "")
                    break
        except Exception:
            pass
    return redirect(url_for("dashboard"))


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        pw = request.form.get("password", "")

        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (user, pw))
            admin = cur.fetchone()

        if admin:
            session["login"] = True
            session["username"] = admin.get("username", user)
            # Default to checking column, fallback to username check if DB not updated yet
            session["role"] = admin.get("role", "admin" if user == "admin" else "user")
            
            # V Load latest upload data dari database untuk restore session
            latest_upload = get_latest_upload()
            if latest_upload:
                upload_id = latest_upload["upload_id"]
                session["upload_id"] = upload_id
                session["csv_filename"] = latest_upload["filename"]
                
                # Try to find processed file for this upload
                try:
                    processed_files = os.listdir(PROCESSED_DIR)
                    for file in sorted(processed_files, reverse=True):
                        if file.endswith(".csv"):
                            session["proc_id"] = file.replace(".csv", "")
                            break
                except Exception as e:
                    print(f"Error loading processed file: {e}")
                
                # V Coba restore result klasifikasi dari database ke session
                try:
                    models = get_model_results(upload_id=upload_id, limit=1)
                    if models:
                        model_db = models[0]
                        # Fetch prediksi untuk recreate report & confusion matrix
                        prediksi = get_prediksi(model_id=model_db.get("id"))
                        if prediksi:
                            df_pred = pd.DataFrame(prediksi)
                            
                            # Pastikan data ada dan kolom sesuai
                            if not df_pred.empty and "label_asli" in df_pred.columns and "prediksi_svm" in df_pred.columns:
                                valid_idx = df_pred.dropna(subset=["label_asli", "prediksi_svm"]).index
                                y_true = df_pred.loc[valid_idx, "label_asli"]
                                y_pred = df_pred.loc[valid_idx, "prediksi_svm"]

                                # Load the correct report that was evaluated only on the 30% test set
                                import json
                                try:
                                    report_path = os.path.join(PROCESSED_DIR, "saved_model", "slim_report.json")
                                    with open(report_path, "r") as f:
                                        report = json.load(f)
                                except Exception:
                                    from sklearn.metrics import classification_report
                                    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
                                
                                from sklearn.metrics import confusion_matrix
                                cm = confusion_matrix(y_true, y_pred)
                                # Hitung label_counts dari SELURUH data preprocessing (bukan hanya prediksi/test)
                                from db_service import get_data_preprocessing
                                all_preproc = get_data_preprocessing(upload_id)
                                if all_preproc:
                                    df_all = pd.DataFrame(all_preproc)
                                    label_counts = {str(k): int(v) for k, v in df_all["label"].value_counts().to_dict().items()}
                                    total_data = len(df_all)
                                else:
                                    label_counts = {str(k): int(v) for k, v in y_true.value_counts().to_dict().items()}
                                    total_data = len(y_true)
                                
                                # Hitung train/test split (70:30)
                                train_count = int(round(total_data * 0.7))
                                test_count = total_data - train_count
                                
                                session["result"] = {
                                    "accuracy": float(model_db.get("accuracy", 0)),
                                    "precision": float(model_db.get("precision_val", 0)),
                                    "recall": float(model_db.get("recall_val", 0)),
                                    "f1": float(model_db.get("f1_val", 0)),
                                    "confusion_img": "cm_heatmap.png",
                                    "roc_img": "wordcloud.png",
                                    "report": report,
                                    "label_counts": label_counts,
                                    "model_id": model_db.get("id"),
                                    "confusion_matrix": cm.tolist(),
                                    "train_count": train_count,
                                    "test_count": test_count,
                                }
                                print("[DEBUG] Berhasil merekonstruksi session 'result' dari database.")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"Error meregister ulang model result ke session: {e}")
            
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Username / password salah.")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form.get("username", "")
        pw = request.form.get("password", "")
        
        if not user or not pw:
            return render_template("register.html", error="Username dan password harus diisi.")
            
        conn = get_db()
        try:
            with conn.cursor() as cur:
                # Cek dulu apakah username sudah ada
                cur.execute("SELECT id FROM admin WHERE username=%s", (user,))
                if cur.fetchone():
                    return render_template("register.html", error="Username sudah terdaftar, silakan gunakan yang lain.")
                    
                # Tentukan role (jika username mengandung kata 'admin', jadikan dia admin)
                role_to_assign = "admin" if "admin" in user.lower() else "user"

                # Insert user baru dengan role=user/admin (asumsi kolom role ada, jika belum ada biarkan fallback)
                try:
                    cur.execute(
                        "INSERT INTO admin (username, password, role) VALUES (%s, %s, %s)",
                        (user, pw, role_to_assign)
                    )
                except Exception as e:
                    # Fallback jika kolom role belum ditambahkan oleh user via XAMPP
                    cur.execute(
                        "INSERT INTO admin (username, password) VALUES (%s, %s)",
                        (user, pw)
                    )
                conn.commit()
            return render_template("register.html", success="Pendaftaran berhasil! Silakan login.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return render_template("register.html", error=f"Terjadi kesalahan sistem: {str(e)}")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def perform_full_reset():
    """Reset total seluruh data upload, preprocessing, model result, session, dan file cache."""
    session.pop("upload_id", None)
    session.pop("proc_id", None)
    session.pop("result", None)
    session.pop("csv_filename", None)

    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM data_upload")
            cur.execute("DELETE FROM user_activity")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[RESET ALL] Error clearing DB: {e}")

    for dir_path in [PROCESSED_DIR, UPLOAD_DIR]:
        if os.path.exists(dir_path):
            for root, dirs, files in os.walk(dir_path, topdown=False):
                for fname in files:
                    try:
                        os.remove(os.path.join(root, fname))
                    except Exception as e:
                        print(f"[RESET ALL] Error removing file {fname}: {e}")

    for img_name in ["cm_heatmap.png", "wordcloud.png"]:
        img_path = os.path.join(STATIC_DIR, img_name)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                print(f"[RESET ALL] Error removing img {img_name}: {e}")


@app.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("login"))
    return render_template("dashboard.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not require_login():
        return redirect(url_for("login"))
    if not require_admin():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        try:
            f = request.files.get("file")
            if not f or f.filename == "":
                return render_template("upload.html", error="Pilih file CSV dulu.")

            # Reset seluruh data lama (DB, session, dan cache file) sebelum upload baru
            perform_full_reset()

            # V Generate upload_id baru
            upload_id = str(uuid.uuid4())

            # V Save file
            save_path = os.path.join(UPLOAD_DIR, f.filename)
            f.save(save_path)

            # V Read CSV
            try:
                df = pd.read_csv(save_path)
            except Exception as e:
                return render_template("upload.html", error=f"Error membaca CSV: {str(e)}")

            # V Validasi minimal kolom (case-insensitive)
            required = {"username", "score", "at", "content"}
            cols_lower = {c.lower() for c in df.columns}
            if not required.issubset(cols_lower):
                return render_template(
                    "upload.html",
                    error=f"Kolom CSV harus ada: {sorted(required)}. Kolom kamu: {df.columns.tolist()}"
                )

            # Generate label otomatis berdasarkan score
            def classify_sentiment(score):
                if pd.isna(score):
                    return "netral"
                try:
                    score = float(score)
                    if score >= 4:
                        return "positif"
                    elif score == 3:
                        return "netral"
                    else:
                        return "negatif"
                except:
                    return "netral"
                    
            df["label"] = df["score"].apply(classify_sentiment)

            # V Simpan upload record
            ok = save_upload_record(upload_id, f.filename, len(df))
            if not ok:
                return render_template("upload.html", error="Gagal menyimpan record upload ke database.")

            # V Simpan data raw
            ok = save_data_raw(upload_id, df)
            if not ok:
                return render_template("upload.html", error="Gagal menyimpan data raw ke database.")

            log_activity("upload_file", upload_id, f"Upload file: {f.filename}")

            # V Preprocess
            try:
                dfp = preprocess_detail(df)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return render_template("upload.html", error=f"Gagal preprocessing: {str(e)}")

            if dfp is None or len(dfp) == 0:
                return render_template(
                    "upload.html",
                    error="Tidak ada data valid setelah preprocessing. Cek kolom content/label."
                )

            # V simpan hasil preprocess ke file server (CSV)
            proc_id = str(uuid.uuid4())
            proc_path = os.path.join(PROCESSED_DIR, f"{proc_id}.csv")
            dfp.to_csv(proc_path, index=False)

            # ==========================================================
            # V AMBIL RAW ID + CONTENT LANGSUNG DARI DB (FULL, BUKAN paging)
            # Ini menghindari konflik karena get_data_raw() kamu sudah paginated.
            # ==========================================================
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, content FROM data_raw WHERE upload_id=%s ORDER BY id ASC",
                    (upload_id,)
                )
                raw_rows = cur.fetchall()
            conn.close()

            if not raw_rows:
                return render_template("upload.html", error="Data raw tidak ditemukan setelah insert. Cek DB.")

            # ==========================================================
            # V Mapping content -> list raw_id (biar aman kalau duplicate content)
            # ==========================================================
            from collections import defaultdict
            content_to_ids = defaultdict(list)
            raw_ids_in_order = []

            for r in raw_rows:
                rid = r.get("id")
                raw_ids_in_order.append(rid)
                key = str(r.get("content") or "").strip().lower()
                content_to_ids[key].append(rid)

            dfp_with_ids = dfp.copy()

            # preprocess_detail kamu bikin kolom content_raw
            # pastikan ada:
            if "content_raw" not in dfp_with_ids.columns:
                # fallback kalau ternyata tidak ada
                dfp_with_ids["content_raw"] = dfp_with_ids.get("content", "")

            def pick_raw_id(text):
                key = str(text or "").strip().lower()
                if key in content_to_ids and content_to_ids[key]:
                    return content_to_ids[key].pop(0)  # ambil satu per satu
                return None

            dfp_with_ids["data_raw_id"] = dfp_with_ids["content_raw"].apply(pick_raw_id)

            # V Fallback urutan kalau masih ada None (misal karena cleaning beda)
            missing_mask = dfp_with_ids["data_raw_id"].isna()
            if missing_mask.any():
                missing_idx = list(dfp_with_ids.index[missing_mask])
                for i, idx in enumerate(missing_idx):
                    # amanin index range
                    if idx < len(raw_ids_in_order):
                        dfp_with_ids.at[idx, "data_raw_id"] = raw_ids_in_order[idx]

            print("[DEBUG] upload_id:", upload_id)
            print("[DEBUG] raw_rows:", len(raw_rows), "dfp:", len(dfp_with_ids))
            print("[DEBUG] missing data_raw_id:", int(dfp_with_ids["data_raw_id"].isna().sum()))

            # V Simpan preprocessing ke DB
            ok = save_data_preprocessing(upload_id, dfp_with_ids)
            if not ok:
                return render_template("upload.html", error="Gagal menyimpan data preprocessing ke database.")

            # V Session
            session["proc_id"] = proc_id
            session["upload_id"] = upload_id
            session["csv_filename"] = f.filename

            preview = dfp.head(10).to_dict(orient="records")
            return render_template("preprocessing.html", preview=preview, total=len(dfp))

        except Exception as e:
            import traceback
            traceback.print_exc()
            return render_template("upload.html", error=f"Terjadi error: {str(e)}")

    return render_template("upload.html")


@app.route("/preprocessing")
def preprocessing():
    if not require_login():
        return redirect(url_for("login"))

    dfp = load_processed_df()
    if dfp is None:
        return redirect(url_for("upload"))

    preview = dfp.head(10).to_dict(orient="records")
    return render_template("preprocessing.html", preview=preview, total=len(dfp))


@app.route("/fitur")
def fitur():
    """Redirect ke klasifikasi - fitur sudah digabung"""
    return redirect(url_for("klasifikasi"))



@app.route("/klasifikasi", methods=["GET", "POST"])
def klasifikasi():
    if not require_login():
        return redirect(url_for("login"))
    if not require_admin():
        return redirect(url_for("dashboard"))

    # GET: Tampilkan form klasifikasi
    if request.method == "GET":
        dfp = load_processed_df()
        if dfp is None:
            return redirect(url_for("upload"))

        upload_id = session.get("upload_id")
        return render_template("klasifikasi.html", upload_id=upload_id, data_count=len(dfp))

    # POST: Jalankan klasifikasi
    dfp = load_processed_df()
    if dfp is None:
        return redirect(url_for("upload"))

    upload_id = session.get("upload_id")

    # Train + Evaluate + Save images
    result = train_and_evaluate(dfp, STATIC_DIR)

    # label_counts buat halaman hasil.html (biar tojson gak error)
    label_counts = {str(k): int(v) for k, v in dfp["label"].value_counts().to_dict().items()}

    # V Simpan hasil model ke database
    model_id = save_model_result(
        upload_id,
        result.get("accuracy"),
        result.get("precision"),
        result.get("recall"),
        result.get("f1"),
        result.get("feature_count"),
        len(dfp),
        None  # model_path
    )
    
    # Debug log
    print(f"[DEBUG] Model saved: model_id={model_id}, upload_id={upload_id}")
    if not model_id:
        print(f"[WARNING] Failed to save model result!")
        return render_template("klasifikasi.html", error="Gagal menyimpan hasil model ke database")

    # V Simpan TF-IDF features ke database
    preprocessing_data = get_data_preprocessing(upload_id)
    if preprocessing_data and result.get("X_tfidf") is not None:
        save_tfidf_features(
            upload_id,
            preprocessing_data,
            result.get("X_tfidf"),
            result.get("feature_names", [])
        )
        print(f"[DEBUG] TF-IDF features saved!")

    # V Dapatkan model dan vectorizer dari hasil training sebelumnya (di train_and_evaluate)
    vectorizer = result.get("vectorizer")
    model = result.get("model")
    
    # V Simpan model + vectorizer ke disk untuk fitur Uji Sentimen
    model_save_dir = os.path.join(PROCESSED_DIR, "saved_model")
    os.makedirs(model_save_dir, exist_ok=True)
    joblib.dump(model, os.path.join(model_save_dir, "svm_model.joblib"))
    joblib.dump(vectorizer, os.path.join(model_save_dir, "tfidf_vectorizer.joblib"))
    print(f"[DEBUG] Model & Vectorizer saved to {model_save_dir}")
    
    # Prediksi untuk semua data
    X_all = vectorizer.transform(dfp["stemming"])
    svm_predictions = model.predict(X_all).tolist()
    
    # Handle confidence scores (decision_function returns 2D array for multi-class)
    decision_scores = model.decision_function(X_all)
    if len(decision_scores.shape) == 2:
        # Multi-class: take max absolute value from each row
        svm_confidence = [float(max(abs(x) for x in row)) for row in decision_scores.tolist()]
    else:
        # Binary class: take absolute value directly
        svm_confidence = [float(abs(score)) for score in decision_scores.tolist()]

    # V Simpan prediksi ke database
    if preprocessing_data and len(preprocessing_data) > 0:
        save_prediksi(upload_id, model_id, preprocessing_data, svm_predictions, svm_confidence)
        print(f"[DEBUG] SVM predictions saved!")
    
    # V Log activity
    log_activity("train_model", upload_id, f"Model trained with accuracy: {result.get('accuracy'):.2%}")

    # simpan hasil ke session (dikurangi agar tidak melebihi batas cookie 4KB)
    # Template evaluasi.html membangun tabel dari report dict langsung
    full_report = result.get("report", {})
    # Hanya simpan key yang dibutuhkan template
    slim_report = {}
    for key in ['negatif', 'netral', 'positif', 'negative', 'neutral', 'positive', 'macro avg', 'weighted avg']:
        if key in full_report:
            slim_report[key] = full_report[key]

    session["result"] = {
        "accuracy": float(result.get("accuracy", 0)),
        "precision": float(result.get("precision", 0)),
        "recall": float(result.get("recall", 0)),
        "f1": float(result.get("f1", 0)),
        "confusion_img": result.get("confusion_img"),
        "roc_img": result.get("roc_img"),
        "report": slim_report,
        "label_counts": label_counts,
        "model_id": model_id,
        "confusion_matrix": result.get("confusion_matrix"),
        "train_count": result.get("train_count"),
        "test_count": result.get("test_count"),
        "n_train": result.get("n_train"),
        "n_test": result.get("n_test"),
    }

    return redirect(url_for("evaluasi"))


@app.route("/reset-klasifikasi", methods=["GET", "POST"])
def reset_klasifikasi():
    if not require_login():
        return redirect(url_for("login"))

    # 1. Hapus hasil dari session
    session.pop("result", None)

    # 2. Hapus dari database
    upload_id = session.get("upload_id")
    if upload_id:
        try:
            delete_model_results(upload_id)
        except Exception as e:
            print(f"[RESET] Error deleting model results: {e}")
    else:
        try:
            delete_model_results()
        except Exception as e:
            print(f"[RESET] Error deleting all model results: {e}")

    # 3. Hapus saved_model files di disk
    try:
        model_save_dir = os.path.join(PROCESSED_DIR, "saved_model")
        if os.path.exists(model_save_dir):
            for fname in os.listdir(model_save_dir):
                fpath = os.path.join(model_save_dir, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
    except Exception as e:
        print(f"[RESET] Error removing model files: {e}")

    log_activity("reset_model", upload_id, "Reset model SVM klasifikasi")
    return redirect(url_for("klasifikasi"))


@app.route("/reset-preprocessing", methods=["GET", "POST"])
@app.route("/reset-all", methods=["GET", "POST"])
def reset_preprocessing():
    if not require_login():
        return redirect(url_for("login"))
    if not require_admin():
        return redirect(url_for("dashboard"))

    perform_full_reset()
    log_activity("reset_preprocessing", None, "Reset seluruh data preprocessing dan upload")
    return redirect(url_for("upload"))


@app.route("/evaluasi")
def evaluasi():
    if not require_login():
        return redirect(url_for("login"))

    result = session.get("result")
    if not result:
        return redirect(url_for("klasifikasi"))

    return render_template("evaluasi.html", result=result)


@app.route("/hasil")
def hasil():
    if not require_login():
        return redirect(url_for("login"))

    result = session.get("result")
    if not result:
        return redirect(url_for("klasifikasi"))

    return render_template("hasil.html", result=result)


@app.route("/download-pdf")
def download_pdf():
    """Download hasil analisis sebagai PDF dengan 4 pilihan jenis laporan"""
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401
    
    result = session.get("result")
    upload_id = session.get("upload_id")
    
    if not result or not upload_id:
        return jsonify({"error": "No result data available"}), 400
    
    report_type = request.args.get("type", "all")
    
    # Mapping old types to new types to avoid caching issues
    if report_type == "preprocessing": report_type = "laporan_1"
    elif report_type == "classification": report_type = "laporan_2"
    elif report_type == "tfidf": report_type = "laporan_3"
    elif report_type == "executive": report_type = "all"
    elif report_type == "prediction": report_type = "laporan_4"
    try:
        # Ambil top TF-IDF features jika dibutuhkan
        top_features = get_tfidf_features(upload_id, top_n=50) if report_type in ["laporan_3", "all", "executive", "preprocessing"] else None
        
        # Ambil label counts dari result
        label_counts = result.get("label_counts")
        
        # Ambil sampel prediksi jika jenis laporan 'laporan_4' atau 'all'
        sample_preds = get_prediksi(upload_id=upload_id)[:50] if report_type in ["laporan_4", "all"] else None
        
        # Generate PDF
        pdf_content = generate_pdf_report(
            upload_id,
            {
                "accuracy": result.get("accuracy", 0),
                "precision": result.get("precision", 0),
                "recall": result.get("recall", 0),
                "f1": result.get("f1", 0),
                "confusion_matrix": result.get("confusion_matrix"),
                "report": result.get("report"),
                "n_train": result.get("n_train") or result.get("train_count"),
                "n_test": result.get("n_test") or result.get("test_count"),
                "test_size": result.get("test_size"),
            },
            STATIC_DIR,
            top_features=top_features,
            label_counts=label_counts,
            report_type=report_type,
            sample_preds=sample_preds
        )
        
        # Return PDF as download
        from io import BytesIO
        pdf_buffer = BytesIO(pdf_content)
        pdf_buffer.seek(0)  # Fix: ensure buffer is at position 0
        
        # Nama file yang deskriptif
        file_names = {
            "laporan_1": "Laporan_Distribusi_Pembagian_Data",
            "laporan_2": "Laporan_Evaluasi_Model_SVM",
            "laporan_3": "Laporan_TF-IDF",
            "laporan_4": "Laporan_50_Sampel_Preprocessing",
            "all": "Laporan_Lengkap_Sentimen",
        }
        fname = file_names.get(report_type, "Laporan_Sentimen")
        
        response = send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{fname}_{upload_id[:8]}.pdf'
        )
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Content-Type'] = 'application/pdf'
        return response
    
    except Exception as e:
        print(f"[ERROR] Download PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/riwayat")
def riwayat():
    if not require_login():
        return redirect(url_for("login"))

    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM hasil_model ORDER BY created_at DESC")
            rows = cur.fetchall()
        conn.close()
        
        # Debug: Log jumlah rows
        print(f"[DEBUG] Riwayat: Found {len(rows) if rows else 0} models")
        
        return render_template("riwayat.html", rows=rows or [])
    except Exception as e:
        print(f"[ERROR] Riwayat: {e}")
        import traceback
        traceback.print_exc()
        return render_template("riwayat.html", rows=[], error=str(e))


# ============ NEW ROUTES ============
@app.route("/perbandingan")
def perbandingan():
    """Halaman perbandingan data raw vs preprocessing (keduanya paginated + search)"""
    if not require_login():
        return redirect(url_for("login"))

    upload_id = session.get("upload_id")
    if not upload_id:
        return redirect(url_for("upload"))

    # === Tab Data Raw: pagination + search ===
    page = request.args.get("page", 1, type=int)
    per_page = 100
    q_raw = request.args.get("q_raw", "", type=str)

    data_raw, total_raw = get_data_raw_paged(upload_id, page=page, per_page=per_page, q=q_raw)
    total_pages = max(1, ceil(total_raw / per_page))

    # === Tab Perbandingan Detail: pagination + search ===
    comp_page = request.args.get("comp_page", 1, type=int)
    comp_per_page = 50
    q_comp = request.args.get("q_comp", "", type=str)

    from db_service import get_data_preprocessing_paged
    comp_data, total_processed = get_data_preprocessing_paged(
        upload_id, page=comp_page, per_page=comp_per_page, q=q_comp
    )
    comp_total_pages = max(1, ceil(total_processed / comp_per_page))

    # Rapihin key
    data_preprocessing = []
    for r in comp_data:
        data_preprocessing.append({
            "preprocessing_id": r.get("preprocessing_id"),
            "content_raw": r.get("content_raw") or "",
            "case_folding": r.get("case_folding") or "",
            "cleaning": r.get("cleaning") or "",
            "stemming": r.get("stemming") or "",
            "label_asli": r.get("label_asli") or "",
            "prediksi_svm": r.get("prediksi_svm") or "",
        })

    return render_template(
        "perbandingan.html",
        data_preprocessing=data_preprocessing,
        data_raw=data_raw,
        total_raw=total_raw,
        total_processed=total_processed,
        # Raw tab pagination
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        q_raw=q_raw,
        # Comp tab pagination
        comp_page=comp_page,
        comp_total_pages=comp_total_pages,
        comp_per_page=comp_per_page,
        q_comp=q_comp
    )

@app.route("/api/comparison")
def api_comparison():
    """API untuk menampilkan perbandingan data"""
    upload_id = session.get("upload_id")
    if not upload_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Ambil data raw
    raw_data = get_data_raw(upload_id)[:5]  # Limit 5 untuk preview
    
    # Ambil data preprocessing
    prep_data = get_data_preprocessing(upload_id, comparison=True)[:5]

    comparison = []
    for raw, prep in zip(raw_data, prep_data):
        comparison.append({
            "id": raw.get("id"),
            "content_raw": raw.get("content"),
            "case_folding": prep.get("case_folding") if prep else "",
            "cleaning": prep.get("cleaning") if prep else "",
            "stemming": prep.get("stemming") if prep else "",
            "label": raw.get("label")
        })

    return jsonify(comparison)


@app.route("/prediksi-detail")
def prediksi_detail():
    """Halaman detail prediksi manual vs SVM"""
    if not require_login():
        return redirect(url_for("login"))

    model_id = request.args.get("model_id")
    if not model_id:
        return redirect(url_for("riwayat"))

    # Ambil data prediksi
    prediksi_list = get_prediksi(model_id=int(model_id))
    
    # Ambil statistik
    stats = get_prediksi_stats(int(model_id))

    return render_template(
        "prediksi_detail.html",
        prediksi_list=prediksi_list,
        stats=stats,
        model_id=model_id
    )


@app.route("/api/prediksi")
def api_prediksi():
    """API untuk mendapatkan prediksi data"""
    upload_id = session.get("upload_id")
    if not upload_id:
        return jsonify({"error": "Unauthorized"}), 401

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    offset = (page - 1) * limit

    prediksi_list = get_prediksi(upload_id=upload_id)
    
    # Paginate
    paginated = prediksi_list[offset:offset + limit]
    
    return jsonify({
        "total": len(prediksi_list),
        "page": page,
        "limit": limit,
        "data": paginated
    })


@app.route("/api/tfidf-detail/<int:preprocessing_id>")
def api_tfidf_detail(preprocessing_id):
    """API untuk mendapatkan detail perhitungan TF-IDF per kata dalam satu dokumen"""
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    upload_id = session.get("upload_id")
    if not upload_id:
        return jsonify({"error": "No upload session"}), 400

    conn = get_db()
    try:
        # 1. Ambil semua dokumen untuk menghitung N dan DF
        with conn.cursor() as cur:
            cur.execute("SELECT id, stemming FROM data_preprocessing WHERE upload_id = %s AND stemming IS NOT NULL AND stemming != ''", (upload_id,))
            all_docs = cur.fetchall()
            
            if not all_docs:
                return jsonify({"error": "Tidak ada data dokumen"}), 404
                
            N = len(all_docs)
            
            # Cari dokumen target
            target_doc = None
            for doc in all_docs:
                if doc["id"] == preprocessing_id:
                    target_doc = doc
                    break
                    
            if not target_doc:
                return jsonify({"error": "Dokumen tidak ditemukan"}), 404

        # 2. Hitung DF untuk setiap kata di korpus
        import math
        from collections import Counter
        
        # DF dictionary: term -> document count
        df_counts = {}
        for doc in all_docs:
            # Gunakan set agar kata yang muncul lebih dari sekali di satu dokumen hanya dihitung 1 untuk DF
            terms = set(doc["stemming"].split())
            for term in terms:
                df_counts[term] = df_counts.get(term, 0) + 1

        # 3. Hitung TF untuk dokumen target
        target_terms = target_doc["stemming"].split()
        tf_counts = Counter(target_terms)
        
        # 4. Susun hasil detail TF-IDF sesuai rumus: TF, DF, N/DF, log10(N/DF), TF*IDF
        detail_results = []
        for i, (term, tf) in enumerate(tf_counts.items(), 1):
            df = df_counts.get(term, 1)
            n_div_df = N / df
            idf = math.log10(n_div_df)
            tf_idf = tf * idf
            
            detail_results.append({
                "no": i,
                "term": term,
                "tf": tf,
                "df": df,
                "n_div_df": round(n_div_df, 4),
                "idf": round(idf, 4),
                "tf_idf": round(tf_idf, 4)
            })
            
        # Urutkan berdasarkan bobot TF-IDF tertinggi
        detail_results.sort(key=lambda x: x["tf_idf"], reverse=True)
        
        # Re-assign nomor urut setelah sorting
        for i, item in enumerate(detail_results, 1):
            item["no"] = i

        return jsonify({
            "success": True,
            "preprocessing_id": preprocessing_id,
            "total_documents": N,
            "details": detail_results
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/prediksi-manual", methods=["POST"])
def prediksi_manual():
    """Endpoint untuk menerima prediksi manual dan menyimpan ke database"""
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401
    if not require_admin():
        return jsonify({"error": "Forbidden: Admin only"}), 403

    data = request.get_json()
    upload_id = session.get("upload_id")
    model_id = data.get("model_id")
    
    if not upload_id or not model_id:
        return jsonify({"error": "Missing data"}), 400

    manual_predictions = data.get("manual_predictions", [])
    
    # Update prediksi manual ke database
    try:
        conn = get_db()
        with conn.cursor() as cur:
            for pred in manual_predictions:
                cur.execute(
                    """UPDATE data_prediksi 
                       SET prediksi_manual = %s 
                       WHERE id = %s AND upload_id = %s""",
                    (pred.get("prediksi"), pred.get("prediksi_id"), upload_id)
                )
        
        log_activity("manual_prediction", upload_id, f"Manual predictions submitted for model {model_id}")
        
        return jsonify({"success": True, "message": "Prediksi manual berhasil disimpan"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/uji-sentimen")
def uji_sentimen():
    """Halaman Uji Sentimen: user bisa ketik komentar dan dapatkan prediksi label"""
    if not require_login():
        return redirect(url_for("login"))

    # Cek apakah model sudah tersedia
    model_path = os.path.join(PROCESSED_DIR, "saved_model", "svm_model.joblib")
    has_model = os.path.exists(model_path)

    # Jika belum ada file model tapi ada data preprocessed, auto-train & save
    if not has_model:
        dfp = load_processed_df()
        if dfp is not None and "stemming" in dfp.columns and "label" in dfp.columns and len(dfp) > 0:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.svm import SVC

                vectorizer = TfidfVectorizer()
                X = vectorizer.fit_transform(dfp["stemming"])
                model = SVC(kernel='linear', random_state=42)
                model.fit(X, dfp["label"])

                model_save_dir = os.path.join(PROCESSED_DIR, "saved_model")
                os.makedirs(model_save_dir, exist_ok=True)
                joblib.dump(model, os.path.join(model_save_dir, "svm_model.joblib"))
                joblib.dump(vectorizer, os.path.join(model_save_dir, "tfidf_vectorizer.joblib"))
                has_model = True
                print("[DEBUG] Auto-trained & saved model for Uji Sentimen")
            except Exception as e:
                print(f"[ERROR] Auto-train failed: {e}")

    return render_template("uji_sentimen.html", has_model=has_model)


@app.route("/api/uji-sentimen", methods=["POST"])
def api_uji_sentimen():
    """API endpoint untuk prediksi sentimen komentar yang diketik user"""
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    komentar = (data.get("komentar") or "").strip()

    if not komentar:
        return jsonify({"error": "Komentar tidak boleh kosong"}), 400

    # Load model + vectorizer dari disk
    model_path = os.path.join(PROCESSED_DIR, "saved_model", "svm_model.joblib")
    vec_path = os.path.join(PROCESSED_DIR, "saved_model", "tfidf_vectorizer.joblib")

    if not os.path.exists(model_path) or not os.path.exists(vec_path):
        return jsonify({"error": "Model belum dilatih. Silakan jalankan Klasifikasi SVM terlebih dahulu."}), 400

    try:
        model = joblib.load(model_path)
        vectorizer = joblib.load(vec_path)
    except Exception as e:
        return jsonify({"error": f"Gagal memuat model: {str(e)}"}), 500

    # Preprocessing komentar (sama seperti pipeline)
    import re, string
    from ml_pipeline import stemmer, stop_id

    text = komentar
    original = text

    # 1. Case folding
    case_folding = text.lower()

    # 2. Cleaning
    cleaned = re.sub(r"http\S+|www\S+", " ", case_folding)
    cleaned = re.sub(r"@\w+", " ", cleaned)
    cleaned = re.sub(r"#\w+", " ", cleaned)
    cleaned = re.sub(r"\b[a-zA-Z]\b", " ", cleaned)
    cleaned = re.sub(r"\d+", " ", cleaned)
    cleaned = cleaned.translate(str.maketrans("", "", string.punctuation))
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", cleaned)
    cleaned = re.sub(r'(.)\1{2,}', r'\1', cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # 3. Normalisasi slang (Dihapus karena tidak ada di ml_pipeline.py)

    # 4. Tokenizing
    tokens = cleaned.split()

    # 5. Stopword removal
    filtered = [t for t in tokens if t not in stop_id and len(t) > 2]

    # 6. Stemming
    stemmed = stemmer.stem(" ".join(filtered))

    if not stemmed.strip():
        return jsonify({"error": "Teks terlalu pendek atau tidak mengandung kata bermakna setelah preprocessing."}), 400

    # Prediksi
    X_input = vectorizer.transform([stemmed])
    prediction = model.predict(X_input)[0]

    # Confidence score
    decision_scores = model.decision_function(X_input)
    if len(decision_scores.shape) == 2:
        confidence = float(max(abs(x) for x in decision_scores[0]))
    else:
        confidence = float(abs(decision_scores[0]))

    # Normalisasi confidence ke 0-100%
    import math
    confidence_pct = round(min(100, (1 / (1 + math.exp(-confidence))) * 100), 1)

    return jsonify({
        "success": True,
        "komentar_asli": original,
        "preprocessing": {
            "case_folding": case_folding,
            "cleaning": cleaned,
            "tokenizing": tokens,
            "stopword_removed": filtered,
            "stemming": stemmed
        },
        "prediksi": prediction,
        "confidence": confidence_pct
    })


if __name__ == "__main__":
    app.run(debug=True)
 