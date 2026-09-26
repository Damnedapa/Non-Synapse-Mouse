@echo off
REM ===================================================================
REM  Non-Synapse-Mouse  -  generar el ejecutable de Windows (.exe)
REM  Doble clic en este archivo (o ejecutalo desde CMD) EN WINDOWS.
REM  Requiere tener Python instalado (con "Add to PATH" marcado).
REM  Si hay un "icono.ico" en la carpeta, se usa como icono del .exe.
REM ===================================================================

echo.
echo == Instalando dependencias (PyInstaller + hidapi) ==
py -m pip install --upgrade pyinstaller hidapi

echo.
echo == Compilando Non-Synapse-Mouse.exe ==
if exist icono.ico (
    echo    (usando icono.ico como icono)
    py -m PyInstaller --onefile --windowed --icon=icono.ico --name Non-Synapse-Mouse Non_Synapse_Mouse.py
) else (
    echo    (sin icono personalizado: no se encontro icono.ico)
    py -m PyInstaller --onefile --windowed --name Non-Synapse-Mouse Non_Synapse_Mouse.py
)

echo.
echo ===================================================================
echo  LISTO. El ejecutable esta en la carpeta:  dist\Non-Synapse-Mouse.exe
echo  Puedes copiarlo y compartirlo tal cual (no necesita instalador).
echo  El archivo razer_presets.json se creara junto al .exe al usarlo.
echo ===================================================================
pause
