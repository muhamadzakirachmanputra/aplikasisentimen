@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Aplikasi Sentimen Analysis - Running
color 0A

echo.
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|     MENJALANKAN APLIKASI SENTIMEN ANALYSIS         ^|
echo  ^|                                                    ^|
echo  ======================================================
echo.

REM ============================================
REM Cek Virtual Environment
REM ============================================
if not exist "%~dp0venv\Scripts\activate.bat" (
    echo  [X] Virtual environment tidak ditemukan!
    echo  Jalankan install.bat terlebih dahulu.
    echo.
    pause
    exit /b 1
)

REM ============================================
REM Cek .env file
REM ============================================
echo  [1/4] Mengecek file .env...
echo  ------------------------------------------------------

if not exist "%~dp0.env" (
    if exist "%~dp0.env.example" (
        copy "%~dp0.env.example" "%~dp0.env" >nul
        echo  [OK] File .env dibuat dari .env.example
    ) else (
        echo  [!] File .env tidak ditemukan!
        echo  Jalankan install.bat terlebih dahulu.
        pause
        exit /b 1
    )
) else (
    echo  [OK] File .env ditemukan!
)
echo.

REM ============================================
REM Aktifkan Virtual Environment
REM ============================================
echo  [2/4] Mengaktifkan Virtual Environment...
echo  ------------------------------------------------------

call "%~dp0venv\Scripts\activate.bat"
echo  [OK] Virtual Environment aktif!
echo.

REM ============================================
REM Cek MySQL dan Database
REM ============================================
echo  [3/4] Mengecek MySQL dan Database...
echo  ------------------------------------------------------

set "MYSQL_PATH="
if exist "C:\xampp\mysql\bin\mysql.exe" set "MYSQL_PATH=C:\xampp\mysql\bin\mysql.exe"
if "!MYSQL_PATH!"=="" if exist "D:\xampp\mysql\bin\mysql.exe" set "MYSQL_PATH=D:\xampp\mysql\bin\mysql.exe"
if "!MYSQL_PATH!"=="" (
    where mysql >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "MYSQL_PATH=mysql"
)

if "!MYSQL_PATH!"=="" (
    echo  [!] MySQL tidak ditemukan di PATH atau XAMPP.
    echo  Pastikan MySQL sudah berjalan sebelum melanjutkan.
    echo.
    set /p CONTINUE=  Lanjutkan tetap? [Y/N]: 
    if /i "!CONTINUE!" NEQ "Y" exit /b 1
    goto :start_flask
)

"!MYSQL_PATH!" -u root -e "SELECT 1" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo  [!] MySQL belum berjalan. Mencoba start via XAMPP...
    
    if exist "C:\xampp\xampp_start.exe" (
        start "" "C:\xampp\xampp_start.exe"
    ) else if exist "D:\xampp\xampp_start.exe" (
        start "" "D:\xampp\xampp_start.exe"
    ) else (
        echo.
        echo  [X] Tidak bisa start MySQL otomatis.
        echo  Silakan buka XAMPP Control Panel dan start MySQL manual.
        echo.
        pause
        exit /b 1
    )
    
    echo  [*] Menunggu MySQL start...
    timeout /t 5 /nobreak >nul
    
    "!MYSQL_PATH!" -u root -e "SELECT 1" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo  [X] MySQL masih belum bisa diakses.
        echo  Pastikan MySQL sudah berjalan dari XAMPP Control Panel.
        echo.
        pause
        exit /b 1
    )
)
echo  [OK] MySQL berjalan!

"!MYSQL_PATH!" -u root -e "USE sentiment_db" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo  [!] Database sentiment_db belum ada. Membuat...
    "!MYSQL_PATH!" -u root -e "CREATE DATABASE IF NOT EXISTS sentiment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    
    if exist "%~dp0sentiment_db.sql" (
        echo  [*] Mengimport sentiment_db.sql...
        "!MYSQL_PATH!" -u root sentiment_db < "%~dp0sentiment_db.sql"
    ) else (
        pushd "%~dp0Backend"
        python init_db.py
        popd
    )
    echo  [OK] Database berhasil disetup!
) else (
    echo  [OK] Database sentiment_db ditemukan!
)
echo.

REM ============================================
REM Jalankan Flask Server, tunggu siap, baru buka browser
REM ============================================
:start_flask
echo  [4/4] Menjalankan Flask Server...
echo  ------------------------------------------------------
echo.

cd /d "%~dp0Backend"

REM Jalankan Flask di background
start "FlaskServer" /b python app.py

echo  [*] Menunggu server siap...

REM Tunggu sampai port 5000 benar-benar listening (max 30 detik)
set "READY=0"
for /l %%i in (1,1,30) do (
    if "!READY!"=="0" (
        timeout /t 1 /nobreak >nul
        netstat -ano 2>nul | findstr ":5000" | findstr "LISTENING" >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set "READY=1"
        )
    )
)

if "!READY!"=="0" (
    echo  [X] Server gagal start dalam 30 detik!
    echo  Cek error di atas.
    pause
    exit /b 1
)

echo  [OK] Server Flask sudah berjalan!
echo.
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|  Aplikasi berjalan di: http://127.0.0.1:5000       ^|
echo  ^|  Tekan CTRL+C untuk menghentikan server            ^|
echo  ^|                                                    ^|
echo  ======================================================
echo.

REM Baru sekarang buka browser, karena server sudah pasti siap
start "" http://127.0.0.1:5000

REM Tetap jaga window terbuka agar user bisa lihat log dan CTRL+C
echo  [*] Server sedang berjalan... Tekan tombol apapun untuk menghentikan.
pause >nul

REM Setelah user tekan tombol, kill Flask
echo.
echo  [*] Menghentikan server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo  [OK] Server dihentikan.
pause
