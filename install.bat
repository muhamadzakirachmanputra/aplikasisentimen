@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Instalasi Aplikasi Sentimen Analysis
color 0B

echo.
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|     INSTALLER - APLIKASI SENTIMEN ANALYSIS         ^|
echo  ^|                                                    ^|
echo  ======================================================
echo.
echo  Script ini akan menginstall semua kebutuhan aplikasi:
echo    [1] Cek Python
echo    [2] Buat Virtual Environment
echo    [3] Install Python Dependencies
echo    [4] Download NLTK Data
echo    [5] Setup File .env
echo    [6] Setup Database MySQL (via XAMPP)
echo.
echo  ------------------------------------------------------
pause
echo.

REM ============================================
REM STEP 1: Cek Python
REM ============================================
echo.
echo  [STEP 1/6] Mengecek instalasi Python...
echo  ------------------------------------------------------

python --version >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo  [X] Python TIDAK ditemukan!
    echo.
    echo  Silakan install Python terlebih dahulu:
    echo  Download di: https://www.python.org/downloads/
    echo.
    echo  [!] PENTING: Centang "Add Python to PATH" saat install!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo  [OK] %PYTHON_VER% ditemukan!
echo.

REM ============================================
REM STEP 2: Buat Virtual Environment
REM ============================================
echo  [STEP 2/6] Membuat Virtual Environment...
echo  ------------------------------------------------------

if exist "%~dp0venv" (
    echo  [!] Virtual environment sudah ada. Skip pembuatan.
) else (
    echo  [*] Membuat virtual environment baru...
    python -m venv "%~dp0venv"
    if !ERRORLEVEL! NEQ 0 (
        echo  [X] Gagal membuat virtual environment!
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment berhasil dibuat!
)
echo.

REM ============================================
REM STEP 3: Activate venv & Install Dependencies
REM ============================================
echo  [STEP 3/6] Menginstall Python Dependencies...
echo  ------------------------------------------------------

call "%~dp0venv\Scripts\activate.bat"

echo  [*] Mengupdate pip...
python -m pip install --upgrade pip >nul 2>&1

echo  [*] Menginstall requirements dari Backend\requirements.txt...
echo.
pip install -r "%~dp0Backend\requirements.txt"

if !ERRORLEVEL! NEQ 0 (
    echo.
    echo  [X] Gagal menginstall beberapa package!
    echo  Coba jalankan ulang script ini.
    pause
    exit /b 1
)
echo.
echo  [OK] Semua Python dependencies berhasil diinstall!
echo.

REM ============================================
REM STEP 4: Download NLTK Data
REM ============================================
echo  [STEP 4/6] Mendownload NLTK Data...
echo  ------------------------------------------------------

python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet'); print('NLTK data downloaded successfully')"

if !ERRORLEVEL! NEQ 0 (
    echo  [!] Beberapa NLTK data mungkin gagal didownload.
    echo  Anda bisa download manual nanti.
) else (
    echo  [OK] NLTK data berhasil didownload!
)
echo.

REM ============================================
REM STEP 5: Setup .env file
REM ============================================
echo  [STEP 5/6] Setup file konfigurasi .env...
echo  ------------------------------------------------------

if exist "%~dp0.env" (
    echo  [!] File .env sudah ada. Skip pembuatan.
    echo  Edit manual jika perlu: %~dp0.env
) else (
    if exist "%~dp0.env.example" (
        copy "%~dp0.env.example" "%~dp0.env" >nul
        echo  [OK] File .env berhasil dibuat dari .env.example
        echo  [*] Edit file .env jika perlu mengubah konfigurasi database.
    ) else (
        echo  [!] File .env.example tidak ditemukan. Membuat .env default...
        (
            echo DB_HOST=localhost
            echo DB_PORT=3306
            echo DB_USER=root
            echo DB_PASSWORD=
            echo DB_NAME=sentiment_db
            echo FLASK_ENV=development
            echo FLASK_DEBUG=True
            echo SECRET_KEY=skripsi-secret
        ) > "%~dp0.env"
        echo  [OK] File .env default berhasil dibuat!
    )
)
echo.

REM ============================================
REM STEP 6: Setup Database MySQL
REM ============================================
echo  [STEP 6/6] Setup Database MySQL...
echo  ------------------------------------------------------
echo.

set "MYSQL_PATH="
if exist "C:\xampp\mysql\bin\mysql.exe" set "MYSQL_PATH=C:\xampp\mysql\bin\mysql.exe"
if "!MYSQL_PATH!"=="" if exist "D:\xampp\mysql\bin\mysql.exe" set "MYSQL_PATH=D:\xampp\mysql\bin\mysql.exe"
if "!MYSQL_PATH!"=="" (
    where mysql >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "MYSQL_PATH=mysql"
)

if "!MYSQL_PATH!"=="" (
    echo  [!] MySQL tidak ditemukan!
    echo.
    echo  Pastikan XAMPP sudah terinstall dan MySQL sudah berjalan.
    echo  Anda bisa setup database secara manual nanti dengan:
    echo    1. Buka XAMPP Control Panel
    echo    2. Start Apache dan MySQL
    echo    3. Jalankan: start_database.bat
    echo.
    goto :end_script
)

echo  [OK] MySQL ditemukan: !MYSQL_PATH!
echo.

"!MYSQL_PATH!" -u root -e "SELECT 1" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo  [!] MySQL service belum berjalan!
    echo  Silakan start MySQL dari XAMPP Control Panel terlebih dahulu.
    echo  Setelah MySQL berjalan, jalankan: start_database.bat
    echo.
    goto :end_script
)

echo  [OK] MySQL service sedang berjalan!
echo.
echo  Ingin setup database sekarang? [Y/N]
set /p DB_SETUP=  Pilihan Anda: 

if /i "!DB_SETUP!"=="Y" (
    echo.
    echo  [*] Membuat database sentiment_db...
    "!MYSQL_PATH!" -u root -e "CREATE DATABASE IF NOT EXISTS sentiment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    
    if exist "%~dp0sentiment_db.sql" (
        echo  [*] Mengimport data dari sentiment_db.sql...
        echo  * Ini mungkin memerlukan beberapa menit...
        "!MYSQL_PATH!" -u root sentiment_db < "%~dp0sentiment_db.sql"
        echo  [OK] Database berhasil diimport!
    ) else (
        echo  [*] Menjalankan database schema...
        pushd "%~dp0Backend"
        python init_db.py
        popd
        echo  [OK] Database schema berhasil dibuat!
    )
) else (
    echo  [-] Setup database dilewati.
    echo  Jalankan start_database.bat nanti untuk setup database.
)

:end_script
echo.
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|     [OK] INSTALASI SELESAI!                        ^|
echo  ^|                                                    ^|
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|  Cara menjalankan aplikasi:                          ^|
echo  ^|                                                    ^|
echo  ^|  1. Pastikan XAMPP MySQL sudah berjalan              ^|
echo  ^|  2. Klik 2x file: start.bat                         ^|
echo  ^|                                                    ^|
echo  ^|  Batch files yang tersedia:                          ^|
echo  ^|  * install.bat        - Script ini (install awal)    ^|
echo  ^|  * start.bat          - Jalankan aplikasi            ^|
echo  ^|  * start_database.bat - Setup/import database saja   ^|
echo  ^|  * stop.bat           - Hentikan aplikasi            ^|
echo  ^|                                                    ^|
echo  ======================================================
echo.
pause
