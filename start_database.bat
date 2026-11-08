@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Setup Database - Sentimen Analysis
color 0E

echo.
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|     SETUP DATABASE - SENTIMEN ANALYSIS             ^|
echo  ^|                                                    ^|
echo  ======================================================
echo.

REM ============================================
REM STEP 1: Cari MySQL
REM ============================================
echo  [1/3] Mencari MySQL...
echo  ------------------------------------------------------

set "MYSQL_PATH="
set "XAMPP_PATH="

if exist "C:\xampp\mysql\bin\mysql.exe" (
    set "MYSQL_PATH=C:\xampp\mysql\bin\mysql.exe"
    set "XAMPP_PATH=C:\xampp"
)
if "!MYSQL_PATH!"=="" if exist "D:\xampp\mysql\bin\mysql.exe" (
    set "MYSQL_PATH=D:\xampp\mysql\bin\mysql.exe"
    set "XAMPP_PATH=D:\xampp"
)
if "!MYSQL_PATH!"=="" (
    where mysql >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "MYSQL_PATH=mysql"
)

if "!MYSQL_PATH!"=="" (
    echo  [X] MySQL tidak ditemukan!
    echo.
    echo  Pastikan XAMPP sudah terinstall.
    echo  Download: https://www.apachefriends.org/
    echo.
    pause
    exit /b 1
)

echo  [OK] MySQL ditemukan: !MYSQL_PATH!
echo.

REM ============================================
REM STEP 2: Cek MySQL service berjalan
REM ============================================
echo  [2/3] Mengecek MySQL service...
echo  ------------------------------------------------------

"!MYSQL_PATH!" -u root -e "SELECT 1" >nul 2>&1
if !ERRORLEVEL! NEQ 0 goto :mysql_not_running
echo  [OK] MySQL sudah berjalan!
echo.
goto :check_db

:mysql_not_running
echo  [!] MySQL belum berjalan.

if "!XAMPP_PATH!"=="" (
    echo  [X] XAMPP path tidak diketahui. Start MySQL manual lalu jalankan lagi.
    pause
    exit /b 1
)

if not exist "!XAMPP_PATH!\mysql\bin\mysqld.exe" (
    echo  [X] Tidak bisa start MySQL otomatis.
    echo  Buka XAMPP Control Panel dan start MySQL manual,
    echo  lalu jalankan script ini lagi.
    pause
    exit /b 1
)

echo  [*] Mencoba start MySQL via XAMPP...
start "" "!XAMPP_PATH!\mysql\bin\mysqld.exe" --defaults-file="!XAMPP_PATH!\mysql\bin\my.ini"
echo  [*] Menunggu MySQL start (10 detik)...
timeout /t 10 /nobreak >nul

"!MYSQL_PATH!" -u root -e "SELECT 1" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo  [X] MySQL gagal start!
    echo  Buka XAMPP Control Panel dan start MySQL manual.
    pause
    exit /b 1
)
echo  [OK] MySQL berhasil distart!
echo.

REM ============================================
REM STEP 3: Cek database, buat & import jika belum ada
REM ============================================
:check_db
echo  [3/3] Mengecek database sentiment_db...
echo  ------------------------------------------------------

"!MYSQL_PATH!" -u root -e "USE sentiment_db" >nul 2>&1
if !ERRORLEVEL! NEQ 0 goto :db_not_exist

REM Database ada, cek jumlah tabel
set "TABLE_COUNT=0"
for /f "tokens=*" %%t in ('"!MYSQL_PATH!" -u root -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=0x73656E74696D656E745F6462;" 2^>nul') do set TABLE_COUNT=%%t

if !TABLE_COUNT! GTR 0 (
    echo  [OK] Database sentiment_db sudah ada dengan !TABLE_COUNT! tabel.
    echo.
    echo  Database sudah terisi. Ingin import ulang? [Y/N]
    echo  [!] PERINGATAN: Ini akan menimpa data yang sudah ada!
    set /p REIMPORT=  Pilihan Anda: 

    if /i "!REIMPORT!" NEQ "Y" (
        echo  [-] Import dibatalkan. Database tidak diubah.
        goto :done
    )
)

echo.
echo  [*] Menghapus database lama...
"!MYSQL_PATH!" -u root -e "DROP DATABASE sentiment_db;"

:db_not_exist
echo  [*] Membuat database sentiment_db...
"!MYSQL_PATH!" -u root -e "CREATE DATABASE sentiment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

if !ERRORLEVEL! NEQ 0 (
    echo  [X] Gagal membuat database!
    pause
    exit /b 1
)

if not exist "%~dp0sentiment_db.sql" goto :no_sql_file

echo  [*] Mengimport data dari sentiment_db.sql...
echo  * Ini mungkin memerlukan beberapa menit untuk file besar...
echo.
"!MYSQL_PATH!" -u root sentiment_db < "%~dp0sentiment_db.sql"

if !ERRORLEVEL! NEQ 0 (
    echo  [X] Gagal mengimport SQL file!
    pause
    exit /b 1
)
echo  [OK] Data berhasil diimport dari sentiment_db.sql!
goto :done

:no_sql_file
echo  [!] File sentiment_db.sql tidak ditemukan!
echo  [*] Membuat schema kosong via init_db.py...

if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
)

pushd "%~dp0Backend"
python init_db.py
popd

if !ERRORLEVEL! NEQ 0 (
    echo  [X] Gagal membuat schema!
    pause
    exit /b 1
)
echo  [OK] Schema database berhasil dibuat!

:done
echo.
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|     [OK] DATABASE SETUP SELESAI!                   ^|
echo  ^|                                                    ^|
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|  Database : sentiment_db                             ^|
echo  ^|  Host     : localhost                                ^|
echo  ^|  Port     : 3306                                     ^|
echo  ^|  User     : root                                     ^|
echo  ^|                                                    ^|
echo  ^|  Jalankan start.bat untuk memulai aplikasi!          ^|
echo  ^|                                                    ^|
echo  ======================================================
echo.
pause
