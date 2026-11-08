# 🛠️ Software Pendukung & Persyaratan Sistem

Dokumen ini berisi daftar perangkat lunak (software) pendukung yang dibutuhkan untuk menjalankan **Aplikasi Analisis Sentimen (SVM & Naive Bayes)** berbasis Web Flask & MySQL.

---

## 📋 Ringkasan Software Required

| Software | Kategori | Fungsi Utama | Link Download |
| :--- | :--- | :--- | :--- |
| **Python** (3.8 - 3.11) | Programming Language | Running backend server Flask & Model ML | [Download Python](https://www.python.org/downloads/) |
| **XAMPP** (v7.4+) | Database Server | Menjalankan Database MySQL & phpMyAdmin | [Download XAMPP](https://www.apachefriends.org/) |
| **Google Chrome / Edge** | Web Browser | Mengakses antarmuka UI web aplikasi | [Download Chrome](https://www.google.com/chrome/) |
| **VS Code** *(Opsional)* | Code Editor | Membuka & mengedit source code / konfigurasi | [Download VS Code](https://code.visualstudio.com/) |

---

## 💻 Rincian Spesifikasi & Panduan Instalasi

### 1. 🐍 Python (Versi 3.8 - 3.11 direkomendasikan)
* **Fungsi**: Diperlukan untuk mengeksekusi backend Flask, script preprocessing teks, algoritma SVM & Naive Bayes, serta pembuatan laporan PDF.
* **Petunjuk Instalasi**:
  > [!IMPORTANT]
  > Saat menginstall Python, **WAJIB mencentang opsi `"Add Python to PATH"`** di halaman awal installer agar perintah `python` dan `pip` dapat dipanggil oleh script `.bat`.

### 2. 🐬 XAMPP (Control Panel)
* **Fungsi**: Menyediakan server database **MySQL** pada port default `3306` untuk menyimpan data ulasan, hasil preprocessing, pembobotan TF-IDF, serta riwayat evaluasi model.
* **Komponen yang Digunakan**:
  - **MySQL / MariaDB**: Server database utama.
  - **Apache / phpMyAdmin** *(Opsional)*: Untuk melihat database secara visual melalui browser (`http://localhost/phpmyadmin`).
* **Catatan Konfigurasi**:
  - Default user: `root`
  - Default password: `(kosong)`
  - Default port: `3306`

### 3. 🌐 Web Browser (Google Chrome / Microsoft Edge / Firefox)
* **Fungsi**: Untuk mengakses antarmuka Web GUI aplikasi yang berjalan di local address `http://127.0.0.1:5000`.
* **Rekomendasi**: Google Chrome versi terbaru untuk tampilan UI terbaik dan kompatibilitas CSS/JavaScript yang optimal.

### 4. 📝 Visual Studio Code (Opsional)
* **Fungsi**: Diperlukan jika Anda ingin melakukan penyesuaian kode, mengubah file konfigurasi `.env`, atau melihat struktur database.

---

## 📦 Python Libraries (Otomatis Diinstall via `install.bat`)

Semua library Python di bawah ini akan otomatis diinstall ke dalam Virtual Environment (`venv`) saat Anda menjalankan `install.bat`:

- **Flask**: Web framework untuk routing dan backend controller.
- **PyMySQL**: Connector Python ke database MySQL.
- **scikit-learn**: Implementasi algoritma ML (SVM & Naive Bayes) serta TF-IDF Vectorizer.
- **pandas & numpy**: Manipulasi data tabular dan komputasi array.
- **NLTK & Sastrawi**: Preprocessing teks bahasa Indonesia (Stopword, Stemming, Tokenizing).
- **ReportLab**: Generator laporan statistik & perbandingan dalam format dokumen PDF.
- **WordCloud, Matplotlib, Seaborn**: Visualisasi kata dan grafik performa model.

---

## 🚀 Langkah Cepat Memulai (Quick Start)

Setelah semua software pendukung terinstall:

1. Buka **XAMPP Control Panel** → Klik **Start** pada **MySQL**.
2. Double-click file [`install.bat`](file:///d:/Aplikasi%20Sentimen/install.bat) (cukup dijalankan 1x untuk setup awal).
3. Double-click file [`start.bat`](file:///d:/Aplikasi%20Sentimen/start.bat) untuk menjalankan aplikasi. Browser akan otomatis terbuka di `http://127.0.0.1:5000`.
