# Backend/db_service.py
"""
Service untuk operasi database terkait sentiment analysis
"""
import pymysql
from datetime import datetime
from config import DB_CONFIG
from typing import List, Dict, Optional, Tuple


def get_db():
    """Get database connection"""
    conn_params = {
        "host": DB_CONFIG["host"],
        "user": DB_CONFIG["user"],
        "password": DB_CONFIG["password"],
        "database": DB_CONFIG["database"],
        "port": DB_CONFIG.get("port", 3306),
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True
    }
    if DB_CONFIG.get("ssl"):
        conn_params["ssl"] = {'ssl': {}}
    return pymysql.connect(**conn_params)


# ============ DATA UPLOAD ============
def save_upload_record(upload_id: str, filename: str, total_records: int) -> bool:
    """Simpan record upload ke database"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO data_upload (upload_id, filename, total_records) 
                   VALUES (%s, %s, %s)""",
                (upload_id, filename, total_records)
            )
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving upload record: {e}")
        return False


def get_upload_record(upload_id: str) -> Optional[Dict]:
    """Ambil record upload"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM data_upload WHERE upload_id = %s", (upload_id,))
            result = cur.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting upload record: {e}")
        return None


def get_latest_upload() -> Optional[Dict]:
    """Ambil record upload terbaru (untuk restore session setelah login)"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM data_upload ORDER BY upload_date DESC LIMIT 1")
            result = cur.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting latest upload: {e}")
        return None


# ============ DATA RAW ============
def save_data_raw(upload_id: str, df) -> bool:
    """Simpan data raw (sebelum preprocessing) ke database"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(
                    """INSERT INTO data_raw 
                       (upload_id, userName, score, at, content, label) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        upload_id,
                        str(row.get("userName", ""))[:255] if pd.notna(row.get("userName")) else None,
                        int(row.get("score")) if pd.notna(row.get("score")) else None,
                        str(row.get("at", ""))[:255] if pd.notna(row.get("at")) else None,
                        str(row.get("content", "")),
                        str(row.get("label", ""))
                    )
                )
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving data raw: {e}")
        return False


