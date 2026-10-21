# Guía: publicar Non-Synapse-Mouse en winget y Scoop

Nada de esto está validado en Windows desde aquí. Pruébalo tú antes de anunciarlo.

## 0. Preparar los manifiestos
1. Publica primero la release v1.4.0 en GitHub con el asset `Non-Synapse-Mouse_v1.4.0.exe` (el nombre exacto importa: `Non-Synapse-Mouse_v<versión>.exe`, el que genera `build_exe.bat`).
2. En Windows o aquí: `python prepare_packaging.py Non-Synapse-Mouse_v1.4.0.exe 1.4.0 --out out`
3. Te saca el SHA256 (pégalo también en `RELEASE_v1.4.0.md`) y genera `out/winget/...` y `out/scoop/non-synapse-mouse.json`.

## 1. winget
1. Instala wingetcreate: `winget install Microsoft.WingetCreate`.
2. Opción fácil: `wingetcreate new https://github.com/Damnedapa/Non-Synapse-Mouse/releases/download/v1.4.0/Non-Synapse-Mouse_v1.4.0.exe`. Responde igual que en las plantillas (PackageIdentifier `Damnedapa.NonSynapseMouse`, tipo portable, comando `non-synapse-mouse`).
3. Opción manual: haz fork de `microsoft/winget-pkgs`, copia `out/winget/manifests/...` a la misma ruta y valida: `winget validate --manifest <carpeta>`; prueba: `winget install --manifest <carpeta>` (requiere `winget settings --enable LocalManifestFiles`).
4. Abre la PR. Un bot la valida (incluye antivirus y SmartScreen) y un moderador la aprueba; tarda días.
5. Siguientes versiones: `wingetcreate update Damnedapa.NonSynapseMouse --version X.Y.Z --urls <url del exe> --submit`.

## 2. Scoop
1. Crea un repo `scoop-bucket` en tu cuenta con una carpeta `bucket/`.
2. Copia `out/scoop/non-synapse-mouse.json` a `bucket/`.
3. Prueba: `scoop bucket add damnedapa https://github.com/Damnedapa/scoop-bucket` y `scoop install non-synapse-mouse`.
4. `checkver` y `autoupdate` están puestos: `scoop checkver -u` (o el Excavator de GitHub Actions) actualiza versión y hash solos.

## 3. Cosas a tener en cuenta
- El exe de PyInstaller sin firmar puede disparar falsos positivos de antivirus o SmartScreen; en winget puede bloquear la PR hasta que se revise.
- El actualizador integrado de la app y winget/Scoop conviven mal: si lo instalan por gestor, mejor actualizar con `winget upgrade` / `scoop update`. Puedes avisarlo en el README.
- winget portable no crea acceso directo en el menú Inicio (Scoop sí, vía `shortcuts`).
- Los datos siguen en `%APPDATA%\Non-Synapse-Mouse`, así que desinstalar no los borra.

## 4. Snippet para el README (solo cuando esté aprobado)
```
winget install Damnedapa.NonSynapseMouse
scoop bucket add damnedapa https://github.com/Damnedapa/scoop-bucket
scoop install non-synapse-mouse
```
