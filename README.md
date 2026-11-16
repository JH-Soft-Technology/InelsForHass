<p align="center">
  <img src="custom_components/inels_rpc/brand/icon@2x.png" alt="InelsForHass" width="128">
</p>

<h1 align="center">InelsForHass</h1>

<p align="center">
  Home Assistant integration for the <b>iNELS BUS</b> smart home system by ELKO EP,<br>
  connected through the iNELS <b>Connection Server</b> over XML-RPC.
</p>

<p align="center">
  <a href="https://github.com/JH-Soft-Technology/InelsForHass/releases"><img src="https://img.shields.io/github/v/release/JH-Soft-Technology/InelsForHass?color=1A9E8F" alt="Release"></a>
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5" alt="HACS"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5" alt="Home Assistant">
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
| Service url | `http://192.168.1.10` | address of the Connection Server, including `http://` |
| Service port | `8001` | XML-RPC port of the Connection Server |
| Central unit name | `CU3` | name of your central unit |

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

## 🛠️ Troubleshooting

- **Cannot connect:** check that the url includes `http://`, and that the Connection Server's XML-RPC port is reachable from Home Assistant.
- **A device is missing:** the integration only sees what the Connection Server publishes. Check the device in `export.pub` (Connection Server administration → Configuration → CU config).
- **Debug logging:**

  ```yaml
  logger:
    logs:
      custom_components.inels_rpc: debug
      pyinels: debug
  ```

---

## 🐞 Issues

Found a bug or missing a device? [Open an issue](https://github.com/JH-Soft-Technology/InelsForHass/issues) and include the Home Assistant version, the integration version and the debug log.

## 📄 License

[MIT](LICENSE). iNELS is a trademark of ELKO EP, s.r.o. This project is not affiliated with or endorsed by ELKO EP.

<p align="center">
  <a href="https://www.buymeacoffee.com/jhoralek"><img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?logo=buymeacoffee&logoColor=black" alt="Buy me a coffee"></a>
</p>
