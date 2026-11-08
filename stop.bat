@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Stop Aplikasi Sentimen Analysis
color 0C

echo.
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|     MENGHENTIKAN APLIKASI SENTIMEN ANALYSIS        ^|
echo  ^|                                                    ^|
echo  ======================================================
echo.

REM ============================================
REM Kill Flask/Python processes on port 5000
REM ============================================
echo  [1/2] Menghentikan Flask Server...
echo  ------------------------------------------------------

REM Cari dan kill proses python yang menjalankan app.py
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING" 2^>nul') do (
    echo  [*] Menghentikan proses PID: %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Kill semua proses python yang mungkin terkait
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Aplikasi Sentimen*" >nul 2>&1

echo  [OK] Flask server dihentikan!
echo.

REM ============================================
REM Opsi: Stop MySQL
REM ============================================
echo  [2/2] MySQL Service...
echo  ------------------------------------------------------
echo.
echo  Apakah ingin menghentikan MySQL juga? (Y/N)
set /p STOP_MYSQL=  Pilihan Anda: 

if /i "!STOP_MYSQL!"=="Y" (
    echo.
    echo  [*] Menghentikan MySQL...
    
    if exist "C:\xampp\xampp_stop.exe" (
        start "" "C:\xampp\xampp_stop.exe"
    ) else if exist "D:\xampp\xampp_stop.exe" (
        start "" "D:\xampp\xampp_stop.exe"
    ) else (
        taskkill /F /IM mysqld.exe >nul 2>&1
    )
    
    echo  [OK] MySQL dihentikan!
) else (
    echo  [-] MySQL tetap berjalan.
)

echo.
echo  ======================================================
echo  ^|                                                    ^|
echo  ^|     [OK] APLIKASI BERHASIL DIHENTIKAN              ^|
echo  ^|                                                    ^|
echo  ======================================================
echo.
pause
