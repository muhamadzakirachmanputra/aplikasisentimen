# Manual Book - Script Batch (.bat) Aplikasi Sentimen Analysis

Dokumen ini berisi panduan lengkap cara menjalankan semua file `.bat` yang tersedia pada Aplikasi Analisis Sentimen.

---

## Daftar File Script

| No | File | Fungsi | Kapan Dijalankan |
|:--:|:-----|:-------|:-----------------|
| 1 | `install.bat` | Instalasi awal (setup environment & dependencies) | **Sekali saja** saat pertama kali setup |
| 2 | `start.bat` | Menjalankan aplikasi (server Flask + buka browser) | **Setiap kali** ingin membuka aplikasi |
| 3 | `start_database.bat` | Setup / import ulang database MySQL | Jika database perlu dibuat ulang atau diimport ulang |
| 4 | `stop.bat` | Menghentikan server aplikasi | Jika ingin mematikan server Flask & MySQL |

---

## Prasyarat Sebelum Menjalankan Script

Pastikan software berikut sudah terinstall di komputer Anda:

1. **Python 3.8 - 3.11** — [Download Python](https://www.python.org/downloads/)
   > **PENTING:** Saat install Python, **wajib centang** opsi `"Add Python to PATH"` di halaman awal installer.

2. **XAMPP** — [Download XAMPP](https://www.apachefriends.org/)
   > Digunakan untuk menjalankan server database MySQL.

3. **Web Browser** (Google Chrome / Microsoft Edge)
   > Untuk mengakses tampilan web aplikasi di `http://127.0.0.1:5000`.

---

## 1. install.bat — Instalasi Awal

### Kapan Dijalankan
- **Hanya sekali**, saat pertama kali menyiapkan aplikasi di komputer baru.
- Jalankan lagi jika ada masalah pada environment atau dependencies.

### Cara Menjalankan
1. Buka folder `Aplikasi Sentimen`.
2. **Klik 2x (double-click)** file `install.bat`.
3. Tekan **Enter** atau tombol apapun saat muncul `Press any key to continue...`.
4. Tunggu proses instalasi selesai.

### Urutan Proses yang Dijalankan

| Step | Proses | Keterangan |
|:----:|:-------|:-----------|
| 1/6 | **Cek Python** | Memastikan Python sudah terinstall dan ada di PATH |
| 2/6 | **Buat Virtual Environment** | Membuat folder `venv` untuk isolasi library Python |
| 3/6 | **Install Python Dependencies** | Menginstall Flask, scikit-learn, NLTK, pandas, dll. dari `requirements.txt` |
| 4/6 | **Download NLTK Data** | Mendownload data tokenizer, stopwords, dan wordnet untuk preprocessing teks |
| 5/6 | **Setup File .env** | Membuat file konfigurasi `.env` dari template `.env.example` |
| 6/6 | **Setup Database MySQL** | Mendeteksi MySQL via XAMPP, menawarkan import database `sentiment_db.sql` |

### Contoh Output yang Diharapkan

```
[STEP 1/6] Mengecek instalasi Python...
[OK] Python 3.11.9 ditemukan!

[STEP 2/6] Membuat Virtual Environment...
[OK] Virtual environment berhasil dibuat!

[STEP 3/6] Menginstall Python Dependencies...
[OK] Semua Python dependencies berhasil diinstall!

[STEP 4/6] Mendownload NLTK Data...
[OK] NLTK data berhasil didownload!

[STEP 5/6] Setup file konfigurasi .env...
[OK] File .env berhasil dibuat dari .env.example

[STEP 6/6] Setup Database MySQL...
[OK] MySQL ditemukan: C:\xampp\mysql\bin\mysql.exe
[OK] MySQL service sedang berjalan!
Ingin setup database sekarang? [Y/N]
```

### Troubleshooting

| Masalah | Solusi |
|:--------|:-------|
| `[X] Python TIDAK ditemukan!` | Install Python dan pastikan centang "Add Python to PATH" |
| `[X] Gagal menginstall beberapa package!` | Pastikan koneksi internet stabil, jalankan ulang `install.bat` |
| `[!] MySQL tidak ditemukan!` | Install XAMPP terlebih dahulu |
| `[!] MySQL service belum berjalan!` | Buka XAMPP Control Panel, klik **Start** pada **MySQL** |

---

## 2. start.bat — Menjalankan Aplikasi

### Kapan Dijalankan
- **Setiap kali** ingin membuka dan menggunakan aplikasi.

### Cara Menjalankan
1. Pastikan **XAMPP MySQL** sudah berjalan (buka XAMPP Control Panel → Start MySQL).
2. **Klik 2x (double-click)** file `start.bat`.
3. Tunggu sampai browser terbuka otomatis.
4. Aplikasi siap digunakan di `http://127.0.0.1:5000`.

### Urutan Proses yang Dijalankan

| Step | Proses | Keterangan |
|:----:|:-------|:-----------|
| 1/4 | **Cek file .env** | Memastikan file konfigurasi `.env` ada |
| 2/4 | **Aktifkan Virtual Environment** | Mengaktifkan `venv` agar library Python tersedia |
| 3/4 | **Cek MySQL dan Database** | Memastikan MySQL berjalan dan database `sentiment_db` ada |
| 4/4 | **Jalankan Flask Server** | Menjalankan `python app.py`, menunggu server siap, lalu buka browser |

> **Catatan:** Browser **baru akan terbuka setelah** server Flask benar-benar siap menerima koneksi (port 5000 aktif). Tidak akan ada halaman kosong/error karena server belum siap.

### Contoh Output yang Diharapkan

```
[1/4] Mengecek file .env...
[OK] File .env ditemukan!

[2/4] Mengaktifkan Virtual Environment...
[OK] Virtual Environment aktif!

[3/4] Mengecek MySQL dan Database...
[OK] MySQL berjalan!
[OK] Database sentiment_db ditemukan!

[4/4] Menjalankan Flask Server...
[*] Menunggu server siap...
[OK] Server Flask sudah berjalan!

======================================================
|                                                    |
|  Aplikasi berjalan di: http://127.0.0.1:5000       |
|  Tekan CTRL+C untuk menghentikan server            |
|                                                    |
======================================================
```

### Cara Menghentikan
- Tekan **tombol apapun** di jendela Command Prompt, atau
- Tutup jendela Command Prompt secara langsung, atau
- Jalankan `stop.bat`.

### Troubleshooting

| Masalah | Solusi |
|:--------|:-------|
| `[X] Virtual environment tidak ditemukan!` | Jalankan `install.bat` terlebih dahulu |
| `[!] File .env tidak ditemukan!` | Jalankan `install.bat` atau copy `.env.example` ke `.env` manual |
| `[X] MySQL masih belum bisa diakses` | Buka XAMPP Control Panel → Start MySQL |
| `[X] Server gagal start dalam 30 detik!` | Cek apakah port 5000 sudah dipakai aplikasi lain |
| Browser terbuka tapi halaman kosong | Tunggu beberapa detik lalu refresh (F5) |

---

## 3. start_database.bat — Setup / Import Database

### Kapan Dijalankan
- Jika database `sentiment_db` belum dibuat.
- Jika ingin **import ulang** data dari file `sentiment_db.sql`.
- Jika database rusak dan perlu di-reset.

### Cara Menjalankan
1. Pastikan **XAMPP MySQL** sudah berjalan.
2. **Klik 2x (double-click)** file `start_database.bat`.
3. Ikuti instruksi di layar.

### Urutan Proses yang Dijalankan

| Step | Proses | Keterangan |
|:----:|:-------|:-----------|
| 1/3 | **Mencari MySQL** | Mendeteksi lokasi MySQL di XAMPP (drive C: atau D:) |
| 2/3 | **Cek MySQL Service** | Memastikan MySQL berjalan, otomatis start jika belum |
| 3/3 | **Cek & Import Database** | Mengecek apakah database sudah ada, lalu import jika perlu |

### Skenario yang Ditangani

| Kondisi Database | Aksi Script |
|:-----------------|:------------|
| Database **belum ada** | Otomatis membuat database baru dan import dari `sentiment_db.sql` |
| Database **ada tapi kosong** (0 tabel) | Otomatis hapus, buat ulang, dan import dari `sentiment_db.sql` |
| Database **sudah ada dan terisi** | Menampilkan jumlah tabel, lalu bertanya: *"Ingin import ulang? [Y/N]"* |

> **Peringatan:** Jika Anda memilih **Y** (import ulang), semua data yang ada di database akan **ditimpa** dengan data dari `sentiment_db.sql`.

### Contoh Output yang Diharapkan

```
[1/3] Mencari MySQL...
[OK] MySQL ditemukan: C:\xampp\mysql\bin\mysql.exe

[2/3] Mengecek MySQL service...
[OK] MySQL sudah berjalan!

[3/3] Mengecek database sentiment_db...
[OK] Database sentiment_db sudah ada dengan 8 tabel.

Database sudah terisi. Ingin import ulang? [Y/N]
[!] PERINGATAN: Ini akan menimpa data yang sudah ada!
Pilihan Anda: N
[-] Import dibatalkan. Database tidak diubah.

[OK] DATABASE SETUP SELESAI!
```

### Troubleshooting

| Masalah | Solusi |
|:--------|:-------|
| `[X] MySQL tidak ditemukan!` | Install XAMPP terlebih dahulu |
| `[X] MySQL gagal start!` | Buka XAMPP Control Panel dan start MySQL manual |
| `[X] Gagal mengimport SQL file!` | Pastikan file `sentiment_db.sql` ada di folder utama aplikasi |
| Import memakan waktu lama | File `sentiment_db.sql` berukuran ~5MB, tunggu hingga selesai |

---

## 4. stop.bat — Menghentikan Aplikasi

### Kapan Dijalankan
- Jika ingin menghentikan server Flask yang sedang berjalan.
- Jika ingin mematikan MySQL juga (opsional).

### Cara Menjalankan
1. **Klik 2x (double-click)** file `stop.bat`.
2. Script akan otomatis menghentikan Flask server.
3. Jawab **Y** atau **N** saat ditanya apakah ingin menghentikan MySQL juga.

### Urutan Proses yang Dijalankan

| Step | Proses | Keterangan |
|:----:|:-------|:-----------|
| 1/2 | **Menghentikan Flask Server** | Mencari dan mematikan proses Python yang berjalan di port 5000 |
| 2/2 | **MySQL Service (opsional)** | Menawarkan pilihan untuk ikut mematikan MySQL atau biarkan tetap jalan |

### Contoh Output yang Diharapkan

```
[1/2] Menghentikan Flask Server...
[*] Menghentikan proses PID: 12345
[OK] Flask server dihentikan!

[2/2] MySQL Service...
Apakah ingin menghentikan MySQL juga? (Y/N)
Pilihan Anda: N
[-] MySQL tetap berjalan.

[OK] APLIKASI BERHASIL DIHENTIKAN
```

---

## Urutan Penggunaan (Quick Start)

Untuk pengguna pertama kali, ikuti langkah berikut secara berurutan:

```
┌─────────────────────────────────────────────────┐
│  LANGKAH 1: Install Software Pendukung          │
│  → Install Python 3.8-3.11 (centang Add to PATH)│
│  → Install XAMPP                                 │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  LANGKAH 2: Buka XAMPP Control Panel            │
│  → Klik Start pada MySQL                        │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  LANGKAH 3: Jalankan install.bat                │
│  → Double-click install.bat                     │
│  → Tunggu sampai semua step selesai             │
│  → Jawab Y saat ditanya setup database          │
│  (CUKUP SEKALI SAJA)                            │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  LANGKAH 4: Jalankan start.bat                  │
│  → Double-click start.bat                       │
│  → Tunggu browser terbuka otomatis              │
│  → Aplikasi siap digunakan!                     │
│  (SETIAP KALI INGIN BUKA APLIKASI)              │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│  LANGKAH 5: Selesai menggunakan?                │
│  → Tekan tombol apapun di Command Prompt, atau  │
│  → Double-click stop.bat                        │
└─────────────────────────────────────────────────┘
```

---

## FAQ (Pertanyaan Umum)

**Q: Apakah harus menjalankan `install.bat` setiap kali?**
> Tidak. `install.bat` cukup dijalankan **sekali saja** saat pertama kali setup. Untuk penggunaan sehari-hari, cukup jalankan `start.bat`.

**Q: Apakah harus menjalankan `start_database.bat` sebelum `start.bat`?**
> Tidak. `start.bat` sudah **otomatis mengecek** dan membuat database jika belum ada. `start_database.bat` hanya perlu dijalankan jika ingin **import ulang** data database.

**Q: Port 5000 sudah dipakai aplikasi lain, bagaimana?**
> Hentikan aplikasi lain yang menggunakan port 5000, atau jalankan `stop.bat` untuk mematikan proses yang menempati port tersebut.

**Q: Browser terbuka tapi halaman error/kosong?**
> Tunggu beberapa detik lalu tekan **F5** (refresh). Jika masih error, cek jendela Command Prompt untuk melihat pesan error dari Flask.

**Q: XAMPP MySQL tidak mau start?**
> Pastikan tidak ada MySQL lain yang berjalan. Buka Task Manager → cari proses `mysqld.exe` → End Task, lalu coba start lagi dari XAMPP.
