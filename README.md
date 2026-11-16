[![Board Status](https://dev.azure.com/JH-Soft-Technology/ea6666c8-9de9-44c9-9767-69a01e3640dc/93f17136-8240-4edb-bd99-efdb435cca03/_apis/work/boardbadge/79979854-27b8-4ce5-b2f0-111ba419b94a?columnOptions=1)](https://dev.azure.com/JH-Soft-Technology/ea6666c8-9de9-44c9-9767-69a01e3640dc/_boards/board/t/93f17136-8240-4edb-bd99-efdb435cca03/Microsoft.RequirementCategory/)

# InelsForHass is a Home Assistant HACS itegration for Elko inels smart home

_Integrates all common devices from Inels BUS system into the Home Assistant._

## What?

InelsForHass gives you a chance to control your proprietary Inels devieces through the Home Assistant.

## Supported devices

- [x] Ordinary and dimmable lights
- [x] Switches
- [x] Shades
- [x] Garage doors
- [x] Heating (room controllers as `climate` entities + room temperature `sensor`)
- [ ] Weather stations
- [ ] Lara radio

## Heating

Every iNELS `heat-control` room regulator is exposed as a `climate` entity (HVAC mode `heat`) together with a room temperature `sensor`.

- The current temperature is read from `<room>_Temperature`.
- The **preset** selects the active iNELS level: `minimum`, `attenuation` (Útlum), `normal`, `comfort`. Selecting a preset writes `<room>_V<level>=1`.
- The target temperature is shown read-only. iNELS calculates it from the active level, so it cannot be set directly. The temperatures of the levels are configured in iNELS IDM.
- Valves and heat demand are not published by the Connection Server and are therefore not available.

> **Note:** the iNELS time programs keep switching levels automatically, so a preset selected from Home Assistant is overridden at the next program change. Every preset change is a write into the central unit — use automations with hysteresis and a sensible minimum interval.

The room variables (`*_Temperature`, `*_StateTH`, `*_State*`, `*_V*`) must be exported from IDM (`export.pub`); nothing needs to be changed in the PLC.

## HowTo

At the beginning you need to install [HACS](https://hacs.xyz/) into your home assistant instance. All you need to know about instalation is on the web site.

When you have HACS installed, click the button below, or open the HACS UI, go into the integration section, click the three dots in the top right corner and select *Custom repositories*.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JH-Soft-Technology&repository=InelsForHass&category=integration)

Copy URL of IneslForHass (https://github.com/JH-Soft-Technology/InelsForHass) repo into repository field and select category integration.

Search for InelsForHass. Then download it and configure.

## Issues

~~If~~ When you experience issues/bugs with this the best way to report them is to open an issue in **this** repo.

[Issue link](https://github.com/JH-Soft-Technology/InelsForHass/issues/)

[![buy me a coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jhoralek)
