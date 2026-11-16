<p align="center">
  <img src="custom_components/inels_rpc/brand/icon@2x.png" alt="InelsForHass" width="128">
</p>

<h1 align="center">InelsForHass</h1>

<p align="center">
  Home Assistant integration for the <b>iNELS BUS</b> smart home system by ELKO EP,<br>
  connected through the iNELS <b>Connection Server</b> over XML-RPC.
</p>

<p align="center">
  <a href="https://github.com/JH-Soft-Technology/InelsForHass/releases"><img src="https://img.shields.io/github/v/release/JH-Soft-Technology/InelsForHass?color=41BDF5" alt="Release"></a>
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5" alt="HACS"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.3%2B-41BDF5" alt="Home Assistant">
  <a href="https://github.com/JH-Soft-Technology/InelsForHass/actions/workflows/validate.yml"><img src="https://github.com/JH-Soft-Technology/InelsForHass/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/JH-Soft-Technology/InelsForHass" alt="License"></a>
</p>

<p align="center">🌐 <a href="README.cs.md">Česká verze</a></p>

---

## ✨ Features

| Platform | iNELS devices | What you get |
|---|---|---|
| 💡 `light` | on/off and dimmable lights | switching, brightness for dimmers |
| 🔌 `switch` | relays, sockets, gates and garage doors | on/off |
| 🪟 `cover` | shutters and blinds | open, close, stop |
| 🌡️ `climate` | room heating regulators (`heat-control`) | current and target temperature, heating level as preset |
| 📈 `sensor` | room heating regulators | room temperature with history and statistics |

