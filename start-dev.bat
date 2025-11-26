@echo off
REM Clean startup script for Almacena Dashboard (Windows)

echo Cleaning up old dev servers...

REM Kill any existing Node processes running Vite
taskkill /F /IM node.exe /FI "WINDOWTITLE eq vite*" 2>NUL

REM Wait a moment
timeout /t 2 /nobreak >NUL

echo Setting up public directory...

REM Create public directory if it doesn't exist
if not exist "public" mkdir public

REM Copy data files to public directory
if exist "..\data" (
    xcopy /E /I /Y ..\data public\data >NUL
    echo Data files copied to public directory
) else (
    echo Warning: ..\data directory not found, using mock data
)

echo Starting Vite dev server...
npm run dev
