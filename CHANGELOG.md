# Changelog · Historial de cambios

> 🌐 **English** first · **Español** debajo de cada versión
>
> **v1.4.0 is the first public release since v1.0.0.** Versions 1.1.0, 1.2.0 and 1.3.0
> were internal development versions and were never published; their detailed notes
> are kept at the bottom for reference.
> **La v1.4.0 es la primera versión pública desde la v1.0.0.** La 1.1.0, 1.2.0 y 1.3.0
> fueron versiones internas de desarrollo y nunca se publicaron; sus notas detalladas
> están al final como referencia.

---

## v1.4.0 — everything since v1.0.0 · todo lo nuevo desde la v1.0.0

### English

**Profiles that work like Synapse**
- **Control mode:** while the app is open it takes over the mouse's profile button and switches your **5 DPI profiles instantly and exactly** (DPI up/down go next/previous). No guessing, no "start tracking". The mouse's onboard profiles are never touched; closing the app returns the mouse to normal.
- **Compatibility mode** as an automatic fallback if Windows won't let the app listen to the button: it infers the profile from the DPI and never overwrites anything.
- **Write to mouse:** a guided wizard stores your profiles in the mouse's own memory (colour by colour, checking each one), and the app offers it on exit.
- Edit DPI per profile, leave one empty to skip it, **Use** button to activate one, polling rate 125/500/1000 Hz.
- **Logo blink** in the profile's colour (three pulses) when you change profile, then the LED goes back to how it was. Doesn't write the mouse's memory.
- Optional **profile notification** with a 5-segment bar and the battery level.