- Set up from the UI (config flow), no YAML.
- Local polling every 5 s, no cloud.
- Uses the [`pyinels`](https://github.com/JH-Soft-Technology/pyinels) library.

**Planned:** weather stations, Lara radio.

---

## 🧭 How it works

```
Home Assistant ──XML-RPC──▶ iNELS Connection Server ──▶ central unit (CU3) ──▶ BUS devices
                 :8001
```

The integration talks to the **iNELS Connection Server**, not to the central unit directly. It sees every device and variable that the Connection Server publishes from the iNELS IDM project (`export.pub`). Nothing has to be changed in the PLC.

---

## 🚀 Installation

### 1. Install via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JH-Soft-Technology&repository=InelsForHass&category=integration)

Or manually: **HACS → ⋮ → Custom repositories** → `https://github.com/JH-Soft-Technology/InelsForHass`, type **Integration** → download **Inels over XMLRPC** → restart Home Assistant.

<details><summary>Manual installation without HACS</summary>

Copy `custom_components/inels_rpc` to `/config/custom_components/` and restart Home Assistant.
</details>

### 2. Add the integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=inels_rpc)

**Settings → Devices & services → Add integration → Inels over XMLRPC** and fill in:

| Field | Example | Note |
|---|---|---|
| Host | `192.168.1.10` | IP address or host name of the Connection Server; `http://` is added automatically (a value with `http://` is accepted too) |
| Port | `8001` | XML-RPC port of the Connection Server (default `8001`) |
| Central unit | `CU3` | type of your central unit (default `CU3`) |

The same Connection Server (host and port) can be added only once.

### Changing the address

When the Connection Server gets a new IP address or port, open **Settings → Devices & services → Inels over XMLRPC → ⋮ → Reconfigure**. The connection is checked before the change is saved; entities, entity IDs and history stay as they are.

### Upgrading from 0.4.x

- The existing entry is migrated automatically, nothing has to be set up again.
- **Entity IDs do not change**, so automations, scripts and dashboards keep working.
- The **displayed names** follow the Home Assistant naming rules now: the main entity of a device has the device name, the room temperature sensor is shown as `<regulator> Room temperature` (previously `<regulator> temperature`). Names you changed yourself are kept.
- In the device registry the model shows the iNELS device type (`light`, `switch`, `door`, `shutter`, `heat-control`) and the manufacturer is ELKO EP.
- Shutters no longer report a made-up position (the central unit does not know it), so the close button is not disabled after a restart.

---

## 🌡️ Heating

Every iNELS room regulator becomes a `climate` entity (HVAC mode `heat`) plus a room temperature `sensor`.

| iNELS variable | Used for |
|---|---|
| `<room>_Temperature` | current temperature |
| `<room>_StateTH` | target temperature (read-only) |
| `<room>_StateM/U/N/K` | active heating level |
| `<room>_VM/VU/VN/VK` | switching the heating level |

**Presets = iNELS heating levels:**

| Preset | iNELS level |
|---|---|
| `minimum` | Minimum |
| `attenuation` | Attenuation (Útlum) |
| `normal` | Normal |
| `comfort` | Comfort |

- The **target temperature cannot be set directly**. The central unit derives it from the active level, and the level temperatures are configured in iNELS IDM. Selecting a preset writes `<room>_V<level>=1`, and the change shows up within about 10 seconds.
- **iNELS time programs keep running.** A preset selected from Home Assistant stays active only until the next program change.
- Valves and heat demand are not published by the Connection Server, so they are not available.

> [!TIP]
> Every preset change is a write into the central unit. When you switch levels from automations, only write on an actual change and add hysteresis and a minimum interval.

> [!NOTE]
> If the regulator's level variables are not exported, the integration only reads temperatures.

---

## 🔄 Data updates and availability

- The list of devices is loaded once when the integration starts. The values of all devices are then read every **5 seconds** in a single request.
- Commands are sent one at a time. The commanded state is shown right away and kept until a poll confirms it (at most 6 s, 20 s for heating presets), so the entity does not flicker while the central unit applies the change.
- If the Connection Server is not reachable when Home Assistant starts, the integration retries the setup automatically. If it stops answering later, all its entities become **unavailable** and recover on the first successful read; the outage is logged once.
- A command that cannot be delivered shows an error in the UI (and fails the automation step) instead of being lost silently.

### New and removed devices

- **New devices** published by the Connection Server appear after reloading the integration (**⋮ → Reload**) or restarting Home Assistant.
- Devices that the Connection Server no longer publishes are removed automatically on the next start or reload. A device can also be deleted manually from its device page when it is no longer published.

---

## ⚠️ Known limitations

- Shutters support open, close and stop only; the position is not known.
- The target temperature of the heating is read-only (see [Heating](#️-heating)).
- The integration polls; changes made elsewhere (wall switches, iNELS apps) show up within 5 seconds.
- Only devices of the types listed in [Features](#-features) are supported.

---

## 🛠️ Troubleshooting

- **Cannot connect:** check the host and port, and that the Connection Server's XML-RPC port is reachable from Home Assistant.
- **Diagnostics:** **Settings → Devices & services → Inels over XMLRPC → ⋮ → Download diagnostics** saves a file with the integration settings (without the server address), the list of devices (type, id, name, room) and their last values. Attach it to an issue.
- **A device is missing:** the integration only sees what the Connection Server publishes. Check the device in `export.pub` (Connection Server administration → Configuration → CU config).
- **Debug logging:**

  ```yaml
  logger:
    logs:
      custom_components.inels_rpc: debug
      pyinels: debug
  ```

---

## 🗑️ Removing the integration

1. **Settings → Devices & services → Inels over XMLRPC → ⋮ → Delete.** This removes the entry with all its devices and entities. Nothing is changed in iNELS.
2. If you installed it via HACS: **HACS → Inels over XMLRPC → ⋮ → Remove**. For a manual installation delete `/config/custom_components/inels_rpc`.
3. Restart Home Assistant.

---

## 🐞 Issues

Found a bug or missing a device? [Open an issue](https://github.com/JH-Soft-Technology/InelsForHass/issues) and include the Home Assistant version, the integration version and the debug log.

## 📄 License

[MIT](LICENSE). iNELS is a trademark of ELKO EP, s.r.o. This project is not affiliated with or endorsed by ELKO EP.

<p align="center">
  <a href="https://www.buymeacoffee.com/jhoralek"><img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?logo=buymeacoffee&logoColor=black" alt="Buy me a coffee"></a>
</p>
