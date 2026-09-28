> 🌐 **[English](README.md)** · **[Español](README.es.md)**

# Non-Synapse-Mouse

**Configurador ligero para ratones Razer, sin Razer Synapse.**

Razer Synapse/Chroma ocupa espacio, corre servicios en segundo plano, consume
RAM y necesita cuenta y conexión — todo para tareas tan simples como cambiar el
DPI. **Non-Synapse-Mouse** hace ese trabajo hablando directamente con el ratón
por USB (los mismos *feature reports* HID que manda Synapse), **sin servicios de
fondo, sin nube y sin instalar drivers**. Funciona en Windows.

> ⚠️ Proyecto independiente de la comunidad. **No está afiliado a Razer ni
> respaldado por Razer.** Software libre (**GPL-3.0**), se ofrece *tal cual*,
> **sin garantías** (ver [Licencia](#licencia)).

---

## Índice
- [De dónde viene y por qué](#de-dónde-viene-y-por-qué)
- [Características](#características)
- [Qué NO hace (limitaciones)](#qué-no-hace-limitaciones)
- [Modelos compatibles](#modelos-compatibles)
- [Requisitos](#requisitos)
- [Uso rápido](#uso-rápido)
- [Compilar a .exe](#compilar-a-exe-windows)
- [Cómo funciona por dentro](#cómo-funciona-por-dentro)
- [Perfiles: cómo funciona](#perfiles-cómo-funciona)
- [Archivo de configuración](#archivo-de-configuración)
- [Solución de problemas](#solución-de-problemas)
- [Seguridad y aviso legal](#seguridad-y-aviso-legal)
- [Créditos](#créditos)
- [Historial de versiones](#historial-de-versiones)
- [Licencia](#licencia)

---

## De dónde viene y por qué

Synapse/Chroma me parecía un despropósito: RAM y procesos en segundo plano,
cuenta y conexión, para algo tan simple como fijar un DPI o un color. La idea era
poder configurar el ratón **una vez** y quitarme el software de encima.

Esto es posible gracias al proyecto **[OpenRazer](https://github.com/openrazer/openrazer)**
(licencia **GPL-2.0**), que lleva años descifrando por ingeniería inversa el
protocolo de los dispositivos Razer. De su código se tomaron y **verificaron** los
comandos (DPI, polling, batería, iluminación) y las estructuras del protocolo.
Este programa **no copia código de OpenRazer**: reimplementa el protocolo en
Python, pero el mérito de la ingeniería inversa es de OpenRazer y su comunidad.
**Gracias.**

Por sintonía con ese ecosistema y para que el proyecto **siga siendo libre**
(que nadie lo cierre y lo venda sin compartir), se publica bajo **GPL-3.0**.

## Características

- 🖱️ **DPI**: leer y aplicar. Se graba en la **memoria interna** del ratón, así
  que **persiste** aunque cierres el programa (o de forma temporal, si prefieres).
  Deslizador + campo numérico, con el máximo ajustado a cada modelo.
- ⚡ **Tasa de sondeo** (polling): 125 / 500 / 1000 Hz.
- 🔋 **Batería**: indicador **siempre visible** en la cabecera, con nivel, estado
  de carga y **color según el nivel** (verde/ámbar/rojo). Se pulsa para
  actualizar. Solo en ratones inalámbricos.
- 💡 **Iluminación** (LED del logo): **color** (paleta rápida + hex `#RRGGBB`),
  **intensidad** y **encender/apagar** con un solo botón.
- 🤖 **Totalmente automático**: se conecta solo al ratón al abrirlo, se reconecta si
  lo desenchufas o se duerme, y refresca la batería por su cuenta.
- 🎯 **Perfiles, como Synapse**: mientras el programa está abierto **toma el control
  del botón de perfil** del ratón y cambia entre **tus 5 perfiles de DPI** al instante
  y sin fallos. Se aplican al abrir el programa; los perfiles internos del ratón nunca
  se tocan y vuelven al cerrarlo. **Aviso emergente (toast)** opcional al cambiar.
- 🌐 **Bilingüe** español / inglés con selector, cambio en caliente.
- 🎨 **Interfaz** de escritorio limpia, tema oscuro plano, **tamaño fijo**.
- 🔎 **Selector de modelo** (~20 modelos Razer) + **autodetección** de cualquier
  Razer y del `transaction_id` correcto por comando.
- 💾 **Configuración persistente** (presets, color, brillo, idioma, último
  modelo, casillas) en `%APPDATA%\Non-Synapse-Mouse\razer_presets.json`, así que
  sobreviven a mover, recompilar o actualizar el `.exe`. El seguimiento de perfiles
  también se recuerda.
- 🗂️ **Pestaña Opciones** (v1.1.0):
  - **Minimizar a la bandeja del sistema** (junto al reloj), con menú *Mostrar* / *Salir*.
  - **Arrancar con Windows** (minimizado en la bandeja y se conecta solo al ratón).
  - **Buscar actualizaciones** en GitHub (al iniciar y a demanda) y **descargar e
    instalar** el `.exe` nuevo con un clic (tu configuración se conserva).
  - **Reportar un error**: abre un *issue* en GitHub con versión, sistema, modelo,
    firmware y las últimas líneas del registro ya rellenos (no se envía nada hasta
    que tú lo publiques).
- 🗒️ El **registro y los mensajes de error siguen el idioma elegido** (v1.1.0).
- 🖥️ **Modo consola** de respaldo (`--cli`).
- ✅ **Protocolo verificado** contra [OpenRazer](https://github.com/openrazer/openrazer).

## Qué NO hace (limitaciones)

Transparencia total, para que nadie se lleve sorpresas:

- ⚠️ **El remapeo de botones es solo por software (de momento).** Funciona con el
  programa abierto y **no se guarda en la memoria del ratón** (el comando de mapeo de
  Razer aún no está descifrado). El clic izquierdo y el derecho no se remapean nunca,
  no hay macros, y algunos anticheats pueden detectar el gancho de Windows que usa.
- ❌ **No cambia de perfil por software.** Razer no expone el comando para
  seleccionar/leer el perfil activo. El cambio se hace con el **botón físico**
  del ratón; el programa solo **deduce** en cuál estás (por el DPI).
- ❌ **Solo color estático + brillo.** No hay efectos *breathing*, *spectrum*,
  *wave*, etc., ni iluminación por zonas/teclas (una sola zona: el logo).
- ❌ **No** gestiona *lift-off distance*, *angle snapping*, *debounce*,
  *motion sync* ni la configuración de los 5 escalones de DPI.
- ❌ **Solo ratones Razer.** Otras marcas (p. ej. Pulsar) usan otro protocolo.
- ⚠️ **Probado a fondo solo con la Razer Viper Ultimate** (modelo de referencia).
  El resto se apoya en ingeniería inversa + autodetección; deberían funcionar,
  pero no están verificados uno a uno contra hardware real.
- ⚠️ Si dos perfiles tienen **el mismo DPI**, el seguimiento no puede detectar
  ese salto concreto.
- ⚠️ Los **juegos en pantalla completa exclusiva** pueden no mostrar el aviso
  emergente (usa modo ventana/borderless).

## Modelos compatibles

Seleccionables en el menú (además de **"Auto-detectar cualquier Razer"**):

Viper Ultimate · Viper · Viper Mini · Viper 8KHz · Viper V2 Pro · Viper Mini SE ·
DeathAdder V2 · DeathAdder V2 Pro · DeathAdder V2 Mini · DeathAdder Elite ·
DeathAdder V3 Pro · Basilisk V2 · Basilisk V3 · Basilisk Ultimate ·
Basilisk X HyperSpeed · Naga Pro · Naga X · Cobra · Mamba Elite · Orochi V2.

> ¿Tu modelo no está o falla? Usa **"Auto-detectar"**: el programa prueba las
> interfaces y sondea el `transaction_id` hasta dar con el que responde.

## Requisitos

**Como ejecutable (.exe):** nada. Doble clic.

**Como script (.py):**
- Python 3.8 o superior.
- El paquete **`hidapi`**:
  ```
  py -m pip install hidapi
  ```
  ⚠️ Instala `hidapi`, **no** `hid` a secas (son paquetes distintos).
- Opcional, para la bandeja del sistema: `py -m pip install pystray pillow` (sin
  ellos funciona todo; solo se desactiva la opción de la bandeja).

## Uso rápido

1. **Cierra Razer Synapse por completo** (incluidos sus servicios en el
   Administrador de tareas) o desinstálalo. Mientras Synapse tenga tomado el
   ratón, puede bloquear las respuestas.
2. Ejecuta el programa:
   ```
   py Non_Synapse_Mouse.py
   ```
   (o el `.exe`, o `py Non_Synapse_Mouse.py --cli` para consola).
3. Se **conecta solo**. La cabecera muestra *Conectado · (tu modelo)* y la batería.
4. Pulsa el **botón de perfil** del ratón hasta dar la vuelta a todos tus perfiles.
   Listo: a partir de ahí los sigue solo.

## Compilar a .exe (Windows)

No necesitas instalador: un único `.exe` autocontenido es suficiente.

**Opción fácil:** doble clic en `build_exe.bat` (incluido).

**Manual:**
```
py -m pip install pyinstaller hidapi pystray pillow
py -m PyInstaller --onefile --windowed --clean --hidden-import pystray._win32 --icon=icono.ico --add-data "icono.ico;." --name Non-Synapse-Mouse_v1.1.0 Non_Synapse_Mouse.py
```
El ejecutable aparece en `dist\Non-Synapse-Mouse_v1.1.0.exe`. Cópialo y compártelo
tal cual (pon `icono.ico` junto al script antes de compilar; `build_exe.bat` lo
hace todo solo).

> **Nota sobre avisos de Windows/antivirus:** un `.exe` de PyInstaller sin firma
> digital puede disparar el aviso de SmartScreen ("Windows protegió tu PC" →
> *Más información* → *Ejecutar de todas formas*) y, a veces, falsos positivos de
> algún antivirus. Es habitual en ejecutables no firmados. Alternativas: compartir
> el código fuente (es abierto, se puede leer) o compilar con `--onedir`.

## Cómo funciona por dentro

El programa envía **informes HID de 90 bytes** al ratón (el mismo mecanismo de
Synapse): estado, `transaction_id`, tamaño, clase de comando, id de comando,
argumentos y un **CRC** (XOR de los bytes 2..87). Los comandos y parámetros están
tomados y verificados contra el código de **OpenRazer**.

Detalles que lo hacen robusto:
- **Autodetección de interfaz:** prueba las interfaces HID y se queda con la que
  responde.
- **Autodetección del `transaction_id` por clase de comando:** distintos modelos
  (e incluso distintos comandos del mismo modelo) usan valores distintos; se
  sondean con comandos de lectura y se cachean.
- **Sin reemplazar drivers:** usa la pila HID del sistema (como Synapse); no hace
  falta Zadig ni WinUSB.

## Perfiles: cómo funciona

**Modo control (por defecto, como Synapse).** Mientras el programa está abierto,
pone el ratón en su *modo driver*: el ratón deja de cambiar sus perfiles internos y
**avisa al programa cada vez que pulsas el botón de perfil** (o los de DPI). El
programa aplica entonces el siguiente de **tus 5 perfiles**, al instante y sin fallos:
nada de adivinar.

- Tus perfiles viven en el programa (edita las casillas de DPI y pulsa *Guardar
  perfiles*; deja una vacía para desactivar ese perfil). Clic en el nombre de un
  perfil para activarlo.
- Se aplican nada más abrir el programa y se recuerdan entre sesiones.
- El botón de perfil pasa al siguiente; *DPI abajo* vuelve al anterior.
- **Los perfiles internos del ratón nunca se tocan**: el DPI se aplica sin escribir
  en su memoria. Al cerrar el programa, el ratón vuelve a su modo normal y sus
  perfiles propios funcionan otra vez. (Si el programa se cerrase de golpe,
  desenchufar y enchufar el ratón lo arregla.)
- Si el ratón se reinicia o se despierta, el programa retoma el control solo.
- *Restablecer perfiles* vuelve a los valores por defecto (400 / 800 / 1600 / 3200 / 6400).
- Como con Synapse, el LED de perfil del ratón no cambia de color en este modo (lo
  controla el firmware). A cambio, cada perfil muestra su circulito de color en el
  programa y el aviso emergente sale de ese color.
- **Pestaña Mapeo (remapeo por software, Windows):** remapea pulsar rueda, rueda arriba/abajo y
  los laterales izquierdos a *cualquier* acción: perfil anterior /
  siguiente / concreto, clics, doble clic, copiar/pegar/deshacer, Alt+Tab, mostrar
  escritorio, captura de pantalla, multimedia y volumen, o **cualquier combinación de
  teclas** (p. ej. `ctrl+shift+s`, `alt+f4`, `f13`). Las teclas se mantienen mientras
  mantienes el botón. Está **desactivado por defecto**, funciona con el programa abierto
  (también minimizado o en la bandeja) y **aún no se guarda en la memoria del ratón**.
  Desactívalo al jugar con anticheat. El clic izquierdo y el derecho no se tocan nunca.
  Si tus laterales de ambos lados mandan la misma señal a Windows, se remapean juntos. En la Viper (ambidiestra), los **laterales derechos** los comunica el propio
  ratón en modo control y aparecen en el grupo de abajo, con las mismas acciones.
  Bajo la línea aparecen solos los botones especiales que el ratón comunica en modo
  control (perfil/DPI y los que comunique), con las mismas acciones.
- **Al cerrar**, el programa pregunta si grabar tus perfiles en la memoria del ratón
  (solo si han cambiado desde la última vez; se puede desactivar en Opciones).
- **Grabar en el ratón:** un asistente guiado guarda tus perfiles en la **memoria del
  propio ratón**, para que los conserve —con sus colores de LED (1 rojo · 2 verde ·
  3 azul · 4 turquesa · 5 amarillo en la Viper Ultimate)— con el programa cerrado o
  en otro PC. Te pide poner el LED en cada color con el botón de perfil, graba el DPI
  de ese perfil y lo comprueba leyéndolo. *Guardar perfiles* por sí solo los guarda
  únicamente en el programa.

**Modo compatibilidad (respaldo automático).** Si Windows no deja al programa
escuchar el botón del ratón, o si la primera vez no llega ninguna pulsación en 25 s,
devuelve el ratón a su modo normal y **deduce el perfil activo por el DPI**. En este
modo **nunca sobrescribe tus perfiles por su cuenta**: si un DPI no cuadra, solo lo
indica. Puedes activar/desactivar el modo control en *Opciones › Ratón*.

## Archivo de configuración

`%APPDATA%\Non-Synapse-Mouse\razer_presets.json` (pega `%APPDATA%` en la barra de
direcciones del Explorador para llegar). Contiene: presets de DPI, color e
intensidad del LED, idioma, último modelo, si el seguimiento de perfiles está
activo y el estado de las casillas. Puedes borrarlo para volver a los valores por
defecto. Si tenías un `razer_presets.json` junto al `.exe` (v1.0.0), se migra solo.

Solo se ejecuta **una copia** del programa a la vez: si ya está abierto (por
ejemplo en la bandeja), al abrirlo otra vez te avisa de dónde está, para que nunca
haya dos copias hablando con el ratón a la vez.

## Solución de problemas

- **"Falta el paquete 'hidapi'":** `py -m pip install hidapi` (no `hid`).
- **"Ninguna interfaz respondió":** cierra Synapse **del todo** (servicios
  incluidos) o desinstálalo, y reintenta.
- **Los perfiles están mezclados:** *Restablecer perfiles* en la pestaña Perfiles.
- **La batería sale "no disponible":** tu modelo es por cable / no reporta batería.
- **El aviso emergente no aparece en un juego:** ponlo en ventana/borderless.
- **Modelo raro o no listado:** elige **"Auto-detectar"** en *Opciones › Ratón*.

## Seguridad y aviso legal

- El programa **solo** envía comandos de configuración estándar al ratón. No toca
  el sistema y no instala nada.
- **Uso de red:** la única conexión es la **comprobación de actualizaciones** (una
  consulta de lectura a `api.github.com`, desactivable en Opciones) y, si la
  aceptas, la descarga de la versión nueva desde GitHub. Los enlaces que pulses
  (Ko-fi, reportar error) se abren en tu navegador. Sin telemetría ni cuentas.
- **Arrancar con Windows** escribe un único valor en
  `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (solo tu usuario, sin
  permisos de administrador); al desmarcar la opción se borra.
- Es **software libre y de código abierto**: puedes revisar exactamente qué hace.
- Se ofrece **SIN GARANTÍA de ningún tipo**. Aunque el protocolo está verificado
  contra OpenRazer, cada equipo es un mundo: **úsalo bajo tu responsabilidad**.
- **No afiliado a Razer.** "Razer", "Synapse" y "Chroma" son marcas de Razer Inc.

## Créditos

- **[OpenRazer](https://github.com/openrazer/openrazer)** (**GPL-2.0**) — la
  ingeniería inversa del protocolo Razer en la que se basa este programa. Sin su
  trabajo, esto no existiría.
- **[hidapi](https://github.com/trezor/cython-hidapi)** — acceso HID
  multiplataforma.

## Historial de versiones

Resumen de hitos (la **v1.0.0** fue la primera versión pública):

| Hito | Qué se añadió |
|------|----------------|
| Base | Comunicación HID con la Viper Ultimate: DPI, polling, batería, guardado onboard. |
| Multimodelo | Selector de ~20 modelos + autodetección del `transaction_id`; 5 presets de DPI. |
| Perfiles | Detección del perfil activo por DPI (resaltado). |
| Sondeo | Sondeo automático solo con la ventana visible (con casilla). |
| Seguimiento | Ancla guiada + seguimiento del ciclo de perfiles + auto-corrección al recuperar el foco. |
| Aviso | Aviso emergente (toast) al cambiar de perfil + sondeo en segundo plano opcional. |
| Iluminación | Pestaña de LED: color, intensidad y encendido/apagado. |
| Interfaz | Pestañas, tema oscuro plano y tamaño fijo autoajustado. |
| Marca | Renombrado a *Non-Synapse-Mouse*, botón "Acerca de" y enlace de donación. |
| Idiomas | Interfaz bilingüe ES/EN con selector y documentación a fondo del código. |
| Batería | Indicador de batería siempre visible, con color por nivel y actualización al pulsar. |
| **v1.0.0** | Distribución: rutas arregladas para `.exe`, licencia GPL-3.0, documentación. |
| **v1.1.0** | Registro y errores en el idioma elegido; pestaña Opciones: bandeja del sistema, arranque con Windows, buscar e instalar actualizaciones, botón de reportar errores; icono de ventana; **modo automático**: conexión/reconexión sola, **modo control como Synapse** (el programa gestiona el botón de perfil), modo compatibilidad de respaldo que nunca sobrescribe perfiles. |

### Ideas / pendientes (roadmap)
- Remapeo de botones nativo (requiere capturas de Wireshark de Synapse).
- Soporte para otras marcas (p. ej. Pulsar, ya descifrado por la comunidad).
- Más efectos de iluminación (breathing, spectrum…).

## Licencia

**[GPL-3.0](LICENSE)** — software libre con *copyleft*: puedes usarlo, estudiarlo,
modificarlo y redistribuirlo, pero cualquier versión que distribuyas debe seguir
siendo libre y con esta misma licencia. Consulta el archivo `LICENSE` para el
texto completo. **Sin garantía.**

Aviso de marcas: proyecto no afiliado a Razer Inc. "Razer", "Synapse" y "Chroma"
son marcas de sus respectivos propietarios.

---

Si te resulta útil y te apetece invitar a un scoop de proteína:
☕ **https://ko-fi.com/damneddamm**
