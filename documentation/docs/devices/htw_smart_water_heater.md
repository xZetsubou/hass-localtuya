# HTW Smart Plus Water Heater

**Brand:** HTW | **Category:** Water Heater

**Models:** `HTW-TV-030SMPLUS`, `HTW-TV-050SMPLUS`, `HTW-TV-080SMPLUS`, `HTW-TV-100SMPLUS`

**Product page:** [htwspain.com](https://htwspain.com/pt/%C3%A1gua-quente-pt/frasco-termico-smart-plus/){target="_blank"}

---

## Entities

| # | Platform | DP ID | Name | Device Class |
|---|---|---|---|---|
| 1 | `water_heater` | 1 | Water Heater | — |
| 2 | `switch` | 1 | Power | switch |
| 3 | `sensor` | 12 | Energy Today | energy |
| 4 | `select` | 2 | Mode | — |
| 5 | `sensor` | 10 | Current Temperature | temperature |
| 6 | `sensor` | 9 | Target Temperature | temperature |
| 7 | `sensor` | 14 | Surplus Water | water |
| 8 | `sensor` | 13 | Status | enum |
| 9 | `sensor` | 19 | Countdown Left | — |
| 10 | `binary_sensor` | 20 | Fault | problem |

**Modes:** ECO, Anti-Bacteria, Instant Heating, Smart

---

[:material-download: Download template](https://github.com/xZetsubou/hass-localtuya/blob/master/custom_components/localtuya/templates/htw_smart_water_heater.yaml){target="_blank" .md-button}
