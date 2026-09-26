[README.md](https://github.com/user-attachments/files/32686073/README.md)
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
- [Los 5 perfiles y el seguimiento](#los-5-perfiles-y-el-seguimiento)
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
- 🎯 **Perfiles**: 5 presets de DPI (uno por perfil onboard), con **detección y
  seguimiento automático del perfil activo** y **aviso emergente (toast)** al
  cambiar de perfil.
- 🌐 **Bilingüe** español / inglés con selector, cambio en caliente.
- 🎨 **Interfaz** de escritorio limpia, tema oscuro plano, **tamaño fijo**.
- 🔎 **Selector de modelo** (~20 modelos Razer) + **autodetección** de cualquier
  Razer y del `transaction_id` correcto por comando.
- 💾 **Configuración persistente** (presets, color, brillo, idioma, último
  modelo, casillas) en un `razer_presets.json` junto al programa.
- 🖥️ **Modo consola** de respaldo (`--cli`).
- ✅ **Protocolo verificado** contra [OpenRazer](https://github.com/openrazer/openrazer).

## Qué NO hace (limitaciones)

Transparencia total, para que nadie se lleve sorpresas:

- ❌ **No remapea botones ni graba macros.** El comando de mapeo de botones de
  los ratones Razer **no está descifrado de forma fiable**; se optó por no
  incluir algo que pudiera fallar en silencio.
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

## Uso rápido

1. **Cierra Razer Synapse por completo** (incluidos sus servicios en el
   Administrador de tareas) o desinstálalo. Mientras Synapse tenga tomado el
   ratón, puede bloquear las respuestas.
2. Ejecuta el programa:
   ```
   py Non_Synapse_Mouse.py
   ```
   (o el `.exe`, o `py Non_Synapse_Mouse.py --cli` para consola).
3. Elige tu **modelo** y pulsa **"Detectar / Probar conexión"**.
4. Si te lee firmware, DPI y batería con valores normales, **funciona**.

## Compilar a .exe (Windows)

No necesitas instalador: un único `.exe` autocontenido es suficiente.

**Opción fácil:** doble clic en `build_exe.bat` (incluido).

**Manual:**
```
py -m pip install pyinstaller hidapi
py -m PyInstaller --onefile --windowed --name Non-Synapse-Mouse Non_Synapse_Mouse.py
```
El ejecutable aparece en `dist\Non-Synapse-Mouse.exe`. Cópialo y compártelo tal
cual. El `razer_presets.json` se crea junto al `.exe` al usarlo.

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

## Los 5 perfiles y el seguimiento

El ratón guarda hasta 5 perfiles y se cambia con el **botón físico**. Razer **no
expone** el comando para leer o cambiar el perfil activo por software, así que el
programa lo **deduce por el DPI**: cada preset guarda el DPI de un perfil,
**"Empezar seguimiento"** ancla el Perfil 1, y a partir de ahí cada cambio de DPI
se **registra** en el preset que toca y se marca el perfil activo, sin que toques
nada. Al volver a primer plano se **auto-corrige** si el DPI coincide con un
perfil conocido. Opcionalmente, un **aviso emergente** te dice a qué perfil
cambiaste (ese modo sondea también en segundo plano).

## Archivo de configuración

`razer_presets.json`, junto al programa (o al `.exe`). Contiene: presets de DPI,
color e intensidad del LED, idioma, último modelo y estado de las casillas.
Puedes borrarlo para volver a los valores por defecto.

## Solución de problemas

- **"Falta el paquete 'hidapi'":** `py -m pip install hidapi` (no `hid`).
- **"Ninguna interfaz respondió":** cierra Synapse **del todo** (servicios
  incluidos) o desinstálalo, y reintenta.
- **El DPI no persiste:** deja marcada *"Guardar en memoria del ratón"*.
- **La batería sale "no disponible":** tu modelo es por cable / no reporta batería.
- **El aviso emergente no aparece en un juego:** ponlo en ventana/borderless.
- **Modelo raro o no listado:** usa **"Auto-detectar"**.

## Seguridad y aviso legal

- El programa **solo** envía comandos de configuración estándar al ratón. No toca
  el sistema, no instala nada, no se conecta a internet (salvo abrir el enlace de
  donación en tu navegador si lo pulsas tú).
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

Resumen de hitos hasta la **v1.0.0** (primera versión pública):

| Hito | Qué se añadió |
|------|----------------|
| Base | Comunicación HID con la Viper Ultimate: DPI, polling, batería, guardado onboard. |
| Multimodelo | Selector de ~20 modelos + autodetección del `transaction_id`; 5 presets de DPI. |
| Perfiles | Detección del perfil activo por DPI (resaltado). |
| Sondeo | Sondeo automático solo en primer plano (con casilla). |
| Seguimiento | Ancla guiada + seguimiento del ciclo de perfiles + auto-corrección al recuperar el foco. |
| Aviso | Aviso emergente (toast) al cambiar de perfil + sondeo en segundo plano opcional. |
| Iluminación | Pestaña de LED: color, intensidad y encendido/apagado. |
| Interfaz | Pestañas, tema oscuro plano y tamaño fijo autoajustado. |
| Marca | Renombrado a *Non-Synapse-Mouse*, botón "Acerca de" y enlace de donación. |
| Idiomas | Interfaz bilingüe ES/EN con selector y documentación a fondo del código. |
| Batería | Indicador de batería siempre visible, con color por nivel y actualización al pulsar. |
| **v1.0.0** | Distribución: rutas arregladas para `.exe`, licencia GPL-3.0, documentación. |

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
