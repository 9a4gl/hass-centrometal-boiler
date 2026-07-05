# PelTec II entity policy and parameter reference

Version 0.2.0.11 was checked against an authenticated Centrometal portal capture containing the status payload, portal templates, parameter definitions, controls, error history, and live WebSocket traffic.

## Entity policy

PelTec II uses a strict allowlist:

1. Create an entity only when the portal meaning and conversion are confirmed.
2. Use internal helper values only to decode a confirmed entity.
3. Do not create raw fallback entities for unknown controller fields.
4. Do not create weather, schedule, or notification entities.
5. Discard schedule values and weather groups during ingestion.

Examples of internal-only values include `B_addConf`, `B_Inp1`, and `B_cm2k`. `B_addConf` controls whether pellet percentage is meaningful, and bit 6 of `B_Inp1` is exposed as the decoded External Start Input binary sensor. The raw values themselves are not entities.

## Confirmed values

| Parameter | Home Assistant meaning | Rule |
|---|---|---|
| `B_SUP_TYPE` | Internet Access | `1` Supervision, `2` Supervision + control |
| `B_signal` | WiFi Signal | dB when reported; portal `0` maps to `---dB`; diagnostic sensor without long-term statistics |
| `B_specG` | Status Mark | `0` None, `1` R, `2` B, `3` T, `4` G, `5` F; descriptive shutdown attributes included |
| `B_start` | Start / Stop Transition | `0` Idle, `1` Starting, `2` Stopping; `B_STATE=S7-3` is paused/standby |
| `B_Oxy1` | Lambda Probe | entity is always created; every finite numeric portal value is displayed, including idle values such as `25.5` |
| `B_razina` | Fuel Level State | `0` Empty, `1` Reserve, `2` Full |
| `B_FotV` | Photocell Resistance | kΩ; `1001` represents the controller display `>1000 kΩ` |
| `B_fan` | Fan Speed | rpm |
| `B_misP` | 4-Way Mixing Valve Position | `0–100%` |
| `B_puz` | Feeder Screw | Off/On |
| `B_tur` | Turbulator Cleaner | Off/On |
| `B_resInd` + `B_resDir` + `B_resMax` | Burner Grate Position | signed position state with direction and semantic attributes |
| `B_razP` | Pellet Level | `0–100%`; created only when `B_addConf` bit 3 is set |
| `B_Tk1` | Boiler Temperature | portal-valid temperature |
| `B_Tkm1` | DHW Tank Temperature | portal-valid temperature |
| `B_Tak1_1` | Buffer Tank Temperature (Upper) | portal-valid temperature |
| `B_Tak2_1` | Buffer Tank Temperature (Lower) | portal-valid temperature |
| `B_Tdpl1` | Flue Gas Temperature | `-45 < value < 300`, excluding zero |
| `B_Tpov1` | Boiler Return Temperature | `-45 < value < 145`, excluding zero |
| `B_Ths1` | Hydraulic Crossover Temperature | invalid/sentinel values are unavailable |
| `B_Tva1` | Outside Temperature | `-45 < value < 145` |
| `K1B_Tpol1` | K1 Flow Measured Temperature | `-45 < value < 145` |
| `K1B_Tsob1` | K1 Room Measured Temperature | invalid/sentinel values are unavailable |
| `K1B_Tpol` | K1 Flow Target Temperature | setpoint; no measurement state class |
| `K1B_Tsob` | K1 Room Target Temperature | setpoint; no measurement state class |
| `K1B_onOff` | K1 Heating Circuit Enabled | Off/On |
| `K1B_zahP` | K1 Pump Demand | Off/On request, separate from actual pump state |
| `B_Ppwm` | PWM Pump | Off/On |
| `B_fan01` | Boiler Fan | Off/On |
| `B_P1`…`B_P4` | Pump states | Off/On |
| `B_gri` | Electric Heater | Off/On |
| `B_zahPpwm` | PWM Pump Demand | Off/On demand signal, separate from pump state |
| `B_VAC_TUR` | Vacuum Turbine | Off/On |
| `B_fireS` | Flame State | Off/On |
| `K1B_P` | K1 Circuit Pump | Off/On |
| `B_PTV_PRI` | DHW Priority | Off/On |
| `B_bup` | Buffer Tank Heat Request | Off/On; created only in buffer configurations |
| `B_REC` | DHW Recirculation Enabled | Off/On; created only in DHW configurations |
| `B_REO` | DHW Recirculation Pump | Off/On; created only in DHW configurations |
| `B_FILE` | Active File | controller file string |
| `B_KONF` | Configuration | raw `12` maps to portal label `13. DHC 2X` |

`CNT_0` is Boiler Work + Standby Time and `CNT_15` is Boiler Work Time. Both are cumulative minute counters; the remaining counter mappings are unchanged.

## Data intentionally not exposed

- Schedule selectors and table values (`PVAL`, `PDEF`, `PMIN`, and `PMAX` for database indexes 223–226)
- Portal weather forecast data
- Raw protocol/timing fields such as `PING`, `B_Time`, `CMD_TIME`, `SE00`, `SE01`, `SE02`, and `wf_req`
- Raw encoded event markers (`IW1-1`, `IW1-2`); decoded event history is used instead
- Unknown or unverified controller telemetry such as the `B_Sts*`, `B_puz*`, and similar fields visible in raw diagnostics
- Duplicate metadata already represented by the Home Assistant device

These values may still exist in the server response, but they do not become stored PelTec II parameters or Home Assistant entities where an ingestion filter applies.
