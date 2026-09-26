
[README.md](https://github.com/user-attachments/files/32687359/README.md)
> 🌐 **[English](README.md)** · **[Español](README.es.md)**

# Non-Synapse-Mouse
![Non-Synapse-Mouse](https://i.imgur.com/MfgLxiW.png)
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
- [The 5 profiles and tracking](#the-5-profiles-and-tracking)
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
- 🎯 **Profiles**: 5 DPI presets (one per onboard profile), with **automatic
  detection and tracking of the active profile** and a **pop-up (toast)** when it
  changes.
- 🌐 **Bilingual** English / Spanish with a selector, live switching.
- 🎨 Clean desktop **interface**, flat dark theme, **fixed size**.
- 🔎 **Model selector** (~20 Razer models) + **auto-detection** of any Razer and of
  the correct `transaction_id` per command.
- 💾 **Persistent settings** (presets, color, brightness, language, last model,
  checkboxes) in a `razer_presets.json` next to the program.
- 🖥️ Fallback **console mode** (`--cli`).
- ✅ **Protocol verified** against [OpenRazer](https://github.com/openrazer/openrazer).

## What it does NOT do (limitations)

Full transparency, so nobody gets surprises:

- ❌ **No button remapping or macros.** The button-mapping command for Razer mice
  is **not reliably reverse-engineered**; shipping something that could fail
  silently was avoided.
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

## Quick start

1. **Close Razer Synapse completely** (services included, in Task Manager) or
   uninstall it. While Synapse holds the mouse, it can block the responses.
2. Run the program:
   ```
   py Non_Synapse_Mouse.py
   ```
   (or the `.exe`, or `py Non_Synapse_Mouse.py --cli` for the console).
3. Pick your **model** and press **"Detect / Test connection"**.
4. If it reads firmware, DPI and battery with sensible values, **it works**.

## Build the .exe (Windows)

No installer needed: a single self-contained `.exe` is enough.

**Easy way:** double-click `build_exe.bat` (included).

**Manual:**
```
py -m pip install pyinstaller hidapi
py -m PyInstaller --onefile --windowed --icon=icono.ico --name Non-Synapse-Mouse Non_Synapse_Mouse.py
```
The executable appears in `dist\Non-Synapse-Mouse.exe`. Copy and share it as is.
The `razer_presets.json` is created next to the `.exe` when used.

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

## The 5 profiles and tracking

The mouse stores up to 5 profiles and you switch between them with the **physical
button**. Razer **does not expose** the command to read or change the active profile
by software, so the program **infers it from the DPI**: each preset stores a
profile's DPI, **"Start tracking"** anchors Profile 1, and from then on every DPI
change is **recorded** in the right preset and the active profile is highlighted,
without you touching anything. On regaining focus it **auto-corrects** if the DPI
matches a known profile. Optionally, a **pop-up** tells you which profile you
switched to (that mode also polls in the background).

## Configuration file

`razer_presets.json`, next to the program (or the `.exe`). It holds: DPI presets,
LED color and brightness, language, last model and checkbox states. Delete it to
reset to defaults.

## Troubleshooting

- **"hidapi package missing":** `py -m pip install hidapi` (not `hid`).
- **"No interface responded":** close Synapse **completely** (services included) or
  uninstall it, and retry.
- **DPI doesn't persist:** keep *"Save to mouse memory"* checked.
- **Battery shows "n/a":** your model is wired / doesn't report battery.
- **Pop-up doesn't show in a game:** use windowed/borderless mode.
- **Weird or unlisted model:** use **"Auto-detect"**.

## Security and legal notice

- The program **only** sends standard configuration commands to the mouse. It
  doesn't touch the system, doesn't install anything, and doesn't connect to the
  internet (except opening the donation link in your browser if you click it).
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

Summary of milestones up to **v1.0.0** (first public release):

| Milestone | What was added |
|-----------|----------------|
| Base | HID communication with the Viper Ultimate: DPI, polling, battery, onboard save. |
| Multi-model | Selector of ~20 models + `transaction_id` auto-detection; 5 DPI presets. |
| Profiles | Active-profile detection by DPI (highlight). |
| Polling | Automatic polling only in the foreground (with a checkbox). |
| Tracking | Guided anchor + profile-cycle tracking + auto-correction on regaining focus. |
| Pop-up | Toast on profile change + optional background polling. |
| Lighting | LED tab: color, brightness and on/off. |
| Interface | Tabs, flat dark theme and fixed auto-fit size. |
| Branding | Renamed to *Non-Synapse-Mouse*, "About" button and donation link. |
| Languages | Bilingual EN/ES interface with selector and thorough code documentation. |
| Battery | Always-visible battery indicator, color by level and click-to-refresh. |
| **v1.0.0** | Distribution: fixed paths for the `.exe`, GPL-3.0 license, documentation. |

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
