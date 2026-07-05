# Changelog

## 0.2.0.11 — controller targets, requests, recirculation, and Wi-Fi RSSI correction

- Added K1 heating-circuit enabled state, pump demand, flow target temperature, and room target temperature while preserving the existing measured-temperature and pump entities.
- Kept target temperatures out of long-term measurement statistics because they are setpoints rather than measured values.
- Added DHW priority, conditional buffer-tank heat request, DHW recirculation enabled, and DHW recirculation pump states only for controller configurations containing the corresponding DHW or buffer component.
- Corrected `CNT_0` to Boiler Work + Standby Time and `CNT_15` to Boiler Work Time; both runtime values use minutes.
- Corrected Wi-Fi signal handling to match the controller display: the entity uses dB and portal value `0` is treated as the unavailable `---dB` sentinel. Nonzero readings become available automatically, without creating long-term RSSI statistics.
- Preserved all existing unique IDs and left unverified mode, safety, valve-direction, and auxiliary-output parameters hidden.

## 0.2.0.10 — restore Lambda and Wi-Fi readings

- Restored the v1-compatible Lambda behavior: finite controller values such as `0`, `25.4`, and `25.5` are displayed instead of forcing the entity unavailable.
- Restored Wi-Fi signal to the portal percentage unit and preserved `0` as a valid reading.
- Kept the Lambda placeholder entity so it still appears when the controller temporarily omits the parameter and recovers automatically when a value returns.
- Added diagnostic attributes for Lambda measurement activity, boiler state, flame detection, raw values, and portal connection context without changing entity IDs.
- Left all other 0.2.0.9 mappings and entities unchanged.

## 0.2.0.9 — documented PelTec II telemetry and resilient Lambda entity

- Added documented PelTec II operation stages `S3-1`, `S3-2`, and `S7` without changing existing stage values.
- Added operation-stage group, description, raw-code, and modulation-level attributes.
- Added descriptive attributes for `R`, `B`, `T`, `G`, and `F` temporary shutdown marks while preserving their existing entity states.
- Exposed photocell resistance, fan speed, 4-way mixing-valve position, feeder-screw activity, turbulator-cleaner activity, and burner-grate position.
- Kept the Lambda Probe entity present when the controller omits the value while not firing; it becomes available automatically when a valid reading returns.
- Corrected the PelTec II display names for rated boiler power and DHW tank temperature, and added the kW unit to rated power.
- Left uncertain safety, recirculation, auxiliary-output, and ambiguous counter mappings unchanged.

## 0.2.0.8 — final PelTec II cleanup

- Rebuilt PelTec II entity creation around a strict portal-confirmed allowlist.
- Removed raw, hidden, duplicated, and unverified PelTec II fallback entities.
- Removed weather, schedule, and notification entities and their loading paths.
- Discarded PelTec II schedule values during HTTP and WebSocket ingestion.
- Discarded portal weather groups during parameter-list parsing.
- Added automatic removal of obsolete sensor registry entries from earlier builds.
- Corrected internet-access, Wi-Fi dB, status-mark, transition-state, fuel-level, lambda, and temperature decoding.
- Decoded the external-start input from the controller bitmask without exposing the raw input value.
- Corrected pump, heater, demand, configuration, and active-file names.
- Kept invalid portal sentinel values unavailable instead of presenting them as measurements.
- Retained decoded portal error history and confirmed editable settings.
- Added portal-capture regression tests and Home Assistant runtime smoke validation.
