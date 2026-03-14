# Changelog

## [0.0.60] - 2026-03-14

### Fixed (all device types)
- **Critical**: `if not self.enabled` guard removed from all `update_callback` methods. This silently blocked every websocket push update — all sensors and switches froze at startup values and never updated. Fixes issue #21 (circuit switches always showing OFF).
- `B_Tptv1` and `B_Tkm1` both created `sensor.*_dhw_temperature` — one was silently dropped. Now "DHW Flow Temperature" and "DHW Boiler Temperature".
- `K1B_CircType/korType/dayNight` duplicated between sensor maps — now created once.
- `B_ODRTMP` now has `°C` unit and temperature device class.
- `K1B_korN` now has `°C` unit and temperature device class.
- `CNT_1` (Burner Starts) and `CNT_7` (Vacuum Turbine Cycles) had empty string unit — now None.
- `device_state_attributes` (deprecated) replaced with `extra_state_attributes` everywhere.

### Improved sensor display
- Pump states `B_P2`, `B_P3`, `B_P4`, `B_Paku`, `B_Pk1_k2` now show ON/OFF (consistent with `B_P1`).
- Vacuum states `B_VAC_STS`, `B_VAC_TUR` now show ON/OFF.
- Active states `B_dop`, `B_doz`, `B_specG`, `B_start` now show ON/OFF.
- `B_Valve` now shows Open/Closed instead of Yes/No.
- `B_puz` (Pellet Transporter) now shows Yes/No.
- Heating circuit `_onOff`, `_P`, `_zahP`, `_misC`, `_misO` now show ON/OFF.
- Heating circuit `_dayNight` now shows Day/Night/Program instead of raw 0/1/2.
- `B_razina` shows Empty/Reserve/Full.
- `B_SUP_TYPE` shows None/Pellet Screw/Vacuum.
- Binary sensors (`B_Ppwm`, `B_P1`, `B_gri`, `B_fan01`, `K1B_onOff`, `K1B_P`) show ON/OFF.
- `B_fireS`, `B_zahPa`, `B_cm2k` show Yes/No.

### Added
- Full `peltec2` (PelTec II Lambda) device type support.
- `WebBoilerOperationStateSensor`: translates `B_STATE` to human-readable strings (OFF, S0-S7, SP1-SP5, D0-D6, PF0-PF4, C0).
- `B_fanB` (Fan B Speed), `B_WifiVER` (WiFi Box Version) sensors.
- Heating circuit `_misC`/`_misO` (Valve Closing/Opening), `_korN`, `_Prec`, `_zahP`.
- All PelTec II specific parameters mapped.
- `SensorStateClass.MEASUREMENT` for temperature/percentage sensors.
- `SensorStateClass.TOTAL_INCREASING` for counters.
- Unknown parameters auto-exposed, hidden in entity registry by default.
- Bundled `py-centrometal-web-boiler==0.0.60` with SSL fixes — no PyPI dependency.
- Entity deduplication at setup.

### Removed
- `WebBoilerCurrentTimeSensor`, `WebBoilerBinaryStateSensor`, `WebBoilerPelletLevelSensor` (logic merged or unused).
- Runtime monkey patches (baked into bundled wheel).
- Duplicate raw 0/1 params: `B_zahPpwm`, `B_zahP1`, `B_zahK1_K2`, `B_zahValve`, `B_PTV_PRI`.
