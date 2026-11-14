[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
![Maintenance](https://img.shields.io/maintenance/yes/2023.svg)

# hass-centrometal-boiler

Home Assistant custom component integration for Centrometal Boiler System (with CM WiFi-Box).

To visualize boiler display as card use https://github.com/9a4gl/lovelace-centrometal-boiler-card card.

## About

This component is based on https://github.com/9a4gl/py-centrometal-web-boiler library to connect to Centrometal web boiler system.
The integration is created to support Centrometal Boiler System with CM WiFi-Box in Home Assistant.

This is based on analysis of Centrometal's web application. I have asked Centrometal for specification and support for integrating their boilers into Home Assistant. They have not replied to any of my 5 emails sent during March, April and May of 2021. After calling them by phone, they comfirmed receiving of my emails and promised to contact me back on Friday 16-Apr-2021, but that have not happened on 16-Apr-2021 or any date later so far. What a pity.

## Installation

Requires Home Assistant core-2021.11.3 or newer.

### Installation through HACS

If you have not yet installed HACS, go get it at https://hacs.xyz/ and walk through the installation and configuration.

Use "https://github.com/9a4gl/hass-centrometal-boiler" as URL for a new HACS custom repository.

Then find the Centrometal Boiler System integration in HACS and install it.

Install the new integration through *Configuration -> Integrations* in HA (see below).

### Manual installation

Copy the sub-path `/hass-centrometal-boiler/custom_components/centrometal_boiler` of this repo into the path `/config/custom_components/centrometal_boiler` of your HA installation.

Alternatively use the following commands within an SSH shell into your HA system.
Do NOT try to execute these commands directly your PC on a mounted HA file system. The resulting symlink would be broken for the HA file system.
```
cd /config
git clone https://github.com/9a4gl/hass-centrometal-boiler.git

# if folder custom_components does not yet exist:
mkdir custom_components

cd custom_components
ln -s ../hass-centrometal-boiler/custom_components/centrometal_boiler
```

## Configuration

### Frozen measurements after November 14, 2026

[Issue #29](https://github.com/9a4gl/hass-centrometal-boiler/issues/29)
documents a broker permission error. HTTPS login and the status endpoint
still worked while the broker accepted STOMP CONNECT and rejected SUBSCRIBE
with ACCESS_REFUSED. The HTTP REFRESH and RSTAT commands request device
updates. They do not apply the returned measurements to Home Assistant.

The patched integration falls back immediately on a STOMP error or after
60 seconds without a valid live parameter update for any installation.
It reads one authenticated HTTP snapshot for all installations every 60
seconds, applies measurements for installations without fresh live data
to their existing parameters, and retries WebSocket subscriptions
automatically. Once every installation receives live updates again,
polling stops. Failed requests use backoff up to five minutes. An expired
session triggers one login and one retry per polling cycle. After three
minutes without usable data from either source, affected readings are
marked unavailable until data resumes.

#### Patch an existing HACS installation

1. Create a Home Assistant backup and save a copy of
   `/config/custom_components/centrometal_boiler/` outside
   `custom_components`. Keep the original config entry, entity registry,
   and recorder database. The existing account, device and entity identifiers
   preserve dashboard and automation references and recorder history.
2. Pause any automation or external tool that installs updates for this HACS
   repository, or exclude its update entity from that automation. In
   **Settings → Devices & services → Entities**, you can disable the
   repository's HACS **update** entity to suppress update prompts. Avoid
   **Update**, **Redownload**, and **Remove** for this repository while the
   patch is installed. A skipped version only suppresses that release.
3. Download the patched branch or commit. Copy the following files from its
   `custom_components/centrometal_boiler/` directory into the same relative
   locations under `/config/custom_components/centrometal_boiler/`:
   - `__init__.py`
   - `transport.py` (new)
   - `config_flow.py`
   - `switch.py`
   - `sensors/WebBoilerGenericSensor.py`
   - `switches/WebBoilerCircuitSwitch.py`
   - `switches/WebBoilerPowerSwitch.py`

   For the v0.0.54 overlay, keep its manifest and all other installed files.
   This retains its published `py-centrometal-web-boiler==0.0.58` dependency
   and its existing set of entities. The patched files also support the
   published `0.0.61` dependency pinned on upstream main.
4. Restart Home Assistant. Open a temperature sensor already on your
   dashboard or in **Developer Tools → States**. Watch it through a natural
   change in boiler temperature and compare against the web portal. During
   fallback allow at least two poll cycles. Compare both its value and
   **Last updated** attribute, and check its existing History view before
   and after the restart. A steady measurement can keep the same value.
5. To inspect transport activity, enable debug logging for
   `custom_components.centrometal_boiler.transport`. It reports transport
   mode, subscription status, the last accepted live and HTTP readings, and
   retry activity. The existing connection binary sensor reports the
   WebSocket even while measurements are available through HTTP.

#### Roll back to v0.0.54

Restore the saved v0.0.54 integration directory in the same location and
remove the added `transport.py` if you restore by copying over individual
files. Alternatively, use HACS **Redownload** and select release `0.0.54`.
Restart Home Assistant with the same config entry and recorder database.
Re-enable the HACS update entity or update automation if desired. The
original live-only behavior returns, so readings can freeze again if the
broker still rejects subscriptions.

The regression tests use simulated broker messages and HTTP responses.
Live BioTecPlus measurements and an in-place restart on a running Home
Assistant system still need hardware validation.

### Home Assistant

Setup under Integrations in Home Assistant, search for "Centrometal Boiler System". You need to enter e-mail and password.

Even though this integration can be installed and configured via the Home Assistant GUI (uses config flow), you might have to restart Home Assistant to get it working.

## Supported devices

The following devices are supported, other may work with CM WiFi-Box.

* PelTec-lambda, Peltec
* CentroPlus + Cm Pelet-set
* BioTec-L
* EKO-CK P + Cm Pelet-set
* BioTec-Plus (also Morvan GMX EASY)
* EKO-CKS Multi Plus ? (need tester) ?

## Services

`centrometal_boiler.turn`
Start or stop the boiler..

## Development

### Debugging

To enable debug logging for this integration and related libraries you
can control this in your Home Assistant `configuration.yaml`
file. Example:

```
logger:
  default: info
  logs:
    custom_components.centrometal_boiler: debug
```

After a restart detailed log entries will appear in `/config/home-assistant.log`.