**Buttons**
- **Software remapping** (Windows): wheel click, wheel up/down and side buttons to clicks, double click, copy/paste, Alt+Tab, media keys, switching profile or **any key combination**. Off by default; works while the app is open; not saved to the mouse.
- **Sniper button:** assign it to any button that reports release; the DPI drops while you hold it.
- **Special buttons** (profile, DPI and the Viper's right side buttons, handled by the mouse itself) can be remapped too, in control mode.
- What you can't use right now is **greyed out**.

**Battery**
- In the sidebar, plus **alerts** at the top right of the screen at 90, 80 … 20, 15, 10, 8, 6, 5, 4, 3, 2 and 1 %, one when you open the app and one when it's fully charged. No repeats when the reading wobbles by 1 %.
- **Fixed:** the battery could show **0 %** (or a wrong level) while the app started or the mouse woke up. See *Reliability*.

**Interface**
- New **Windows 11 Settings** look: sidebar, row cards, switches, everything applies instantly.
- **Dark or light mode**, smooth (anti-aliased) switches, dots and sliders, crisp at 125 %/150 % scaling.
- **Resizable** window that remembers size and position.
- **English by default**, Spanish with the **ES | EN** switch in the sidebar.
- **Colour picker** with a colour wheel, a brightness bar and the `#RRGGBB` code (editable both ways), plus a quick palette.
- **Themes:** colours plus the shape of the parts (round, square, cut corners, diamond, optional neon glow). Make your own as a `.json` file; a template and a "Neon" example are included.
- Welcome screen on first run, **What's new** after updating.

**System**
- **System tray** (status, profile switching from the menu), **start with Windows**, **update check and one-click install**, **Report a bug** with the technical details filled in.
- Settings in `%APPDATA%\Non-Synapse-Mouse` (the v1.0.0 file next to the program is carried over automatically); only one copy runs at a time.
- **Log always in English**, so it can be read in any bug report. Ko-fi shortcut in the sidebar.

**Reliability (debugging pass before release)**
- Only answers that **echo the command sent** and come back with status *OK* are trusted. A wireless receiver can return the previous answer or zeros while the mouse wakes up; that was the cause of the fake 0 % battery and could also give wrong DPI readings.
- An odd battery reading (0 % without charging, or a jump of 25 points or more) is **checked again** and only shown if it repeats; a failed reading is retried within seconds instead of waiting a minute.
- A sleeping mouse is no longer treated as unplugged.
- **Fast presses of the profile button are no longer lost** (a 250 ms filter meant for the scroll wheel was also eating real presses).
- Periodic reads and DPI changes run in **their own threads**: the window no longer freezes for up to several seconds when the receiver is slow or busy.
- Fewer memory writes: a write is not re-sent just because the receiver answered late.
- Settings are **saved safely** (temporary file + backup); a damaged or hand-edited file no longer stops the app from opening, and values it doesn't understand fall back to their defaults.
- Update download checks that the file is complete and is really a Windows program before offering to open it.
- The log keeps the last 1,500 lines, so it doesn't grow forever if the app runs for days.

**Not included on purpose:** per-profile polling rate (changing it without noticing is a trap on high-refresh screens). Lighting is static colour + brightness only.

### Español

**Perfiles que funcionan como en Synapse**
- **Modo control:** con el programa abierto, el botón de perfil del ratón lo gestiona el programa, que cambia tus **5 perfiles de DPI al instante y sin fallos** (DPI arriba/abajo van al siguiente/anterior). Sin adivinar y sin «empezar seguimiento». Los perfiles internos del ratón no se tocan; al cerrar, el ratón vuelve a su modo normal.
- **Modo compatibilidad** de respaldo automático si Windows no deja escuchar el botón: deduce el perfil por el DPI y nunca sobrescribe nada.
- **Grabar en el ratón:** un asistente guarda tus perfiles en la memoria del propio ratón (color a color, comprobando cada uno), y el programa te lo ofrece al cerrar.
- DPI de cada perfil editable, deja uno vacío para saltarlo, botón **Usar** para activar uno, frecuencia de sondeo 125/500/1000 Hz.
- **Parpadeo del logo** con el color del perfil (tres pulsos) al cambiar de perfil, y el LED vuelve a como estaba. No escribe en la memoria del ratón.
- **Aviso de perfil** opcional con barra de 5 tramos y el nivel de batería.

**Botones**
- **Remapeo por software** (Windows): pulsar rueda, rueda arriba/abajo y laterales a clics, doble clic, copiar/pegar, Alt+Tab, teclas multimedia, cambio de perfil o **cualquier combinación de teclas**. Desactivado por defecto; funciona con el programa abierto; no se guarda en el ratón.
- **Botón sniper:** asígnalo a cualquier botón que avise al soltar; el DPI baja mientras lo mantienes.
- Los **botones especiales** (perfil, DPI y los laterales derechos de la Viper, que gestiona el propio ratón) también se pueden remapear, en modo control.
- Lo que no puedes usar en ese momento sale **en gris**.

**Batería**
- En la barra lateral, y **avisos** arriba a la derecha de la pantalla al 90, 80 … 20, 15, 10, 8, 6, 5, 4, 3, 2 y 1 %, uno al abrir el programa y otro al cargar del todo. Sin repetirse si la lectura baila un 1 %.
- **Corregido:** la batería podía marcar **0 %** (o un nivel equivocado) al arrancar el programa o al despertar el ratón. Ver *Fiabilidad*.

**Interfaz**
- Aspecto nuevo de **Configuración de Windows 11**: barra lateral, tarjetas-fila, interruptores, todo se aplica al momento.
- **Modo oscuro o claro**, interruptores, puntos y deslizadores suavizados (sin dientes de sierra), nítida con escalado al 125 %/150 %.
- Ventana **redimensionable** que recuerda tamaño y posición.
- **Inglés por defecto**, español con el interruptor **ES | EN** de la barra lateral.
- **Selector de color** con disco de color, barra de brillo y el código `#RRGGBB` (editable en los dos sentidos), además de la paleta rápida.
- **Temas:** colores más la forma de las piezas (redonda, cuadrada, esquinas cortadas, rombo, halo de neón opcional). Haz el tuyo en un `.json`; vienen una plantilla y un ejemplo «Neon».
- Bienvenida la primera vez y **Novedades** al actualizar.

**Sistema**
- **Bandeja del sistema** (estado, cambio de perfil desde el menú), **iniciar con Windows**, **buscar e instalar actualizaciones con un clic**, **Reportar un error** con los datos técnicos ya rellenos.
- Configuración en `%APPDATA%\Non-Synapse-Mouse` (el archivo de la v1.0.0 junto al programa se pasa solo); solo se abre una copia a la vez.
- **Registro siempre en inglés**, para que se entienda en cualquier reporte de error. Acceso a Ko-fi en la barra lateral.

**Fiabilidad (depuración antes de publicar)**
- Solo se fía de las respuestas que **hacen eco de la orden enviada** y vuelven con estado *OK*. Un receptor inalámbrico puede devolver la respuesta anterior o ceros mientras el ratón se despierta: esa era la causa del 0 % de batería falso y también podía dar lecturas de DPI malas.
- Una lectura de batería rara (0 % sin cargar, o un salto de 25 puntos o más) **se vuelve a comprobar** y solo se muestra si se repite; una lectura fallida se reintenta en segundos en vez de esperar un minuto.
- Un ratón dormido ya no se trata como desenchufado.
- **Ya no se pierden pulsaciones rápidas del botón de perfil** (un filtro de 250 ms pensado para la rueda también se comía pulsaciones de verdad).
- Las lecturas periódicas y los cambios de DPI van en **hilos propios**: la ventana ya no se congela (hasta varios segundos) cuando el receptor va lento u ocupado.
- Menos escrituras en la memoria: una escritura no se reenvía solo porque el receptor contestó tarde.
- La configuración **se guarda de forma segura** (archivo temporal + copia de seguridad); un archivo estropeado o editado a mano ya no impide abrir el programa, y lo que no entienda vuelve a su valor por defecto.
- La descarga de actualizaciones comprueba que el archivo está completo y que de verdad es un programa de Windows antes de ofrecer abrirlo.
- El registro guarda las últimas 1.500 líneas, para que no crezca sin fin con el programa días abierto.

**Fuera a propósito:** frecuencia de sondeo por perfil (cambiarla sin darte cuenta es una trampa con pantallas de muchos Hz). La iluminación es solo color fijo + brillo.

---

## v1.0.0

### English
First public release: DPI, polling rate, battery, logo LED (colour, brightness, on/off), 5 DPI presets with profile detection and a pop-up, English/Spanish interface, ~20 Razer models plus auto-detection.

### Español
Primera versión pública: DPI, frecuencia de sondeo, batería, LED del logo (color, brillo, encendido/apagado), 5 presets de DPI con detección de perfil y aviso emergente, interfaz en español e inglés, unos 20 modelos Razer más autodetección.

---

<details>
<summary><b>Development history · Historial de desarrollo</b> (internal versions 1.1.0 – 1.3.0 and v1.4.0 dev notes, never published · versiones internas, nunca publicadas)</summary>

### v1.4.0 (development notes · notas de desarrollo)

#### English
**Themes, light mode, smooth edges and a colour picker.**
- **Theme system.** A theme is now a set of colour tokens **plus the shape of the parts**: `round` (Windows 11), `square`, `chamfer` (cut corners) or `diamond`, with corner size, border width and an optional **neon glow**. No colour is hard-coded in the interface any more; everything comes from the theme.
- **Custom themes** as `.json` files in `%APPDATA%\Non-Synapse-Mouse\themes`. *Settings › Appearance › Custom themes › Open folder* creates `_template.json` (every key, documented) and `_example-neon.json`. A theme only overrides what it lists; the rest comes from its base. Invalid values are ignored and written to the log. Optional `font` (used if installed).
- **Light mode.** Turn off *Dark mode* in Settings. Theme and mode apply on restart: a *Restart now* card appears and the app closes and reopens by itself (the mouse loses nothing). The title bar follows the mode.
- **Smooth edges everywhere.** Switches, the ES | EN switch, profile dots, slider, battery icon, colour swatches, the "connecting" spinner and the sidebar marker are drawn anti-aliased (no more jagged corners), in any shape the theme asks for.
- **Colour picker.** *Lighting › Current colour › Choose…* opens a colour wheel (hue + saturation) with a brightness bar, a new/current preview and the `#RRGGBB` code, editable both ways: type a code and the marker moves; move the marker and the code changes. *Apply* sends it to the mouse.
- **Greyed-out buttons.** On *Buttons*, the Windows buttons are greyed out and can't be changed while *Software remapping* is off; the buttons the mouse reports follow control mode; *Sniper DPI* is greyed when neither is on.
- **The log is always in English** (also the mouse's own messages), so any log pasted into a bug report can be read.
- **Spot me a scoop:** Ko-fi shortcut at the bottom of the sidebar (Language, Log and About move up a bit).
- Texts: *Theme › Coming soon.*; *Battery alerts › Status pop-ups.*; About now says "Talks directly to the mouse: no intrusive background services, no account and no drivers to install."; the license line is just *GPL-3.0* (the "no warranty" notice stays in the small text below, as the GPL asks).

#### Español
**Temas, modo claro, bordes suaves y selector de color.**
- **Sistema de temas.** Un tema es ahora un juego de colores **más la forma de las piezas**: `round` (Windows 11), `square`, `chamfer` (esquinas cortadas) o `diamond` (rombo), con tamaño de esquina, grosor de borde y **halo de neón** opcional. La interfaz ya no tiene colores escritos a mano: todo sale del tema.
- **Temas propios** en archivos `.json` en `%APPDATA%\Non-Synapse-Mouse\themes`. *Ajustes › Apariencia › Temas personalizados › Abrir carpeta* crea `_template.json` (todas las claves, explicadas) y `_example-neon.json`. Un tema solo cambia lo que trae; el resto sale de su base. Los valores no válidos se ignoran y se anotan en el registro. `font` opcional (se usa si está instalada).
- **Modo claro.** Apaga *Modo oscuro* en Ajustes. Tema y modo se aplican al reiniciar: aparece una tarjeta *Reiniciar ahora* y el programa se cierra y se vuelve a abrir solo (el ratón no pierde nada). La barra de título sigue al modo.
- **Bordes suaves en todo.** Interruptores, el ES | EN, los puntos de perfil, el deslizador, el icono de batería, las muestras de color, el indicador de «conectando» y la marca de la barra lateral se dibujan con antialiasing (adiós dientes de sierra), con la forma que pida el tema.
- **Selector de color.** *Iluminación › Color actual › Elegir…* abre un disco de color (tono + saturación) con barra de brillo, vista previa nuevo/actual y el código `#RRGGBB`, editable en los dos sentidos: escribes un código y se mueve el marcador; mueves el marcador y cambia el código. *Aplicar* lo manda al ratón.
- **Botones en gris.** En *Botones*, los de Windows salen en gris y no se pueden cambiar con el *Remapeo por software* apagado; los que avisa el ratón siguen al modo control; el *DPI del sniper* sale en gris si no está ninguno de los dos.
- **El registro va siempre en inglés** (también los mensajes del propio ratón), para que cualquier registro pegado en un reporte se entienda.
- **Spot me a scoop:** acceso a Ko-fi abajo en la barra lateral (Idioma, Registro y Acerca de suben un poco).
- Textos: *Tema › Próximamente.*; *Avisos de batería › Pop-ups de estado.*; Acerca de dice ahora «Comunicación directa con el ratón, sin servicios en segundo plano intrusivos, sin cuenta y sin instalar drivers.»; la licencia pone solo *GPL-3.0* (el aviso de «sin garantía» se queda en la letra pequeña de debajo, como pide la GPL).

---

### v1.3.0

#### English
**Bigger, resizable, with battery alerts, a profile blink and a sniper button.**
- **Language switch (ES | EN) in the sidebar**, right above *Log*. **English is now the default** (one-time reset on upgrade, even if an older version had saved Spanish; after that, your choice is always remembered). It's no longer in Settings.
- **Resizable window:** it opens as tall as your screen's work area allows (so most pages need no scrollbar; only the long *Settings* page may scroll), you can enlarge or shrink it (cards re-wrap their text), it never goes to the tray while starting up, and it **remembers its size and position**.
- **New mouse silhouette rendering:** thicker lines and smooth, anti-aliased edges (no more jagged "saw teeth"). **New app icon** built from it.
- **Battery alerts:** a separate pop-up at the **top right of the screen** at **90, 80, 70, 60, 50, 40, 30, 20, 15, 10, 8, 6, 5, 4, 3, 2 and 1 %**, plus one **every time you open the app** with the current level, and one when the battery is **fully charged**. A reading that wobbles ±1 % doesn't repeat the alert. Amber below 20 %, red below 10 %. Can be turned off, with a *Test* button (Settings › Battery). The battery is now read in the background (once a minute) while alerts are on, also from the tray.
- **Logo blink on profile change:** three pulses ("tin, tin, tin", like a turn signal) in the profile's colour, then the LED goes back to how it was (on, off, colour). Uses temporary colour commands that **don't write to the mouse's memory**; if your model refuses them, the blink turns itself off. Optional, with a *Test* button (Lighting). It needs the app to know the LED's state: turn it on or off once in *Lighting* (the mouse can't tell us its current colour).
- **Sniper button:** assign **Sniper** to any button that reports release (wheel click, side buttons, and the buttons the mouse reports) and the DPI drops to your *Sniper DPI* (default 400) **while you hold it**; when you release, it goes back to the active profile. Changing profile while holding it is handled.
- **Tray menu:** status line (profile, DPI, battery), **Profiles** submenu to switch profile from the clock area, Show, Quit. The tooltip and the menu update on their own.
- **Theme selector** in Settings (just *Basic* for now) and a **dark / light switch** (dark by default; the light theme is coming).
- **Welcome dialog** on first run and a **"What's new"** dialog after an update (also reachable from *About*).
- **Profile-writing window:** it is wider, and the per-profile "saved" confirmations now overlap in a single fixed line instead of stacking, so the *Write this profile* button can no longer be pushed out of view.
- Model list shows *Auto-detect* in the interface language.
- Under the hood: commands to the mouse are now thread-safe (a lock around every send+read), the button listener reports **release** events, and `set_color`/`set_light_off` accept `store=False`.
- Not included on purpose: per-profile polling rate (changing it without noticing is a trap on high-refresh screens) and community translations.

#### Español
**Más grande, redimensionable, con avisos de batería, parpadeo de perfil y botón sniper.**
- **Interruptor de idioma (ES | EN) en la barra lateral**, justo encima de *Registro*. **El inglés es ahora el idioma por defecto** (se restablece una sola vez al actualizar, aunque una versión anterior hubiera guardado español; después se recuerda siempre tu elección). Ya no está en Ajustes.
- **Ventana redimensionable:** se abre todo lo alta que permita el área útil de tu pantalla (casi ninguna página necesita barra de scroll; solo *Ajustes*, que es larga, puede hacerla), la puedes ampliar y reducir (las tarjetas recolocan sus textos), nunca se va a la bandeja durante el arranque y **recuerda tamaño y posición**.
- **Silueta del ratón renderizada de nuevo:** líneas más gruesas y bordes suaves con antialiasing (adiós a los «dientes de sierra»). **Icono nuevo** hecho con ella.
- **Avisos de batería:** un popup aparte **arriba a la derecha de la pantalla** al **90, 80, 70, 60, 50, 40, 30, 20, 15, 10, 8, 6, 5, 4, 3, 2 y 1 %**, otro **cada vez que abres el programa** con el nivel actual, y otro al **cargar del todo**. Si la lectura oscila ±1 % no repite el aviso. Ámbar por debajo del 20 %, rojo por debajo del 10 %. Se puede desactivar, con botón *Probar* (Ajustes › Batería). Con los avisos activos la batería se lee en segundo plano (una vez por minuto), también desde la bandeja.
- **Parpadeo del logo al cambiar de perfil:** tres pulsos («tin, tin, tin», como un intermitente) con el color del perfil, y el LED vuelve a como estaba (encendido, apagado, color). Usa comandos de color temporal que **no escriben en la memoria del ratón**; si tu modelo los rechaza, el parpadeo se desactiva solo. Opcional, con botón *Probar* (Iluminación). Necesita que el programa sepa cómo está el LED: enciéndelo o apágalo una vez en *Iluminación* (el ratón no nos dice su color actual).
- **Botón sniper:** asigna **Sniper** a cualquier botón que avise al soltar (pulsar rueda, laterales y los botones que avisa el ratón) y el DPI baja a tu *DPI del sniper* (400 por defecto) **mientras lo mantienes**; al soltar, vuelve al perfil activo. Si cambias de perfil con él pulsado, se gestiona bien.
- **Menú de la bandeja:** línea de estado (perfil, DPI, batería), submenú **Perfiles** para cambiar de perfil desde el reloj, Mostrar y Salir. El texto y el menú se actualizan solos.
- **Selector de tema** en Ajustes (de momento solo *Básico*) e **interruptor claro / oscuro** (oscuro por defecto; el claro llegará).
- **Bienvenida** la primera vez y **«Novedades»** tras actualizar (también desde *Acerca de*).
- **Ventana de grabar perfiles:** más ancha, y las confirmaciones de «perfil guardado» se superponen en una sola línea fija en vez de apilarse, así el botón *Grabar este perfil* ya no se puede salir de la vista.
- La lista de modelos muestra *Auto-detectar* en el idioma de la interfaz.
- Por dentro: los comandos al ratón ahora son seguros entre hilos (un cerrojo alrededor de cada envío+lectura), el escucha de botones avisa también al **soltar**, y `set_color`/`set_light_off` aceptan `store=False`.
- Fuera a propósito: frecuencia de sondeo por perfil (cambiarla sin darte cuenta es una trampa con pantallas de muchos Hz) y traducciones de la comunidad.

---

### v1.2.0

#### English
**New interface in the style of Windows 11 Settings (dark mode).**
- **Sidebar** instead of tabs: the mouse and its status at the top (silhouette in green when connected, grey while searching), then **Profiles · Lighting · Buttons · Settings**, and **Log · About** at the bottom.
- Content as **Windows-style row cards** (title and description on the left, control on the right) with **toggle switches** instead of checkboxes.
- Single **Razer green** accent; flat colours, no gradients or glows. Profile colours are now **neon**.
- **Changes apply instantly** — no more "Apply" buttons: polling rate (when you pick it), colour (quick palette or `#RRGGBB` + Enter), brightness (when you release the slider) and logo LED on/off (switch).
- **Profiles page:** "Active profile" card with the DPI in big type; each profile row has its colour dot, a DPI box and a **Use** button (or "In use").
- **New profile-change notification:** grey card with a flat circle in the profile's colour, a **5-segment bar** (as many filled as the profile number) and the **battery level** in the top right corner.
- **System tray tooltip:** hover the tray icon to see the active profile, its DPI and the battery level.
- **"Write to mouse" wizard** redesigned as a Windows 11 dialog, with a progress bar and the list of written profiles.
- **Log** moves to its own section, with **Copy** and **Report a bug**. **About** becomes a section (it replaces the "?" button) and keeps the "why it exists" text. **Language** moves to Settings.
- **Battery** shown discreetly in the sidebar (click to refresh); low battery turns the icon red.
- New mouse silhouette in the sidebar, notification and About.
- **Crisp on high-DPI screens** (125 % / 150 %) instead of blurry, and a **dark title bar**.
- Renamed buttons: "Left side, forward/back", "Right side, upper/lower".
- No mouse logic changed: profiles, control/compatibility modes, remapping, updates, tray and autostart work exactly as in v1.1.0.

#### Español
**Interfaz nueva al estilo de Configuración de Windows 11 (modo oscuro).**
- **Barra lateral** en lugar de pestañas: arriba, el ratón y su estado (silueta en verde si está conectado, gris mientras lo busca); debajo, **Perfiles · Iluminación · Botones · Ajustes**, y abajo del todo **Registro · Acerca de**.
- Contenido en **tarjetas-fila como las de Windows** (título y descripción a la izquierda, control a la derecha) e **interruptores** en lugar de casillas.
- Un único acento **verde Razer**; colores planos, sin degradados ni brillos. Los colores de los perfiles pasan a ser **neón**.
- **Los cambios se aplican al momento**, adiós a los botones «Aplicar»: frecuencia de sondeo (al elegirla), color (paleta rápida o `#RRGGBB` + Intro), brillo (al soltar el deslizador) y LED del logo (interruptor).
- **Página Perfiles:** tarjeta «Perfil activo» con el DPI en grande; cada perfil con su punto de color, su caja de DPI y un botón **Usar** (o «En uso»).
- **Aviso nuevo de cambio de perfil:** tarjeta gris con un círculo plano del color del perfil, una **barra de 5 tramos** (se llenan tantos como el número de perfil) y el **nivel de batería** arriba a la derecha.
- **Texto en el icono de la bandeja:** al pasar el ratón por encima se ve el perfil activo, su DPI y la batería.
- **Asistente «Grabar en el ratón»** rediseñado como diálogo de Windows 11, con barra de progreso y lista de perfiles grabados.
- El **Registro** pasa a su propia sección, con **Copiar** y **Reportar un error**. **Acerca de** es ahora una sección (sustituye al botón «?») y conserva el texto de «por qué existe». El **idioma** pasa a Ajustes.
- La **batería** se muestra discreta en la barra lateral (clic para actualizar); con batería baja, el icono se pone rojo.
- Silueta nueva del ratón en la barra lateral, el aviso y Acerca de.
- **Nítido en pantallas con escalado** (125 % / 150 %) en vez de borroso, y **barra de título oscura**.
- Botones renombrados: «Lateral izquierdo, adelante/atrás», «Lateral derecho, arriba/abajo».
- No se ha tocado la lógica del ratón: perfiles, modos control/compatibilidad, remapeo, actualizaciones, bandeja y arranque con Windows funcionan igual que en la v1.1.0.

---

### v1.1.0

#### English
- **Control mode, like Synapse:** while the app is open it takes over the mouse's profile button and switches between your 5 DPI profiles instantly and exactly. The mouse's onboard profiles are never touched; closing the app returns the mouse to normal mode.
- **Write to mouse** wizard (colour by colour: red, green, blue, turquoise, yellow) and an offer to do it **on exit**.
- **Compatibility mode** fallback that detects the profile by DPI and never overwrites your profiles.
- **Software button remapping** (Windows): wheel click, wheel up/down and side buttons to any action or key combination. Off by default; not saved to the mouse; some anti-cheats may detect it.
- **Automatic connection/reconnection**, battery refreshes by itself.
- **Settings:** system tray, start with Windows, update check with one-click install, bug report.
- Log and errors follow the selected language; settings in `%APPDATA%\Non-Synapse-Mouse`; only one copy runs at a time.

#### Español
- **Modo control, como Synapse:** con el programa abierto, el botón de perfil del ratón lo gestiona el programa, que cambia entre tus 5 perfiles de DPI al instante y sin fallos. Los perfiles internos del ratón no se tocan; al cerrar, el ratón vuelve a su modo normal.
- Asistente **Grabar en el ratón** (color a color: rojo, verde, azul, turquesa, amarillo) y oferta de hacerlo **al cerrar**.
- **Modo compatibilidad** de respaldo: detecta el perfil por el DPI y nunca sobrescribe tus perfiles.
- **Remapeo de botones por software** (Windows): pulsar rueda, rueda arriba/abajo y laterales a cualquier acción o combinación de teclas. Desactivado por defecto; no se guarda en el ratón; algunos anticheats pueden detectarlo.
- **Conexión y reconexión automáticas**; la batería se refresca sola.
- **Opciones:** bandeja del sistema, arrancar con Windows, buscar e instalar actualizaciones con un clic, reportar errores.
- El registro y los errores siguen el idioma elegido; configuración en `%APPDATA%\Non-Synapse-Mouse`; solo se abre una copia a la vez.

</details>
