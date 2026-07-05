# Centrometal Boiler System for Home Assistant

![Version](https://img.shields.io/badge/version-0.2.0.11-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.11%2B-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)

A Home Assistant custom integration for Centrometal Web Boiler cloud-connected heating systems using the CM WiFi-Box.

## PelTec II behavior in 0.2.0.11

PelTec II entities are created from a strict allowlist verified against an authenticated portal HTTP and WebSocket capture. Raw, hidden, duplicated, or unverified controller fields are not created as Home Assistant entities.

The integration does not create or load schedule, weather, or notification entities. Schedule values received inside the main boiler status stream are discarded before they enter the device parameter cache. Weather groups from the parameter-list response are discarded. There is no option to enable either feature.

Exposed PelTec II data includes:

- Boiler power and operating state
- Portal-visible temperatures with invalid-value filtering
- Heating-circuit enabled state, pump demand, pump state, target temperatures, and measured temperatures
- Pump, fan, heater, flame, vacuum, fuel-level, lambda, and Wi-Fi states where the portal meaning is confirmed
- Photocell resistance, fan speed, 4-way mixing-valve position, feeder-screw activity, turbulator-cleaner activity, and burner-grate position
- Descriptive attributes for temporary shutdown marks and operation-stage groups
- Working counters, including corrected total/active boiler runtime labels
- Editable portal temperature settings and the K1 circuit switch
- Controller configuration, product, software version, active file, and event history
- Cloud/WebSocket connectivity and the decoded external-start input

The Lambda Probe entity is created even when the controller omits the reading while the boiler is not firing. Any finite numeric value supplied by the controller, including idle values such as `25.5`, is displayed; a later live combustion value updates normally without reloading the integration. The Wi-Fi signal entity follows the controller display: nonzero values are shown in dB, while portal value `0` represents the unavailable `---dB` state and recovers automatically when RSSI is reported.

Older PelTec and other supported Centrometal families retain their established mappings.

## Installation

### Manual installation

1. Copy the `centrometal_boiler` folder into `config/custom_components/`.
2. Remove or replace the existing `config/custom_components/centrometal_boiler` folder first.
3. Restart Home Assistant.
4. Open **Settings → Devices & services → Add integration** and select **Centrometal Boiler System**.

On the first restart, obsolete sensor registry entries created by earlier builds are removed automatically.

### HACS custom repository

Add the repository as a custom HACS integration, install it, and restart Home Assistant.

## Configuration

Configuration is through the Home Assistant UI. Enter the Centrometal account e-mail, password, and optional entity-name prefix.

The integration options only control HTTP refresh and reconnect timing. There are no schedule or weather switches.

## Diagnostics

The Home Assistant diagnostics download includes the current parsed boiler data with credentials and location fields redacted.

## Debug logging

```yaml
logger:
  default: info
  logs:
    custom_components.centrometal_boiler: debug
```

## TLS

HTTPS and WebSocket certificate verification is always enabled and uses the `certifi` root store.

## License

Apache License 2.0. This is an independent community project and is not affiliated with Centrometal d.o.o.
