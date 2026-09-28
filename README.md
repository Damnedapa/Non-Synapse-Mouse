> 🌐 **[English](README.md)** · **[Español](README.es.md)**

# Non-Synapse-Mouse

**A lightweight configuration tool for Razer mice — without Razer Synapse.**

Razer Synapse/Chroma takes up space, runs background services, eats RAM and needs
an account and a connection — all for tasks as simple as changing the DPI.
**Non-Synapse-Mouse** does that job by talking directly to the mouse over USB (the
same HID *feature reports* Synapse sends), **with no background services, no cloud
and no drivers to install**. Works on Windows.

> ⚠️ Independent community project. **Not affiliated with or endorsed by Razer.**
> Free software (**GPL-3.0**), provided *as is*, **with no warranty**
> (see [License](#license)).

---

## Table of contents
- [Where it comes from and why](#where-it-comes-from-and-why)
- [Features](#features)
- [What it does NOT do (limitations)](#what-it-does-not-do-limitations)
- [Supported models](#supported-models)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Build the .exe](#build-the-exe-windows)
- [How it works under the hood](#how-it-works-under-the-hood)
- [Profiles: how it works](#profiles-how-it-works)
- [Configuration file](#configuration-file)
- [Troubleshooting](#troubleshooting)
- [Security and legal notice](#security-and-legal-notice)
- [Credits](#credits)
- [Version history](#version-history)
- [License](#license)

---

## Where it comes from and why

Synapse/Chroma always felt absurd: RAM and background processes, an account and a
connection, for something as simple as setting a DPI or a color. The idea was to
be able to configure the mouse **once** and get the software off my back.

This is possible thanks to the **[OpenRazer](https://github.com/openrazer/openrazer)**
project (**GPL-2.0**), which has spent years reverse-engineering the protocol of
Razer devices. The commands (DPI, polling, battery, lighting) and protocol
structures were taken and **verified** against its code. This program **does not
copy OpenRazer's code**: it reimplements the protocol in Python, but the credit for
the reverse engineering belongs to OpenRazer and its community. **Thank you.**

To stay in tune with that ecosystem and to keep the project **free** (so nobody can
close it and sell it without sharing), it is released under **GPL-3.0**.

## Features

- 🖱️ **DPI**: read and apply. It's written to the mouse's **onboard memory**, so it
  **persists** even after you close the program (or temporarily, if you prefer).
  Slider + numeric field, with the maximum matched to each model.
- ⚡ **Polling rate**: 125 / 500 / 1000 Hz.
- 🔋 **Battery**: **always-visible** indicator in the header, with level, charging
  status and **color by level** (green/amber/red). Click to refresh. Wireless mice
  only.
- 💡 **Lighting** (logo LED): **color** (quick palette + `#RRGGBB` hex),
  **brightness** and **on/off** with a single button.
- 🤖 **Fully automatic**: connects to the mouse on its own when you open it,
  reconnects if it's unplugged or goes to sleep, and refreshes the battery by itself.
- 🎯 **Profiles, like Synapse**: while the app is open it **takes over the mouse's
  profile button** and switches between **your 5 DPI profiles** instantly and exactly.
  They're applied when the app opens; the mouse's own onboard profiles are never
  touched and come back when you close it. Optional **pop-up (toast)** on change.
- 🌐 **Bilingual** English / Spanish with a selector, live switching.
- 🎨 Clean desktop **interface**, flat dark theme, **fixed size**.
- 🔎 **Model selector** (~20 Razer models) + **auto-detection** of any Razer and of
  the correct `transaction_id` per command.
- 💾 **Persistent settings** (presets, color, brightness, language, last model,
  checkboxes) in `%APPDATA%\Non-Synapse-Mouse\razer_presets.json`, so they survive
  moving, rebuilding or updating the `.exe`. Profile tracking is remembered too.
- 🗂️ **Settings tab** (v1.1.0):
  - **Minimize to the system tray** (next to the clock), with *Show* / *Quit* menu.
  - **Start with Windows** (minimized to the tray, auto-connects to the mouse).
  - **Check for updates** on GitHub (on startup and on demand) and **download &
    install** the new `.exe` with one click (your settings are kept).
  - **Report a bug**: opens a GitHub issue with version, OS, model, firmware and
    the last log lines already filled in (nothing is sent until you submit it).
- 🗒️ Activity **log and error messages follow the selected language** (v1.1.0).
- 🖥️ Fallback **console mode** (`--cli`).
- ✅ **Protocol verified** against [OpenRazer](https://github.com/openrazer/openrazer).

## What it does NOT do (limitations)

Full transparency, so nobody gets surprises:

- ⚠️ **Button remapping is software-only (for now).** It works while the app is open
  and is **not saved to the mouse's memory** (Razer's button-mapping command isn't
  reverse-engineered yet). Left and right click are never remapped, macros aren't
  supported, and some anti-cheat systems may flag the Windows hook it uses.
- ❌ **No software profile switching.** Razer doesn't expose the command to
  select/read the active profile. Switching is done with the **physical button**;
  the program only **infers** which one you're on (by DPI).
- ❌ **Static color + brightness only.** No *breathing*, *spectrum*, *wave*, etc.,
  and no per-zone/per-key lighting (single zone: the logo).
- ❌ **No** *lift-off distance*, *angle snapping*, *debounce*, *motion sync* or the
  5-stage DPI configuration.
- ❌ **Razer mice only.** Other brands (e.g. Pulsar) use a different protocol.
- ⚠️ **Only thoroughly tested with the Razer Viper Ultimate** (the reference model).
  The rest relies on reverse engineering + auto-detection; they should work, but
  haven't been verified one by one against real hardware.
- ⚠️ If two profiles share **the same DPI**, tracking can't detect that particular
  switch.
- ⚠️ **Exclusive fullscreen games** may not show the pop-up (use windowed/borderless).

## Supported models

Selectable from the menu (plus **"Auto-detect any Razer"**):

Viper Ultimate · Viper · Viper Mini · Viper 8KHz · Viper V2 Pro · Viper Mini SE ·
DeathAdder V2 · DeathAdder V2 Pro · DeathAdder V2 Mini · DeathAdder Elite ·
DeathAdder V3 Pro · Basilisk V2 · Basilisk V3 · Basilisk Ultimate ·
Basilisk X HyperSpeed · Naga Pro · Naga X · Cobra · Mamba Elite · Orochi V2.

> Model not listed or not working? Use **"Auto-detect"**: the program probes the
> interfaces and the `transaction_id` until it finds the one that responds.

## Requirements

**As an executable (.exe):** nothing. Double-click.

**As a script (.py):**
- Python 3.8 or newer.
- The **`hidapi`** package:
  ```
  py -m pip install hidapi
  ```
  ⚠️ Install `hidapi`, **not** plain `hid` (they are different packages).
- Optional, for the system tray: `py -m pip install pystray pillow` (without them
  everything works; only the tray option is disabled).

## Quick start

1. **Close Razer Synapse completely** (services included, in Task Manager) or
   uninstall it. While Synapse holds the mouse, it can block the responses.
2. Run the program:
   ```
   py Non_Synapse_Mouse.py
   ```
   (or the `.exe`, or `py Non_Synapse_Mouse.py --cli` for the console).
3. It **connects by itself**. The header shows *Connected · (your model)* and the
   battery.
4. Press your mouse's **profile button** until you've gone through all your
   profiles once. Done: from then on it tracks them on its own.

## Build the .exe (Windows)

No installer needed: a single self-contained `.exe` is enough.

**Easy way:** double-click `build_exe.bat` (included).

**Manual:**
```
py -m pip install pyinstaller hidapi pystray pillow
py -m PyInstaller --onefile --windowed --clean --hidden-import pystray._win32 --icon=icono.ico --add-data "icono.ico;." --name Non-Synapse-Mouse_v1.1.0 Non_Synapse_Mouse.py
```
The executable appears in `dist\Non-Synapse-Mouse_v1.1.0.exe`. Copy and share it as is.
(Put `icono.ico` next to the script before building; `build_exe.bat` does all this.)

> **Note on Windows/antivirus warnings:** an unsigned PyInstaller `.exe` may trigger
> SmartScreen ("Windows protected your PC" → *More info* → *Run anyway*) and,
> sometimes, antivirus false positives. This is common for unsigned executables.
> Alternatives: share the source code (it's open, it can be read) or build with
> `--onedir`.

## How it works under the hood

The program sends **90-byte HID reports** to the mouse (the same mechanism as
Synapse): status, `transaction_id`, size, command class, command id, arguments and
a **CRC** (XOR of bytes 2..87). The commands and parameters are taken and verified
against **OpenRazer**'s code.

Robustness details:
- **Interface auto-detection:** it tries the HID interfaces and keeps the one that
  responds.
- **`transaction_id` auto-detection per command class:** different models (and even
  different commands on the same model) use different values; they are probed with
  read commands and cached.
- **No driver replacement:** it uses the system's HID stack (like Synapse); no
  Zadig or WinUSB required.

## Profiles: how it works

**Control mode (default, like Synapse).** While the app is open it puts the mouse
in its *driver mode*: the mouse stops switching its own onboard profiles and
instead **tells the app every time you press the profile button** (or the DPI
buttons). The app then applies the next of **your 5 profiles**, instantly and
exactly — no guessing.

- Your profiles live in the app (edit the DPI boxes and press *Save profiles*;
  leave a box empty to disable that profile). Click a profile name to activate it.
- They are applied as soon as the app opens and are remembered between sessions.
- The profile button goes to the next profile; *DPI down* goes to the previous one.
- **The mouse's own onboard profiles are never touched**: DPI is applied without
  writing to its memory. When you close the app, the mouse goes back to normal mode
  and its own profiles work again. (If the app were killed abruptly, unplugging and
  replugging the mouse restores it.)
- If the mouse resets or wakes up from sleep, the app takes control again on its own.
- *Reset profiles* restores the defaults (400 / 800 / 1600 / 3200 / 6400).
- Like with Synapse, the mouse's profile LED doesn't change colour in this mode
  (it's firmware-controlled). Instead, each profile shows its colour dot in the app
  and the pop-up appears in that colour.
- **Mapping tab (software remapping, Windows):** remap the wheel click, wheel up/down and the
  left side buttons to *any* action: previous/next/specific profile, clicks,
  double click, copy/paste/undo, Alt+Tab, show desktop, screenshot, media and volume
  keys, or **any custom key combination** (e.g. `ctrl+shift+s`, `alt+f4`, `f13`).
  Keys are held while you hold the button. It's **off by default**, works while the app
  is open (also minimized or in the tray) and **isn't saved to the mouse's memory yet**.
  Turn it off when playing games with anti-cheat. Left/right click are never touched.
  If your side buttons on both sides send the same signal to Windows, they're remapped
  together. On the Viper (ambidextrous), the **right side buttons** are reported by the
  mouse itself in control mode and appear in the lower group, with the same actions. Below the line, the special buttons the mouse reports in control mode
  (profile/DPI buttons and any it reports) appear automatically and take the same actions.
- **On exit** the app asks whether to write your profiles to the mouse's memory (only
  if they changed since the last time; can be turned off in Settings).
- **Write to mouse:** a guided wizard stores your profiles in the mouse's **own
  memory**, so it keeps them — with their LED colours (1 red · 2 green · 3 blue ·
  4 turquoise · 5 yellow on the Viper Ultimate) — when the app is closed or on another
  PC. It asks you to set the LED to each colour with the profile button, writes that
  profile's DPI and checks it by reading it back. *Save profiles* alone only saves
  them in the app.

**Compatibility mode (automatic fallback).** If Windows doesn't let the app listen to
the mouse's button, or if no press arrives within 25 s the first time, it returns the
mouse to normal mode and **infers the active profile from the DPI**. In this mode it
**never overwrites your profiles on its own**: if a DPI doesn't match, it just says
so. You can turn control mode off/on in *Settings › Mouse*.

## Configuration file

`%APPDATA%\Non-Synapse-Mouse\razer_presets.json` (paste `%APPDATA%` in the Explorer
address bar to get there). It holds: DPI presets, LED color and brightness,
language, last model, whether profile tracking is on, and checkbox states. Delete
it to reset to defaults. An old `razer_presets.json` next to the `.exe` (v1.0.0) is
migrated automatically.

Only **one copy** of the program runs at a time: if it's already open (e.g. in the
tray), opening it again just tells you where it is, so two copies never talk to
the mouse at once.

## Troubleshooting

- **"hidapi package missing":** `py -m pip install hidapi` (not `hid`).
- **"No interface responded":** close Synapse **completely** (services included) or
  uninstall it, and retry.
- **Profiles are mixed up:** *Reset profiles* in the Profiles tab.
- **Battery shows "n/a":** your model is wired / doesn't report battery.
- **Pop-up doesn't show in a game:** use windowed/borderless mode.
- **Weird or unlisted model:** pick **"Auto-detect"** in *Settings › Mouse*.

## Security and legal notice

- The program **only** sends standard configuration commands to the mouse. It
  doesn't touch the system and doesn't install anything.
- **Network use:** the only connection is the **update check** (a read-only request
  to `api.github.com`, can be turned off in Settings) and, if you accept it, the
  download of the new version from GitHub. Links you click (Ko-fi, bug report) open
  in your browser. No telemetry, no accounts.
- **Start with Windows** writes a single value in
  `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (current user only, no admin
  rights); unticking the option removes it.
- It's **free and open source**: you can review exactly what it does.
- It's provided **WITH NO WARRANTY of any kind**. Even though the protocol is
  verified against OpenRazer, every setup is different: **use it at your own risk**.
- **Not affiliated with Razer.** "Razer", "Synapse" and "Chroma" are trademarks of
  Razer Inc.

## Credits

- **[OpenRazer](https://github.com/openrazer/openrazer)** (**GPL-2.0**) — the
  reverse engineering of the Razer protocol this program is based on. Without their
  work, this wouldn't exist.
- **[hidapi](https://github.com/trezor/cython-hidapi)** — cross-platform HID access.

## Version history

Summary of milestones (**v1.0.0** was the first public release):

| Milestone | What was added |
|-----------|----------------|
| Base | HID communication with the Viper Ultimate: DPI, polling, battery, onboard save. |
| Multi-model | Selector of ~20 models + `transaction_id` auto-detection; 5 DPI presets. |
| Profiles | Active-profile detection by DPI (highlight). |
| Polling | Automatic polling only while the window is visible (with a checkbox). |
| Tracking | Guided anchor + profile-cycle tracking + auto-correction on regaining focus. |
| Pop-up | Toast on profile change + optional background polling. |
| Lighting | LED tab: color, brightness and on/off. |
| Interface | Tabs, flat dark theme and fixed auto-fit size. |
| Branding | Renamed to *Non-Synapse-Mouse*, "About" button and donation link. |
| Languages | Bilingual EN/ES interface with selector and thorough code documentation. |
| Battery | Always-visible battery indicator, color by level and click-to-refresh. |
| **v1.0.0** | Distribution: fixed paths for the `.exe`, GPL-3.0 license, documentation. |
| **v1.1.0** | Log/errors follow the selected language; Settings tab: system tray, start with Windows, update check & install, bug report button; window icon; **automatic mode**: auto-connect/reconnect, **control mode like Synapse** (the app handles the profile button), compatibility fallback that never overwrites profiles. |

### Ideas / roadmap
- Native button remapping (requires Wireshark captures of Synapse).
- Support for other brands (e.g. Pulsar, already reverse-engineered by the community).
- More lighting effects (breathing, spectrum…).

## License

**[GPL-3.0](LICENSE)** — free software with *copyleft*: you can use, study, modify
and redistribute it, but any version you distribute must remain free and under this
same license. See the `LICENSE` file for the full text. **No warranty.**

Trademark notice: project not affiliated with Razer Inc. "Razer", "Synapse" and
"Chroma" are trademarks of their respective owners.

---

If you find it useful and feel like buying a protein scoop:
☕ **https://ko-fi.com/damneddamm**