def get_data_raw(upload_id: str, limit: int = None) -> List[Dict]:
    """Ambil data raw"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            if limit:
                cur.execute(
                    """SELECT * FROM data_raw 
                       WHERE upload_id = %s 
                       ORDER BY id DESC LIMIT %s""",
                    (upload_id, limit)
                )
            else:
                cur.execute(
                    """SELECT * FROM data_raw 
                       WHERE upload_id = %s 
                       ORDER BY id DESC""",
                    (upload_id,)
                )
            results = cur.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Error getting data raw: {e}")
        return []


# ============ DATA PREPROCESSING ============
def save_data_preprocessing(upload_id: str, df) -> bool:
    """Simpan data preprocessing (sesudah preprocessing)"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # Iterasi setiap baris
            for idx, row in df.iterrows():
                data_raw_id = None
                
                # Cari data_raw_id dari kolom yang sudah dipetakan
                if "data_raw_id" in df.columns:
                    data_raw_id = row.get("data_raw_id")
                    if pd.notna(data_raw_id):
                        data_raw_id = int(data_raw_id)
                    else:
                        data_raw_id = None
                
                cur.execute(
                    """INSERT INTO data_preprocessing 
                       (upload_id, data_raw_id, case_folding, cleaning, tokenizing, stopword_removed, stemming, label) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        upload_id,
                        data_raw_id,
                        str(row.get("case_folding", "")),
                        str(row.get("cleaning", "")),
                        str(row.get("tokenizing", "")),
                        str(row.get("stopword_removed", "")),
                        str(row.get("stemming", "")),
                        str(row.get("label", ""))
                    )
                )
        conn.commit()
        conn.close()
        print(f"[DB] v Saved {len(df)} preprocessing records")
        return True
    except Exception as e:
        print(f"[DB] X Error saving data preprocessing: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_data_preprocessing(upload_id: str, comparison: bool = False) -> List[Dict]:
    """
    Ambil data preprocessing.
    Jika comparison=True, gabung dengan data_raw & prediksi untuk perbandingan lengkap
    """
    try:
        conn = get_db()
        with conn.cursor() as cur:
            if comparison:
                # Query perbandingan lengkap: raw + preprocessing + prediksi (manual vs SVM)
                cur.execute(
                    """SELECT 
                        pr.id as preprocessing_id,
                        pr.upload_id,
                        dr.id as raw_id,
                        dr.content as content_raw,
                        dr.label as label_asli,
                        pr.case_folding,
                        pr.cleaning,
                        pr.tokenizing,
                        pr.stopword_removed,
                        pr.stemming,
                        pr.label,
                        pred.prediksi_svm,
                        pred.confidence_svm,
                        pred.prediksi_manual
                    FROM data_preprocessing pr
                    LEFT JOIN data_raw dr ON pr.data_raw_id = dr.id
                    LEFT JOIN data_prediksi pred ON pred.id = (
                        SELECT MAX(id) FROM data_prediksi WHERE data_preprocessing_id = pr.id
                    )
                    WHERE pr.upload_id = %s
                    ORDER BY pr.id ASC""",
                    (upload_id,)
                )
            else:
                cur.execute(
                    """SELECT * FROM data_preprocessing 
                       WHERE upload_id = %s 
                       ORDER BY id ASC""",
                    (upload_id,)
                )
            results = cur.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Error getting data preprocessing: {e}")
        return []


# ============ HASIL MODEL ============
def save_model_result(upload_id: str, accuracy: float, precision: float, 
                      recall: float, f1: float, feature_count: int, 
                      total_training_data: int, model_path: str = None) -> int:
    """Simpan hasil model training, return model_id"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # Debug
            print(f"[DB] Saving model: upload_id={upload_id}, accuracy={accuracy}, precision={precision}")
            
            cur.execute(
                """INSERT INTO hasil_model 
                   (upload_id, accuracy, precision_val, recall_val, f1_val, feature_count, total_training_data, model_path) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (upload_id, accuracy, precision, recall, f1, feature_count, total_training_data, model_path)
            )
            model_id = cur.lastrowid
            print(f"[DB] v Model saved successfully! model_id={model_id}")
        conn.close()
        return model_id
    except Exception as e:
        print(f"[DB] X Error saving model result: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_model_results(upload_id: str = None, limit: int = 10) -> List[Dict]:
    """Ambil hasil model training, opsional filter by upload_id"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            if upload_id:
                cur.execute(
                    """SELECT * FROM hasil_model 
                       WHERE upload_id = %s 
                       ORDER BY created_at DESC LIMIT %s""",
                    (upload_id, limit)
                )
            else:
                cur.execute(
                    """SELECT * FROM hasil_model 
                       ORDER BY created_at DESC LIMIT %s""",
                    (limit,)
                )
            results = cur.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Error getting model results: {e}")
        return []


def delete_model_results(upload_id: str = None) -> bool:
    """Hapus hasil model training dan data prediksi terkait dari database"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            if upload_id:
                cur.execute("DELETE FROM data_prediksi WHERE upload_id = %s", (upload_id,))
                cur.execute("DELETE FROM hasil_model WHERE upload_id = %s", (upload_id,))
            else:
                cur.execute("DELETE FROM data_prediksi")
                cur.execute("DELETE FROM hasil_model")
            conn.commit()
        conn.close()
        print(f"[DB] Model results reset successfully for upload_id={upload_id}")
        return True
    except Exception as e:
        print(f"[DB] Error resetting model results: {e}")
        return False



# ============ DATA PREDIKSI (Manual vs SVM) ============
def save_prediksi(upload_id: str, model_id: int, preprocessing_data: List[Dict], 
                  svm_predictions: List[str], svm_confidence: List[float],
                  manual_predictions: List[str] = None) -> bool:
    """
    Simpan prediksi manual vs SVM
    
    Args:
        upload_id: ID upload
        model_id: ID model hasil training
        preprocessing_data: List data preprocessing (dengan stemming)
        svm_predictions: Prediksi dari SVM
        svm_confidence: Confidence score dari SVM
        manual_predictions: Prediksi manual (opsional, default None)
    """
    try:
        conn = get_db()
        with conn.cursor() as cur:
            for idx, data in enumerate(preprocessing_data):
                pred_manual = manual_predictions[idx] if manual_predictions else None
                pred_svm = svm_predictions[idx] if idx < len(svm_predictions) else None
                conf_svm = svm_confidence[idx] if idx < len(svm_confidence) else 0.0
                label_asli = data.get("label")
                is_correct = pred_svm == label_asli if pred_svm and label_asli else None
                
                cur.execute(
                    """INSERT INTO data_prediksi 
                       (upload_id, model_id, data_preprocessing_id, content_original, 
                        content_stemmed, label_asli, prediksi_manual, prediksi_svm, 
                        confidence_svm, is_correct_svm) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        upload_id,
                        model_id,
                        data.get("id"),  # data_preprocessing_id
                        data.get("content_raw", "")[:500] if data.get("content_raw") else None,
                        data.get("stemming", ""),
                        label_asli,
                        pred_manual,
                        pred_svm,
                        float(conf_svm),
                        is_correct
                    )
                )
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving prediksi: {e}")
        return False


