> 🌐 **[English](README.md)** · **[Español](README.es.md)**

# Non-Synapse-Mouse

**A lightweight configuration tool for Razer mice — without Razer Synapse.**

<p align="center">
  <img src="assets/screenshot.png" width="680" alt="Non-Synapse-Mouse">
</p>

Razer Synapse takes up space, runs background services, eats RAM and asks for an
account just to change your mouse's DPI. **Non-Synapse-Mouse** does the job by
talking directly to the mouse (the same HID *feature reports* Synapse sends):
**no intrusive background services, no cloud, no account and no drivers to install.**
Works on Windows.

> ⚠️ Independent community project. **Not affiliated with or endorsed by Razer.**
> Free software (**GPL-3.0**), provided *as is*, **with no warranty**.

**[Download the latest version](https://github.com/Damnedapa/Non-Synapse-Mouse/releases/latest)** · [Changelog](CHANGELOG.md)

---

## Table of contents
- [Where it comes from](#where-it-comes-from)
- [Features](#features)
- [Limitations](#limitations)
- [Supported models](#supported-models)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Updating from v1.0.0](#updating-from-v100)
- [How profiles work](#how-profiles-work)
- [Button remapping](#button-remapping)
- [Build the .exe](#build-the-exe)
- [How it works under the hood](#how-it-works-under-the-hood)
- [Settings file](#settings-file)
- [Troubleshooting](#troubleshooting)
- [Security, privacy and legal](#security-privacy-and-legal)
- [Credits](#credits)
- [License](#license)

---

## Where it comes from

Synapse always felt absurd: RAM and background processes, an account and a
connection, for something as simple as setting a DPI or a colour. The idea was to
configure the mouse and get the software off my back.

It's possible thanks to **[OpenRazer](https://github.com/openrazer/openrazer)**
(**GPL-2.0**), which has spent years reverse-engineering Razer devices, but only for
Linux. The commands and protocol structures were taken and **verified** against its
code. This program **does not copy OpenRazer's code**: the protocol is reimplemented
in Python. The credit for the reverse engineering belongs to OpenRazer and its
community. **Thank you.**

To keep the project **free** (so nobody can close it and sell it), it's released
under **GPL-3.0**.

## Features

**Profiles, like Synapse**
- While the app is open it **takes over the mouse's profile button** and switches
  between **your 5 DPI profiles instantly and exactly**. *DPI down* goes back.
- Edit the DPI of each profile in the app; click **Use** to activate one. They're
  applied as soon as the app opens.
- The mouse's own onboard profiles are **never touched** unless you choose to write
  them; closing the app returns the mouse to normal mode.
- **Write to mouse:** a guided wizard stores your profiles in the mouse's own memory,
  colour by colour (red, green, blue, turquoise, yellow), checking each one. You keep
  them with the app closed or on another PC. The app also offers to do it on exit.
- Optional **notification** when the profile changes: a card with the profile's
  colour, a 5-segment bar and the battery level.
- Hover the **tray icon** to see the active profile, its DPI and the battery; right-click
  it to **switch profile** from the menu.
- **Logo blink:** when the profile changes, the logo LED blinks three times in the
  profile's colour (like a turn signal) and goes back to how it was. Optional.

**Everything else**
- **Automatic connection:** finds the mouse by itself and reconnects if it's unplugged
  or goes to sleep. Auto-detects any Razer, even if it's not in the list.
- **Polling rate** 125 / 500 / 1000 Hz, applied as soon as you pick it.
- **Lighting (logo LED):** on/off switch, colour from a quick palette or a **colour
  picker** (colour wheel + brightness bar + `#RRGGBB` code, editable both ways), and
  brightness. Everything applies instantly.
- **Battery** in the sidebar (wireless mice); click to refresh.
- **Battery alerts:** a separate pop-up at the **top right of the screen** at 90, 80, 70,
  60, 50, 40, 30, 20, 15, 10, 8, 6, 5, 4, 3, 2 and 1 %, one **every time you open the
  app** with the current level, and one when it's **fully charged**. Optional.
- **Sniper button:** assign it to any button; while you hold it the mouse drops to the
  DPI you choose (400 by default), and goes back when you let go.
- **Button remapping** by software (Windows) — see [below](#button-remapping).
- **System tray**, **start with Windows**, **update check** with one-click install,
  **bug report** with the technical details already filled in.
- Interface in the style of **Windows 11 Settings**, **dark or light mode**, crisp at
  125 % and 150 % scaling, smooth (anti-aliased) switches, dots and sliders,
  **resizable** (it remembers its size and position). **English (default) / Spanish**
  with a switch in the sidebar.
- **Themes:** a theme is a set of colours plus the **shape of the parts** (round,
  square, cut corners or diamond, with optional neon glow). Make your own as a `.json`
  file: *Settings › Appearance › Custom themes › Open folder* creates a full template
  and an example. Applied on restart (the app restarts itself).
- Options you can't use right now (e.g. standard buttons while remapping is off) are
  **greyed out**.
- The **log is always in English**, so anyone can read it in a bug report.
- **Spot me a scoop:** Ko-fi shortcut at the bottom of the sidebar, if you find it useful.
- Fallback **console mode** (`--cli`).

## Limitations

- **Button remapping is not saved to the mouse's memory yet:** it works while the app
  is open (also minimized or in the tray). Only the DPI profiles can be written to the
  mouse (Razer's button-mapping command isn't reverse-engineered yet).
- Remapping uses a Windows hook: **some anti-cheat systems may detect it**. It ships
  disabled; turn it off when playing games with anti-cheat.
- Left and right click are never remapped (on purpose), and there are no macros.
- While the app runs your profiles, the **profile LED under the mouse stays fixed**
  (same as with Synapse; it's firmware-controlled). Each profile shows its colour in
  the app instead.
- **Logo blink** needs the app to know your LED's state (turn it on or off once in
  *Lighting*), because the mouse can't be asked its current colour. It uses temporary
  colour commands that don't write to the mouse's memory; if your model refuses them,
  the blink turns itself off.
- **Sniper** works on buttons that report release: wheel click, side buttons and the
  buttons the mouse reports (control mode). Not on the wheel itself.
- **Battery alerts** need the app running (it can be in the tray); it reads the battery
  once a minute.
- Lighting: static colour + brightness only (no breathing, wave, spectrum…).
- Themes change colours and the shape of switches, dots, sliders and selectors; the
  regular buttons and drop-downs stay rectangular. A theme's font is used only if it's
  installed in Windows. Changing theme or light/dark needs a restart (one click).
- **Razer mice only.** Thoroughly tested on the **Viper Ultimate**; other models rely
  on reverse engineering + auto-detection, so feedback is welcome.
- Exclusive-fullscreen games may hide the profile notification (use borderless).
- Icons use *Segoe Fluent Icons* (Windows 11) or *Segoe MDL2 Assets* (Windows 10).

## Supported models

Selectable in *Settings › Mouse* (plus **Auto-detect**, which works for any Razer):
Viper Ultimate · Viper · Viper Mini · Viper 8KHz · Viper V2 Pro · Viper Mini SE ·
DeathAdder V2 · DeathAdder V2 Pro · DeathAdder V2 Mini · DeathAdder Elite ·
DeathAdder V3 Pro · Basilisk V2 · Basilisk V3 · Basilisk Ultimate ·
Basilisk X HyperSpeed · Naga Pro · Naga X · Cobra · Mamba Elite · Orochi V2.

## Requirements

- **As an executable (.exe):** nothing. Double-click.
- **As a script:** Python 3.8+ and `py -m pip install hidapi`
  (⚠️ `hidapi`, **not** plain `hid`). Optional, for the system tray:
  `py -m pip install pystray pillow`.

## Quick start

1. **Close Razer Synapse completely** (services included) or uninstall it.
2. Open the app. It **connects by itself**: the sidebar shows your mouse and battery.
3. Switch profiles with the mouse's **profile button**. Edit their DPI in *Profiles*
   and press **Save profiles**.
4. Optional: **Write to mouse…** to keep them in the mouse when the app is closed.

## Updating from v1.0.0

v1.4.0 is the first public release since v1.0.0 (1.1–1.3 were internal development
versions), so it's a big jump. v1.0.0 has no built-in updater: **download the new
`.exe` by hand** from [Releases](https://github.com/Damnedapa/Non-Synapse-Mouse/releases/latest).

- If you put the new `.exe` **in the same folder** as the old one, your DPI presets,
  model and LED colour are carried over automatically (settings now live in
  `%APPDATA%\Non-Synapse-Mouse`). You can then delete the old `.exe`.
- The interface starts in **English**; switch to Spanish with **ES | EN** at the
  bottom of the sidebar (it's remembered).
- No more "Detect" button: it connects by itself. And no more "start tracking": in
  control mode the app *knows* which profile is active.
- From now on, updates are one click: *Settings › Updates*.

## How profiles work

**Control mode (default).** The app puts the mouse in its *driver mode*: the mouse
stops switching its own profiles and **tells the app every time you press the profile
button** (or the DPI buttons). The app applies the next of your profiles — no
guessing. DPI is applied without writing to the mouse's memory. If the mouse sleeps
or resets, the app takes control again on its own.

**Compatibility mode (automatic fallback).** If Windows doesn't let the app listen to
the button, it returns the mouse to normal mode and **infers the active profile from
the DPI**, **without ever overwriting your profiles**. You can switch modes in
*Settings › The app controls the profiles*.

Leave a profile's DPI box empty to disable it (the profile button skips it).
*Reset values* restores 400 / 800 / 1600 / 3200 / 6400.

## Button remapping

In **Buttons**, turn on **Software remapping** and pick an action for each button:
switch profile (next, previous, a specific one), clicks, double click, copy / paste /
undo, Alt+Tab, show desktop, screenshot, media and volume keys, or **any key
combination** (`ctrl+shift+s`, `alt+f4`, `f13`…). Keys are held while you hold the
button. There's also **Sniper** (DPI while held), see [Features](#features).

- **Standard buttons:** wheel click, wheel up / down and the left side buttons.
- **Special buttons** (handled by the mouse itself; they need control mode): profile button, DPI buttons and,
  on the Viper, the **right side buttons**.

## Build the .exe

No installer needed: one self-contained `.exe`.

**Easy way:** put `Non_Synapse_Mouse.py`, `build_exe.bat` and `icono.ico` in the same
folder and double-click `build_exe.bat`. The result is
`dist\Non-Synapse-Mouse_v1.4.0.exe` (change `set VERSION=` at the top for each
release).

**Manual:**
```
py -m pip install pyinstaller hidapi pystray pillow
py -m PyInstaller --onefile --windowed --clean --hidden-import pystray._win32 --icon=icono.ico --add-data "icono.ico;." --name Non-Synapse-Mouse_v1.4.0 Non_Synapse_Mouse.py
```

> An unsigned `.exe` may trigger SmartScreen ("Windows protected your PC" → *More
> info* → *Run anyway*) and, sometimes, antivirus false positives. This is common for
> unsigned executables; the source code is open.

## How it works under the hood

The app sends **90-byte HID reports** to the mouse, like Synapse: status,
`transaction_id`, size, command class, command id, arguments and a CRC (XOR of bytes
2..87). It auto-detects the right HID interface and the `transaction_id` per command
class. Control mode uses the mouse's *driver mode* (`0x03`) and listens to its
"Report 4" button events. No driver replacement: it uses Windows' own HID stack.

Only answers that **echo the command that was sent** and come back with status *OK*
are trusted: a wireless receiver can return the previous answer, or zeros while the
mouse wakes up, and that used to show things like a fake 0 % battery. Periodic reads
(mode check, battery, reconnection) and DPI changes run in their own threads, so the
window never waits for the mouse.

## Settings file

`%APPDATA%\Non-Synapse-Mouse\razer_presets.json` (paste `%APPDATA%` in the Explorer
address bar). It holds your profiles, LED colour and brightness, button mapping,
language, theme, window size and position, last model, last page and the state of every switch.
It's saved safely (written to a temporary file first) with a backup copy
`razer_presets.json.bak`; if the file gets damaged, the app uses the backup, and any
value it doesn't understand falls back to its default. Delete it to reset everything.
Custom themes go in the `themes` folder next to it. Only **one copy** of the app runs
at a time.

## Troubleshooting

- **"Looking for the mouse…" forever:** close Synapse completely (services
  included) or uninstall it; try *Settings › Mouse › Reconnect*.
- **The profile button doesn't change anything:** check that *The app controls the
  profiles* is on; the *Log* tells you if it fell back to compatibility mode.
- **Unknown or unlisted model:** choose **Auto-detect** in *Settings › Mouse*.
- **No battery level for a few seconds after the mouse wakes up:** normal. The app
  waits for a valid reading instead of showing a wrong one (an odd reading is checked
  again before it's shown).
- **Something else:** go to *Log* and press **Report a bug**.

## Security, privacy and legal

- The only network connection is the **update check** (a read-only request to
  `api.github.com`, can be turned off) and, if you accept it, downloading the new
  version. Optional features connect only to the website they need, and only when you
  turn them on. No telemetry, no accounts.
- **Start with Windows** writes one value in
  `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (current user, no admin
  rights); turning it off removes it.
- Software remapping installs a low-level mouse hook only while it's enabled; Windows
  removes it automatically if the app closes.
- **Not affiliated with Razer.** "Razer", "Synapse" and "Chroma" are trademarks of
  Razer Inc.

## Credits

- **[OpenRazer](https://github.com/openrazer/openrazer)** (**GPL-2.0**) — the reverse
  engineering of the Razer protocol this program is based on.
- **[hidapi](https://github.com/trezor/cython-hidapi)** — HID access.

## License

**[GPL-3.0](LICENSE)** — free software with *copyleft*: you can use, study, modify and
redistribute it, but any version you distribute must remain free under the same
license. **No warranty.**

---

If you find it useful and feel like buying me a protein scoop:
☕ **https://ko-fi.com/damneddamm**
