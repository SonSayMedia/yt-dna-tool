@echo off
chcp 65001 >nul
cd /d "%~dp0"
title YT DNA Tool

REM ================================================================
REM  Lan dau chay: tu tao moi truong ao + cai thu vien (1-2 phut).
REM  Cac lan sau: chay ngay.
REM ================================================================

if exist "venv\Scripts\python.exe" goto run

echo ================================================================
echo  [Lan dau] Dang chuan bi moi truong... vui long doi 1-2 phut.
echo  Dung tat cua so nay trong luc cai dat.
echo ================================================================

REM --- Tim Python: uu tien lenh 'py', sau do 'python' ---
set "PYCMD="
where py >nul 2>nul && set "PYCMD=py -3"
if not defined PYCMD (
  where python >nul 2>nul && set "PYCMD=python"
)
if not defined PYCMD goto nopython

REM --- Tao moi truong ao ---
%PYCMD% -m venv venv
if not exist "venv\Scripts\python.exe" goto venvfail

REM --- Cai thu vien ---
"venv\Scripts\python.exe" -m pip install --upgrade pip -q --disable-pip-version-check
"venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto pipfail
echo [OK] Da cai xong thu vien.
goto run

:nopython
echo.
echo [LOI] May chua cai Python.
echo   1. Tai Python 3.10+ tai: https://www.python.org/downloads/
echo   2. Khi cai, NHO TICH o "Add Python to PATH".
echo   3. Cai xong, chay lai run.bat
echo.
pause
exit /b 1

:venvfail
echo.
echo [LOI] Khong tao duoc moi truong ao. Hay kiem tra lai Python roi thu lai.
echo.
pause
exit /b 1

:pipfail
echo.
echo [LOI] Cai thu vien that bai (co the do mang). Kiem tra Internet roi chay lai run.bat
echo.
pause
exit /b 1

:run
REM --- Tao config lan dau tu file mau (chua co key; nhap key trong tab Cai dat) ---
if not exist config.json copy config.example.json config.json >nul

REM --- Chay app (tu mo trinh duyet http://127.0.0.1:5000) ---
"venv\Scripts\python.exe" app.py