def get_prediksi(upload_id: str = None, model_id: int = None) -> List[Dict]:
    """Ambil data prediksi"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            if model_id:
                cur.execute(
                    """SELECT * FROM data_prediksi 
                       WHERE model_id = %s 
                       ORDER BY id DESC""",
                    (model_id,)
                )
            elif upload_id:
                cur.execute(
                    """SELECT * FROM data_prediksi 
                       WHERE upload_id = %s 
                       ORDER BY id DESC""",
                    (upload_id,)
                )
            else:
                cur.execute("SELECT * FROM data_prediksi ORDER BY id DESC LIMIT 100")
            
            results = cur.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Error getting prediksi: {e}")
        return []


def get_prediksi_stats(model_id: int) -> Dict:
    """Ambil statistik prediksi (accuracy SVM vs Manual)"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # Total records
            cur.execute("SELECT COUNT(*) as total FROM data_prediksi WHERE model_id = %s", (model_id,))
            total = cur.fetchone()["total"]
            
            # SVM correct
            cur.execute(
                "SELECT COUNT(*) as correct FROM data_prediksi WHERE model_id = %s AND is_correct_svm = 1",
                (model_id,)
            )
            svm_correct = cur.fetchone()["correct"]
            
            # Manual correct
            cur.execute(
                "SELECT COUNT(*) as correct FROM data_prediksi WHERE model_id = %s AND prediksi_manual = label_asli",
                (model_id,)
            )
            manual_correct = cur.fetchone()["correct"]
            
            # Avg confidence
            cur.execute(
                "SELECT AVG(confidence_svm) as avg_conf FROM data_prediksi WHERE model_id = %s AND confidence_svm IS NOT NULL",
                (model_id,)
            )
            avg_conf = cur.fetchone()["avg_conf"] or 0.0
        
        conn.close()
        
        return {
            "total": total,
            "svm_correct": svm_correct,
            "svm_accuracy": (svm_correct / total * 100) if total > 0 else 0,
            "manual_correct": manual_correct,
            "manual_accuracy": (manual_correct / total * 100) if total > 0 else 0,
            "avg_confidence": float(avg_conf)
        }
    except Exception as e:
        print(f"Error getting prediksi stats: {e}")
        return {}


# ============ USER ACTIVITY ============
def log_activity(action: str, upload_id: str = None, description: str = None) -> bool:
    """Log user activity"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO user_activity (action, upload_id, description) 
                   VALUES (%s, %s, %s)""",
                (action, upload_id, description)
            )
        conn.close()
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False


# ============ COMPARISON & REPORTS ============
def get_comparison_report(upload_id: str) -> Dict:
    """
    Buat laporan perbandingan:
    - Data raw vs preprocessing
    - Manual vs SVM prediction
    """
    try:
        data_raw = get_data_raw(upload_id)
        data_preprocessing = get_data_preprocessing(upload_id, comparison=True)
        
        return {
            "raw_count": len(data_raw),
            "preprocessing_count": len(data_preprocessing),
            "raw_data": data_raw,
            "preprocessing_data": data_preprocessing
        }
    except Exception as e:
        print(f"Error generating comparison report: {e}")
        return {}


import pandas as pd

