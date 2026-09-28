# Non-Synapse-Mouse · v1.0.0 → v1.1.0

> 🌐 **Español** abajo · **English** below

## 🇪🇸 Cambios

### Perfiles (lo gordo)
1. **Modo control, como Synapse:** con el programa abierto, el botón de perfil del ratón lo gestiona el programa. Cambio de perfil **instantáneo y exacto**, sin adivinar por el DPI.
2. **5 perfiles editables** en el programa (casilla vacía = perfil desactivado); se aplican solos al abrirlo y se recuerdan entre sesiones.
3. Clic en el nombre de un perfil para activarlo; *DPI abajo* vuelve al perfil anterior.
4. **Los perfiles internos del ratón no se tocan:** al cerrar el programa, el ratón vuelve a su modo normal.
5. Si el ratón se duerme o se reinicia, el programa **retoma el control solo**.
6. **Grabar en el ratón:** asistente guiado que guarda tus perfiles en la memoria del ratón, color a color (🔴 rojo · 🟢 verde · 🔵 azul · 🩵 turquesa · 🟡 amarillo), y comprueba cada uno. Así los tienes con el programa cerrado o en otro PC.
7. **Al cerrar**, pregunta si quieres grabar los perfiles en el ratón (solo si han cambiado; desactivable).
8. Cada perfil muestra su **circulito de color**, y el aviso emergente sale de ese color.
9. **Modo compatibilidad** de respaldo (si Windows no deja escuchar el botón): detecta el perfil por el DPI y **nunca sobrescribe tus perfiles**.
10. *Restablecer perfiles* vuelve a los valores por defecto.

### Mapeo de botones (nuevo)
11. **Pestaña Mapeo:** remapea pulsar rueda, rueda arriba/abajo y los laterales a **cualquier acción**: cambiar de perfil, clics, doble clic, copiar/pegar/deshacer, Alt+Tab, mostrar escritorio, captura, multimedia, volumen o **cualquier combinación de teclas** (`ctrl+shift+s`, `alt+f4`, `f13`…).
12. Las teclas se mantienen mientras mantienes el botón.
13. En la Viper, los **laterales derechos** funcionan en modo control y admiten las mismas acciones.
14. Desactivado por defecto. El clic izquierdo y el derecho no se remapean nunca.

### Automático y más sencillo
15. **Se conecta solo** al abrir y **se reconecta** si desenchufas el ratón o se duerme.
16. La **batería se refresca sola** cada minuto.
17. Ventana mucho más limpia: fuera el botón de conectar, los botones por perfil, anclar/reanclar y el deslizador suelto.
18. Pestañas: **Perfiles · Iluminación · Mapeo · Opciones**.

### Opciones y sistema
19. **Minimizar a la bandeja del sistema** (junto al reloj).
20. **Arrancar con Windows** (minimizado).
21. **Buscar actualizaciones** al iniciar y **descargar e instalar** la nueva versión con un clic.
22. **Reportar un error:** abre un *issue* de GitHub con los datos técnicos ya rellenos.
23. **Solo se abre una copia** a la vez.
24. La configuración se guarda en `%APPDATA%\Non-Synapse-Mouse` (se migra sola la antigua).

### Arreglos
25. El **registro y los errores** ya salen en el idioma elegido (antes, algunos siempre en castellano).
26. Icono propio en la ventana y la barra de tareas; la versión aparece en el título.

### ⚠️ Avisos
- **El mapeo de botones aún NO se guarda en la memoria del ratón:** funciona con el programa abierto (también minimizado o en la bandeja). En la memoria solo se graban los DPI de cada perfil.
- El mapeo usa un gancho de Windows: **algunos anticheats pueden detectarlo**. Desactívalo al jugar con anticheat.
- En modo control, el LED de perfil de debajo del ratón se queda fijo (igual que con Synapse; lo controla el firmware).
- Quien venga de la v1.0.0 tiene que bajar esta versión a mano una vez; a partir de aquí se actualiza sola.

---

## 🇬🇧 Changes

### Profiles (the big one)
1. **Control mode, like Synapse:** while the app is open, it handles the mouse's profile button. Profile switching is **instant and exact**, no more guessing by DPI.
2. **5 editable profiles** in the app (empty box = profile disabled); applied automatically on launch and remembered between sessions.
3. Click a profile name to activate it; *DPI down* goes back to the previous profile.
4. **The mouse's own onboard profiles are never touched:** when you close the app, the mouse returns to normal mode.
5. If the mouse sleeps or resets, the app **takes control again on its own**.
6. **Write to mouse:** guided wizard that stores your profiles in the mouse's memory, colour by colour (🔴 red · 🟢 green · 🔵 blue · 🩵 turquoise · 🟡 yellow), checking each one. You keep them with the app closed or on another PC.
7. **On exit**, it asks whether to write your profiles to the mouse (only if they changed; can be turned off).
8. Each profile shows its **colour dot**, and the pop-up uses that colour.
9. **Compatibility mode** fallback (if Windows won't let the app listen to the button): detects the profile by DPI and **never overwrites your profiles**.
10. *Reset profiles* restores the defaults.

### Button mapping (new)
11. **Mapping tab:** remap wheel click, wheel up/down and side buttons to **any action**: switch profile, clicks, double click, copy/paste/undo, Alt+Tab, show desktop, screenshot, media, volume or **any key combination** (`ctrl+shift+s`, `alt+f4`, `f13`…).
12. Keys are held while you hold the button.
13. On the Viper, the **right side buttons** work in control mode and take the same actions.
14. Off by default. Left and right click are never remapped.

### Automatic and simpler
15. **Connects by itself** on launch and **reconnects** if the mouse is unplugged or goes to sleep.
16. **Battery refreshes on its own** every minute.
17. Much cleaner window: no more connect button, per-profile buttons, anchor/re-anchor or loose slider.
18. Tabs: **Profiles · Lighting · Mapping · Settings**.

### Settings and system
19. **Minimize to the system tray** (next to the clock).
20. **Start with Windows** (minimized).
21. **Check for updates** on startup and **download & install** the new version with one click.
22. **Report a bug:** opens a GitHub issue with the technical details already filled in.
23. **Only one copy** runs at a time.
24. Settings are stored in `%APPDATA%\Non-Synapse-Mouse` (the old file is migrated automatically).

### Fixes
25. The **log and error messages** now follow the selected language (some used to be always in Spanish).
26. Proper window/taskbar icon; the version is shown in the title bar.

### ⚠️ Notes
- **Button mapping is NOT saved to the mouse's memory yet:** it works while the app is open (also minimized or in the tray). Only each profile's DPI is written to the mouse.
- Mapping uses a Windows hook: **some anti-cheat systems may detect it**. Turn it off when playing games with anti-cheat.
- In control mode, the profile LED under the mouse stays fixed (same as with Synapse; it's firmware-controlled).
- Coming from v1.0.0? Download this version manually once; from now on it updates itself.
