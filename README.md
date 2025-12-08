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
    centrometal_web_boiler: debug
```

After a restart detailed log entries will appear in `/config/home-assistant.log`.
