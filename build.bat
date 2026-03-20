@echo off
setlocal enabledelayedexpansion
title ITAD Pro — Compilador
color 0A
cls

echo.
echo  ============================================
echo   ITAD Pro v2.0 — Compilador a .EXE
echo  ============================================
echo.

:: ── VERIFICAR ADMINISTRADOR ───────────────────────────────────────────────────
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ejecutar como ADMINISTRADOR.
    pause & exit /b 1
)
echo [OK] Corriendo como Administrador.
echo.

:: ── BUSCAR PYTHON ─────────────────────────────────────────────────────────────
echo [1/5] Buscando Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala desde https://python.org
    echo         Marca "Add Python to PATH" durante la instalacion.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] !PYVER!
echo.

:: ── INSTALAR DEPENDENCIAS ─────────────────────────────────────────────────────
echo [2/5] Instalando dependencias...
python -m pip install pyinstaller customtkinter Pillow darkdetect --quiet --upgrade
echo [OK] Dependencias procesadas.
echo.

:: ── LOCALIZAR PYINSTALLER MANUALMENTE ────────────────────────────────────────
echo [3/5] Localizando PyInstaller...

:: Obtener la ruta de Scripts de Python programaticamente
for /f "tokens=*" %%p in ('python -c "import sys, os; print(os.path.join(os.path.dirname(sys.executable), 'Scripts'))"') do set SCRIPTS_DIR=%%p
echo     Carpeta Scripts: !SCRIPTS_DIR!

:: Verificar si pyinstaller.exe existe ahi
if exist "!SCRIPTS_DIR!\pyinstaller.exe" (
    set PYINST="!SCRIPTS_DIR!\pyinstaller.exe"
    echo [OK] PyInstaller encontrado: !PYINST!
) else (
    :: Intentar con where
    where pyinstaller >nul 2>&1
    if not errorlevel 1 (
        set PYINST=pyinstaller
        echo [OK] PyInstaller en PATH.
    ) else (
        :: Ultimo recurso: buscar con python -m
        python -c "import PyInstaller" >nul 2>&1
        if errorlevel 1 (
            echo [ERROR] PyInstaller no se instalo correctamente.
            echo.
            echo  Abre CMD como administrador y ejecuta manualmente:
            echo    pip install pyinstaller
            echo    pyinstaller --version
            echo.
            echo  Si pip install falla, prueba:
            echo    python -m pip install pyinstaller --user
            pause & exit /b 1
        )
        set PYINST=python -m PyInstaller
        echo [OK] Usando: python -m PyInstaller
    )
)
echo.

:: ── PREPARAR ICONO ────────────────────────────────────────────────────────────
echo [4/5] Preparando icono...
if not exist "assets" mkdir assets

set ICON_FLAG=
if not exist "assets\icon.ico" (
    python -c "
from PIL import Image, ImageDraw
sizes = [16,32,48,64,128,256]
imgs = []
for s in sizes:
    img = Image.new('RGBA', (s,s), (15,15,15,255))
    d = ImageDraw.Draw(img)
    m = max(2, s//8)
    d.rectangle([m,m,s-m-1,s-m-1], fill=(211,47,47,255))
    cx,cy,hw = s//2,s//2,s//4
    lw = max(1,s//16)
    d.line([(cx-hw,cy),(cx+hw,cy)], fill='white', width=lw)
    d.line([(cx,cy-hw),(cx,cy+hw)], fill='white', width=lw)
    imgs.append(img)
imgs[0].save('assets/icon.ico', format='ICO', sizes=[(s,s) for s in sizes])
" >nul 2>&1
)
if exist "assets\icon.ico" (
    set ICON_FLAG=--icon "assets\icon.ico"
    echo [OK] Icono listo.
) else (
    echo [AVISO] Sin icono, compilando igual.
)
echo.

:: ── COMPILAR ──────────────────────────────────────────────────────────────────
echo [5/5] Compilando... ^(1-4 minutos, no cierres la ventana^)
echo.

if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist\ITAD_Pro.exe" del /f /q "dist\ITAD_Pro.exe" >nul 2>&1

!PYINST! ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --name "ITAD_Pro" ^
    !ICON_FLAG! ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import darkdetect ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module matplotlib ^
    itad_pro.py

if errorlevel 1 (
    echo.
    echo  ============================================
    echo   [ERROR] Fallo la compilacion.
    echo  ============================================
    echo.
    echo  Causas mas comunes:
    echo   1. itad_pro.py no esta en la misma carpeta que build.bat
    echo   2. Antivirus elimino archivos temporales durante la compilacion
    echo      Solucion: desactiva el antivirus temporalmente o agrega
    echo      esta carpeta a las exclusiones de Windows Defender.
    echo   3. Falta de espacio en disco (necesita ~500 MB temporales)
    echo.
    pause & exit /b 1
)

:: ── RESULTADO ─────────────────────────────────────────────────────────────────
echo.
if exist "dist\ITAD_Pro.exe" (
    for %%A in ("dist\ITAD_Pro.exe") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576
    echo  ============================================
    echo   COMPILACION EXITOSA
    echo  ============================================
    echo   Archivo : dist\ITAD_Pro.exe
    echo   Tamano  : ~!SIZE_MB! MB
    echo  ============================================
    echo.
    explorer dist
) else (
    echo [ERROR] El .exe no aparece en dist\
    echo         Probablemente el antivirus lo elimino al generarse.
    echo         Agrega esta carpeta a exclusiones de Windows Defender e intenta de nuevo.
)

pause
