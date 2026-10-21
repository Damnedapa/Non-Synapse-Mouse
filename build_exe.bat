@echo off
REM ===================================================================
REM  Non-Synapse-Mouse  -  generar el ejecutable de Windows (.exe)
REM  Doble clic en este archivo (o ejecutalo desde CMD) EN WINDOWS.
REM  Requiere Python instalado (con "Add to PATH" marcado).
REM  Si hay un "icono.ico" en la carpeta, se usa como icono del .exe
REM  y tambien se mete dentro para la ventana y la bandeja del sistema.
REM  Si hay "mv_intro.mp3" y "mv_logo.png" en la carpeta, tambien van dentro (modo secreto).
REM ===================================================================

REM  >>> Cambia aqui la version en cada release <<<
set VERSION=1.4.0

echo.
echo == Instalando dependencias [PyInstaller, hidapi, pystray, pillow] ==
py -m pip install --upgrade pyinstaller hidapi pystray pillow

echo.
set "EXTRA="
if exist mv_intro.mp3 set "EXTRA=%EXTRA% --add-data mv_intro.mp3;."
if exist mv_logo.png set "EXTRA=%EXTRA% --add-data mv_logo.png;."
echo == Compilando Non-Synapse-Mouse_v%VERSION%.exe ==
if exist icono.ico goto CON_ICONO

echo    [sin icono personalizado: no se encontro icono.ico]
py -m PyInstaller --onefile --windowed --clean --hidden-import pystray._win32 %EXTRA% --name Non-Synapse-Mouse_v%VERSION% Non_Synapse_Mouse.py
goto FIN

:CON_ICONO
echo    [usando icono.ico]
py -m PyInstaller --onefile --windowed --clean --hidden-import pystray._win32 %EXTRA% --icon=icono.ico --add-data "icono.ico;." --name Non-Synapse-Mouse_v%VERSION% Non_Synapse_Mouse.py

:FIN
echo.
echo ===================================================================
echo  LISTO. El ejecutable esta en:  dist\Non-Synapse-Mouse_v%VERSION%.exe
echo  Compartelo tal cual, no necesita instalador.
echo  La configuracion se guarda en %%APPDATA%%\Non-Synapse-Mouse
echo ===================================================================
pause