# ============ DATA TFIDF FEATURES ============
def save_tfidf_features(upload_id: str, preprocessing_data: List[Dict], 
                        tfidf_matrix, feature_names: List[str]) -> bool:
    """
    Simpan hasil TF-IDF feature extraction
    
    Args:
        upload_id: ID upload
        preprocessing_data: List data preprocessing
        tfidf_matrix: Sparse matrix hasil TfidfVectorizer.fit_transform() (shape: n_samples x n_features)
        feature_names: Nama-nama feature dari vectorizer.get_feature_names_out()
    """
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # Konversi sparse matrix ke COO format untuk iterasi efisien
            tfidf_coo = tfidf_matrix.tocoo()
            
            for row_idx, col_idx, value in zip(tfidf_coo.row, tfidf_coo.col, tfidf_coo.data):
                if row_idx < len(preprocessing_data):
                    data = preprocessing_data[row_idx]
                    feature_name = feature_names[col_idx]
                    
                    cur.execute(
                        """INSERT INTO data_tfidf 
                           (upload_id, data_preprocessing_id, feature_name, tfidf_score) 
                           VALUES (%s, %s, %s, %s)""",
                        (
                            upload_id,
                            data.get("id"),  # data_preprocessing_id
                            feature_name,
                            float(value)
                        )
                    )
        conn.close()
        print(f"[DB] v TF-IDF features saved! Total entries: {len(tfidf_coo.data)}")
        return True
    except Exception as e:
        print(f"[DB] X Error saving TF-IDF features: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_tfidf_features(upload_id: str, top_n: int = 50) -> List[Dict]:
    """
    Ambil top N TF-IDF features berdasarkan rata-rata score
    
    Args:
        upload_id: ID upload
        top_n: Jumlah top features yang ingin diambil
    """
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """SELECT 
                    feature_name,
                    AVG(tfidf_score) as avg_score,
                    MAX(tfidf_score) as max_score,
                    COUNT(*) as frequency
                FROM data_tfidf
                WHERE upload_id = %s
                GROUP BY feature_name
                ORDER BY avg_score DESC
                LIMIT %s""",
                (upload_id, top_n)
            )
            results = cur.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Error getting TF-IDF features: {e}")
        return []


def get_tfidf_for_document(upload_id: str, preprocessing_id: int) -> List[Dict]:
    """Ambil TF-IDF features untuk satu dokumen tertentu"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """SELECT feature_name, tfidf_score
                FROM data_tfidf
                WHERE upload_id = %s AND data_preprocessing_id = %s
                ORDER BY tfidf_score DESC
                LIMIT 30""",
                (upload_id, preprocessing_id)
            )
            results = cur.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Error getting TF-IDF for document: {e}")
        return []

def get_data_raw_paged(upload_id, page=1, per_page=100, q=""):
    from db_service import get_db
    conn = get_db()
    data = []
    total = 0
    try:
        with conn.cursor() as cur:
            offset = (page - 1) * per_page
            query = "SELECT * FROM data_raw WHERE upload_id = %s"
            params = [upload_id]
            if q:
                query += " AND content LIKE %s"
                params.append("%" + q + "%")
            
            count_query = query.replace("SELECT *", "SELECT COUNT(*)")
            cur.execute(count_query, tuple(params))
            row = cur.fetchone()
            total = row['COUNT(*)'] if isinstance(row, dict) else row[0] if row else 0
            
            query += " ORDER BY id ASC LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            cur.execute(query, tuple(params))
            data = cur.fetchall()
    except Exception as e:
        print(f"Error get_data_raw_paged: {e}")
    finally:
        conn.close()
    return data, total

def get_data_preprocessing_paged(upload_id, page=1, per_page=50, q=""):
    from db_service import get_db
    conn = get_db()
    data = []
    total = 0
    try:
        with conn.cursor() as cur:
            offset = (page - 1) * per_page
            base_query = """
                FROM data_preprocessing pr
                LEFT JOIN data_raw dr ON pr.data_raw_id = dr.id
                LEFT JOIN data_prediksi pred ON pred.id = (
                    SELECT MAX(id) FROM data_prediksi WHERE data_preprocessing_id = pr.id
                )
                WHERE pr.upload_id = %s
            """
            params = [upload_id]
            if q:
                base_query += " AND (dr.content LIKE %s OR pr.stemming LIKE %s OR pr.label LIKE %s)"
                params.extend(["%" + q + "%", "%" + q + "%", "%" + q + "%"])
            
            count_query = "SELECT COUNT(DISTINCT pr.id) " + base_query
            cur.execute(count_query, tuple(params))
            row = cur.fetchone()
            total = row['COUNT(DISTINCT pr.id)'] if isinstance(row, dict) else row[0] if row else 0
            
            query = "SELECT pr.id as preprocessing_id, pr.upload_id, dr.id as raw_id, dr.content as content_raw, dr.label as label_asli, pr.case_folding, pr.cleaning, pr.tokenizing, pr.stopword_removed, pr.stemming, pr.label, pred.prediksi_svm, pred.confidence_svm, pred.prediksi_manual " + base_query + " ORDER BY pr.id ASC LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            cur.execute(query, tuple(params))
            data = cur.fetchall()
    except Exception as e:
        print(f"Error get_data_preprocessing_paged: {e}")
    finally:
        conn.close()
    return data, total
