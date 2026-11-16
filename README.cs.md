<p align="center">
  <img src="custom_components/inels_rpc/brand/icon@2x.png" alt="InelsForHass" width="128">
</p>

<h1 align="center">InelsForHass</h1>

<p align="center">
  Integrace chytré elektroinstalace <b>iNELS BUS</b> od ELKO EP do Home Assistantu,<br>
  připojená přes iNELS <b>Connection Server</b> protokolem XML-RPC.
</p>

<p align="center">
  <a href="https://github.com/JH-Soft-Technology/InelsForHass/releases"><img src="https://img.shields.io/github/v/release/JH-Soft-Technology/InelsForHass?color=41BDF5" alt="Release"></a>
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5" alt="HACS"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5" alt="Home Assistant">
  <a href="https://github.com/JH-Soft-Technology/InelsForHass/actions/workflows/validate.yml"><img src="https://github.com/JH-Soft-Technology/InelsForHass/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/JH-Soft-Technology/InelsForHass" alt="Licence"></a>
</p>

<p align="center">🌐 <a href="README.md">English version</a></p>

---

## ✨ Co umí

| Platforma | Zařízení iNELS | Co dostanete |
|---|---|---|
| 💡 `light` | spínaná a stmívaná světla | zapnutí/vypnutí, jas u stmívačů |
| 🔌 `switch` | relé, zásuvky, brány a garážová vrata | zapnutí/vypnutí |
| 🪟 `cover` | rolety a žaluzie | otevřít, zavřít, zastavit |
| 🌡️ `climate` | regulátory vytápění místností (`heat-control`) | aktuální a žádaná teplota, úroveň topení jako preset |
| 📈 `sensor` | regulátory vytápění místností | teplota místnosti s historií a statistikami |

- Nastavení z UI (config flow), bez YAML.
- Lokální dotazování každých 5 s, bez cloudu.
- Používá knihovnu [`pyinels`](https://github.com/JH-Soft-Technology/pyinels).

**Plánováno:** meteostanice, rádio Lara.

---

## 🧭 Jak to funguje

```
Home Assistant ──XML-RPC──▶ iNELS Connection Server ──▶ centrální jednotka (CU3) ──▶ zařízení na sběrnici
                 :8001
```

Integrace komunikuje s **iNELS Connection Serverem**, ne přímo s centrální jednotkou. Vidí všechna zařízení a proměnné, které Connection Server publikuje z projektu iNELS IDM (`export.pub`). V PLC se nic měnit nemusí.

---

## 🚀 Instalace

### 1. Instalace přes HACS

[![Otevřít repozitář v HACS ve vašem Home Assistantu.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JH-Soft-Technology&repository=InelsForHass&category=integration)

Nebo ručně: **HACS → ⋮ → Vlastní repozitáře** → `https://github.com/JH-Soft-Technology/InelsForHass`, typ **Integrace** → stáhnout **Inels over XMLRPC** → restartovat Home Assistant.

<details><summary>Ruční instalace bez HACS</summary>

Zkopírujte `custom_components/inels_rpc` do `/config/custom_components/` a restartujte Home Assistant.
</details>

### 2. Přidání integrace

[![Začít nastavovat integraci ve vašem Home Assistantu.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=inels_rpc)

**Nastavení → Zařízení a služby → Přidat integraci → Inels over XMLRPC** a vyplňte:

| Pole | Příklad | Poznámka |
|---|---|---|
| URL | `http://192.168.1.10` | adresa Connection Serveru včetně `http://` |
| Port služby | `8001` | XML-RPC port Connection Serveru |
| Typ jednotky | `CU3` | název centrální jednotky |

---

## 🌡️ Vytápění

Každý regulátor místnosti v iNELS se v HA objeví jako entita `climate` (režim `heat`) a k tomu `sensor` teploty místnosti.

| Proměnná iNELS | Použití |
|---|---|
| `<místnost>_Temperature` | aktuální teplota |
| `<místnost>_StateTH` | žádaná teplota (jen pro čtení) |
| `<místnost>_StateM/U/N/K` | aktivní úroveň topení |
| `<místnost>_VM/VU/VN/VK` | přepnutí úrovně topení |

**Presety = úrovně topení iNELS:**

| Preset | Úroveň iNELS |
|---|---|
| Minimum | Minimum |
| Útlum | Útlum |
| Normál | Normál |
| Komfort | Komfort |

- **Žádaná teplota se nedá nastavit přímo.** Centrální jednotka ji počítá z aktivní úrovně a teploty úrovní se nastavují v iNELS IDM. Výběr presetu zapíše `<místnost>_V<úroveň>=1`, změna se projeví zhruba do 10 sekund.
- **Časové programy iNELS běží dál.** Preset zvolený z Home Assistantu platí jen do další změny v programu.
- Stav ventilů ani poptávku po teple Connection Server nepublikuje, nejsou proto k dispozici.

> [!TIP]
> Každá změna presetu je zápis do centrální jednotky. Když úrovně přepínáte automatizací, zapisujte jen při skutečné změně a použijte hysterezi a minimální interval.

> [!NOTE]
> Pokud proměnné úrovní regulátoru nejsou exportované, integrace čte jen teploty.

---

## 🛠️ Řešení potíží

- **Nepovedlo se připojit:** zkontrolujte, že URL obsahuje `http://` a že je XML-RPC port Connection Serveru z Home Assistantu dostupný.
- **Chybí zařízení:** integrace vidí jen to, co Connection Server publikuje. Zkontrolujte zařízení v `export.pub` (administrace Connection Serveru → Configuration → CU config).
- **Ladicí log:**

  ```yaml
  logger:
    logs:
      custom_components.inels_rpc: debug
      pyinels: debug
  ```

---

## 🐞 Chyby a návrhy

Narazili jste na chybu nebo vám chybí zařízení? [Založte issue](https://github.com/JH-Soft-Technology/InelsForHass/issues) a přiložte verzi Home Assistantu, verzi integrace a ladicí log.

## 📄 Licence

[MIT](LICENSE). iNELS je ochranná známka společnosti ELKO EP, s.r.o. Projekt není s ELKO EP spojen ani jím schválen.

<p align="center">
  <a href="https://www.buymeacoffee.com/jhoralek"><img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?logo=buymeacoffee&logoColor=black" alt="Buy me a coffee"></a>
</p>
