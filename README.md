# HiSense Air Conditioners

This is a fork of [deiger/AirCon](https://github.com/deiger/AirCon). The original connects the
A/C(s) to Home Assistant through an MQTT broker; this fork drops MQTT entirely and instead runs a
native [ESPHome] API server (via [aioesphomeserver]), so the A/C(s) show up directly in Home
Assistant's ESPHome integration - the same one it already uses for real ESPHome devices. No
broker to run, push-based state updates, and reconnect handling that comes for free from the
ESPHome client Home Assistant already ships. See [ESPHome integration](#esphome-integration)
below for what that gets you and its current limitations.

This program implements the Ayla Networks LAN API to interact with HiSense WiFi Air Conditioner module, models AEH-W4B1 and AEH-W4E1, as well as Fujitsu FGLair.

As discussed [here](../../issues/1), the program doesn't seem to fit the AEH-W4A1 module, which relies on entirely different protocol (implemented by the apps [Hi-Smart Life](https://play.google.com/store/apps/details?id=com.qd.android.livehome), [AirConnect](https://play.google.com/store/apps/details?id=com.oem.android.airconnect), [Smart Cool](https://play.google.com/store/apps/details?id=com.oem.android.livehome), [AC WIFI](https://play.google.com/store/apps/details?id=com.oem.android.ecold) and [טורנדו WiFi](https://play.google.com/store/apps/details?id=com.oem.android.tornadowifi)). Please let me know if you have a different experience, or tried it with other modules.

The module is installed in A/Cs and humidifiers that are either manufactured or only branded by many other companies. These include Beko, Westinghouse, Winia, Tornado, York and more.

**This program is not affiliated with Ayla Networks, HiSense, Fujitsu, any of their subsidiaries, or any of their resellers.**

## Prerequisites

1. Air Conditioner with HiSense AEH-W4B1 or AEH-W4E1 installed, or a Fujitsu FGLair.
1. Have Python 3.14 or above installed (required by the ESPHome server dependency). If using Raspberry Pi, use a recent Raspbian/Raspberry Pi OS release that ships it, or use the Docker method below instead.
1. Configure the A/Cs with the dedicated app. Links to each app are available in the table below. Log into the app, associate each A/C and connect it to the network, as described in the app documentation.
1. Once everything has been configured, the A/Cs can be blocked from connecting to the internet, as it will no longer be needed. Set them static IP addresses in the router, and write them down.
   * Note: _To avoid the need for manual changes later, make sure the app is aware of the new IP addresses before disconnecting the A/Cs from the internet._
1. Find the code for your app, from the list below:

   | Code       | App Name            | App link
   |------------|---------------------|---------|
   | beko-eu    | Beko?               | |
   | haxxair    | HAXXAIR WIFI REMOTE | [![](https://lh3.googleusercontent.com/-9FX7-sYlE2xDwG9uymjPejV-P8nI_hQ9zN7QDu6OgyYILbjdg5o38nQTvAmFTPyiw=s50-rw)](https://play.google.com/store/apps/details?id=com.aylanetworks.accontrol.haxxair) |
   | denali-us  | Denali Aire         | [![](https://lh3.googleusercontent.com/8NYl3eNN7M_cXmvo4ywj9al5794Ci_dzGYxYZopHd96Z4yr1M12e8xzk9mkz5cMELQ=s50-rw)](https://play.google.com/store/apps/details?id=com.smart.internationalus.denaliaire) |
   | fglair-eu  | FGLair              | [![](https://lh3.googleusercontent.com/LcrpWfFdRi3GriCV3MqPhkKsxV-IkwFHxZHHDugC__iaO1HE-7UyKuQj-bEWyggo8DFP=s50-rw)](https://play.google.com/store/apps/details?id=com.fujitsu.fglair) |
   | field-us   | HiSmart Air         | [![](https://lh3.googleusercontent.com/9p4SUOklfccVzJdrbhHZW8MlmioF-YgfLWOQBtad2N_A5AWtcyNv7X-M3QT1e2Fdam00=s50-rw)](https://play.google.com/store/apps/details?id=com.aylanetworks.accontrol.hisense) |
   | hisense-eu | HiSmart Life        | [![](https://lh3.googleusercontent.com/AbCPfEScNDwgsKozku6jmItFPVq9WJCl30jZKlSDFDAtlAiC3WRZZ4MlWEEWR8ZxKA=s50-rw)](https://play.google.com/store/apps/details?id=com.hisense.hismartinternationalforandroid) |
   | hisense-us | HiSmart Home        | [![](https://lh3.googleusercontent.com/Qs9UJVhczWYk-ij7UiRWoCDi2pYIoOUYuU5pBwOKQSD_07KHyAnLGg-myF7U9a387w=s50-rw)](https://play.google.com/store/apps/details?id=com.hisense.hismartinternationalus) |
   | hismart-eu | Smart-Living        | [![](https://lh3.googleusercontent.com/k9p0RMiW_xax5FIU5tpwSZav1In7tu6szGQopRWhSyRd2dIr0_L0IWHPVLSHxbrWrA=s50-rw)](https://play.google.com/store/apps/details?id=com.smart.international2) |
   | hismart-us | AI-Home             | [![](https://lh3.googleusercontent.com/eUJicIOk50rP391IFs0Xw6306adghQuiQtaLgUkxImuP6bAdHvQjS1gbIKY75Bd2mkA=s50-rw)](https://play.google.com/store/apps/details?id=com.smart.internationalus) |
   | huihe-us   | SunHome             | [![](https://lh3.googleusercontent.com/3tI6Nbx4ZlphD_b5O7bW3XcMEKnFkViOKMS9-cL9K9OQVyGJRjRmKu67JU8_t_w93iZs=s50-rw)](https://play.google.com/store/apps/details?id=com.sunvalley.sunhome) |
   | mid-eu     | WiFi AC             | [![](https://lh3.googleusercontent.com/LWmnlcSnT2hYmdwB2vq5SoBuaawkS8eu0F6n9Tytowrftp7kflmUXRAt_uWg7C0Fgspn=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.mid.europe.hisense) |
   | mid-us     | Smiling Air         | [![](https://lh3.googleusercontent.com/op7-cqkm6N3JinyViCONKKgIVeMWI4BGO4TP3atRheGKG_vzsufh1PmEa-v9b8OAEPI=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.mid.america.hisense) |
   | oem-eu     | Hi-Smart AC         | [![](https://lh3.googleusercontent.com/-HdiS1L18OjviXxGY68fvuBO3I4J1XGEEPOIc0f8p268f0ZJYkADHVvOgzH2wttsBwnk=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.europe.hisense) |
   | oem-us     | Hisense?            | |
   | tornado-us | &#x2067;טורנדו WIFI גרסה 2&#x2069; | [![](https://lh3.googleusercontent.com/M9kU7oYeZTU8hVLChdJQL4giJacgUT2yFw-pqNk8JR4kbqbvl9x8dT88BC0admZrrQ=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.tornado.america.hisense) |
   | winia-us   | 위니아 에어컨 홈스마트        | [![](https://lh3.googleusercontent.com/IGIkHlnLbFxTFGOk_aql3sVGgL9DLOtc3Ti_oDhQLUT8_-8PGmXjVBcQnmgqWxitB_U=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.winia.america.hisense) |
   | wwh-us     | Westinghouse?       | |
   | york-us    | YORK Smart          | [![](https://lh3.googleusercontent.com/udf-qe7lXPJ5d7pi96WC8ex20-DuzAvAfyYX1i9B0zyvKjj0TLqoWwZmju-M5y0dQwE=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.york.america.hisense) |

## Run the A/C control server as a HomeAssistant add-on

If using [HomeAssistant], this is the preferred method.

1. In the HomeAssistant UI, enter **Supervisor → Add-on Store**.
1. Click **⋮ menu → Repositories**.
1. Add `https://github.com/vetalkordyak/AirCon` to the list.
1. Choose **HiSense Air Conditioner** and install it.
1. Update the configuration as detailed within the add-on.
1. Start the add-on. Do not forget to enable **Start on boot** and **Watchdog**.

## Run the A/C control server in docker

Use this method if not using HomeAssistant, or if you prefer to set it up outside of HomeAssistant.

1. Download the [`docker-compose.yaml`](docker-compose.yaml) and [`options.json`](options.json). Update all the relevant fields in `options.json`:
   - For every app (multiple apps are supported), set `username` and `password` to your app login credentials, and `code` to the app code from the list above.
     These will be used to discover you A/Cs and get their LAN keys, if there are no config files in the config directory (`/opt/hisense`).
   - Set `esphome_port` (default `6053`) and `esphome_web_port` (default `6052`) if you need to change them, or set `esphome_port` to `0` to disable the ESPHome server entirely.
   - Optionally set `esphome_name` to override the name the virtual ESPHome device is advertised as (defaults to the name of the first A/C).
   - Optionally set `esphome_advertise_ip` if Home Assistant can't reach this machine's own LAN IP directly (e.g. it runs on a Docker macvlan network and this server on a host/bridge network) - see [ESPHome integration](#esphome-integration) below.
   - Set `port` to the port to be used by the web server.
   - Set `log_level` to your desired verbosity level.

1. Run:
   ```bash
   docker-compose up -d
   ```
1. Check the logs and verify that everything is in shape:
   ```bash
   journalctl CONTAINER_NAME=hisense_ac
   ```

1. Profit! Add the device in Home Assistant through **Settings → Devices & Services → Add Integration → ESPHome**,
   using the server's IP address and `esphome_port` (no encryption key needed - see
   [ESPHome integration](#esphome-integration) below).
   [SmartThings] requires manual setup instead, see [SmartThings integration](#smartthings-integration) below.

## Run the A/C control server manually

Use this method if the docker setup above does not work for you.

1. Download and install aircon module:
   ```bash
   python3.14 -m pip install .
   ```

1. Run discovery command to fetch the LAN keys that will allow connecting to the A/C. Pass it your login credentials, as well as the code for your app from the list below:

   For example:
   ```bash
   python3.14 -m aircon discovery tornado-us foo@example.com my_pass
   ```
   The CLI will generate a config file for each A/C, that needs to be passed to the A/C
   control server below. You can select the A/C that the config is generated for by
   setting the `--device` flag to the device name you configured in the app.

* Note: _To update the server from head, run `git pull` on the repository and
  run setup. You may also need to re-run discovery._

1. Test out that you can run the server, e.g.:
   ```bash
   python3.14 -m aircon run --port 8888 --config config.json
   ```
   Parameters:
   - `--port` or `-p` - Port for the web server.
   - `--config` - The config file with the credentials to connect to the A/C.
   - `--esphome_port` - Port for the ESPHome native API. Default is 6053. Set to 0 to disable.
   - `--esphome_web_port` - Port for the ESPHome debug web dashboard. Default is 6052.
   - `--esphome_name` - Name to advertise the virtual ESPHome device as. Defaults to the name of the first configured A/C.
   - `--esphome_advertise_ip` - IP address to advertise the ESPHome device as over Zeroconf/mDNS, if it differs from what this machine would pick on its own. See [ESPHome integration](#esphome-integration) below.
   - `--log_level` - The minimal log level to send to syslog. Default is WARNING.
   - `--local_ip` - The local IP address to report to the AC unit(s) as target server. Useful in case the server running this application has multiple IP addresses (e.g. in multiple VLANs), since some/most(?) AC units will refuse to report to an IP address outside of their subnet.
1. Access e.g. using curl:
   ```bash
   curl -ik 'http://localhost:8888/hisense/status'
   curl -ik 'http://localhost:8888/hisense/command?property=t_power&value=ON'
   ```

### Multiple Air Conditioners
In order to use with multiple Air Conditioners, simply add multiple --config params. Each A/C is
exposed as its own climate entity (named after the A/C's name in the app) under the single
virtual ESPHome device.

### Run as a service
Assuming your username is "pi"

1. Create a dedicated directory for the script files, and move the files to it.
   Pass the ownership to root. e.g.:
   ```bash
   sudo mkdir /opt/hisense
   sudo mv config*.json /opt/hisense
   sudo chown pi:pi /opt/hisense/*
   ```
1. Create a service configuration file (as root), e.g. `/lib/systemd/system/hisense.service`:
   ```INI
   [Unit]
   Description=Hisense A/C server
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3.14 -m aircon run --port 8888 --config config.json
   WorkingDirectory=/opt/hisense
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```
1. Link to it from `/etc/systemd/system/`:
   ```bash
   sudo ln -s /lib/systemd/system/hisense.service /etc/systemd/system/multi-user.target.wants/hisense.service
   ```
1. Enable and start the new service:
   ```bash
   sudo systemctl enable hisense.service
   sudo systemctl start hisense.service
   ```
1. [HomeAssistant] should now be able to find the A/C(s) through its ESPHome integration, see
   [ESPHome integration](#esphome-integration) below.

## ESPHome integration

Each configured A/C shows up in Home Assistant as a device with the following entities:

| Entity                  | Type            | Hisense property                                    | Notes                                                                                          |
|--------------------------|-----------------|-------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| *(the A/C's own name)*   | `climate`       | `t_power`, `t_work_mode`, `t_temp`, `f_temp_in`, `t_fan_speed`, `t_fan_power`, `t_fan_leftright` | HVAC modes off/heat/cool/dry/fan_only/auto; fan speed is a *custom fan mode* using the A/C's own names (`auto`/`lower`/`low`/`medium`/`high`/`higher`) instead of being lossily mapped onto ESPHome's fixed fan enum; swing mode (off/vertical/horizontal/both) drives the vertical and horizontal air flow flaps together |
| … Backlight              | `switch`        | `t_backlight`                                        | display on/off |
| … Eco Mode               | `switch`        | `t_eco`                                              | |
| … Quiet Mode             | `switch`        | `t_fan_mute`                                         | |
| … Filter Clean Required  | `binary_sensor` | `f_filterclean`                                      | |
| … Humidity               | `sensor`        | `f_humidity`                                         | some A/C models never report a real value here (always 0) - that's the hardware, not this integration |
| … Voltage                | `sensor`        | `f_voltage`                                          | same caveat as Humidity |

Not exposed yet: sleep mode (`t_sleep`), the fast/eight-heat modes (`t_temp_heatcold`, `t_temp_eight`), and the raw fault-code flags (`f_e_*`). Use the [HTTP API](#run-the-a-c-control-server-manually) directly for those in the meantime, or open an issue/PR.

To add the device in Home Assistant: **Settings → Devices & Services → Add Integration →
ESPHome**, then enter the server's IP address and the `esphome_port` (`6053` by default). No
encryption key is needed - `aioesphomeserver` only supports the plaintext API for now.

`aioesphomeserver` is alpha-quality, and its connection handling has been observed to wedge after
a burst of simultaneous reconnects (e.g. right after Home Assistant itself restarts and every
ESPHome device it knows about tries to reconnect at once) - the process stays up and the port
stays open, but new clients never get past the initial handshake. The `docker-compose.yaml` here
includes a Docker `HEALTHCHECK` that actually performs that handshake, plus an `autoheal` sidecar
that restarts `hisense_ac` automatically when it fails (Docker's own restart policy only reacts to
the process exiting, not to a failed healthcheck). This has been enough in practice to recover
within about 30 seconds. Note that `autoheal` needs access to the Docker socket to do this, which
in general grants a container fairly broad control over the host's other containers - acceptable
for a home setup, worth knowing about if this runs anywhere more sensitive.

If Home Assistant reports the device as unavailable shortly after adding it (even though the
initial connection worked), the device's Zeroconf/mDNS self-announcement is probably pointing
Home Assistant back at an address it can't actually reach - most commonly because Home Assistant
runs on a Docker macvlan network (its own direct LAN IP) while this server runs with
`network_mode: host`, and containers on a macvlan network generally can't reach the Docker host's
own IP. Find an address Home Assistant *can* reach this server through (e.g. the gateway IP of
whatever bridge network Home Assistant is also attached to) and set it as `esphome_advertise_ip`
in `options.json`, then remove and re-add the integration in Home Assistant.

## SmartThings integration

You will need a groovy script to enable SmartThings integration with the Air Conditioner, through
the control server above. It currently implements the main functionality (turn on/off, AC mode,
fan speed, dimmer etc.).

The groovy file is available [here](devicetypes/deiger/hisense-air-conditioner.src/hisense-air-conditioner.groovy), for download and installation through the [Groovy IDE](https://graph.api.smartthings.com). As I'm continuously improving this script, it would be more efficient to use the IDE's github integration, in order to stay up-to-date.

## Available Properties

Listed here are the properties available through the [HTTP API](#run-the-a-c-control-server-manually)
for standard A/Cs (FGLair and humidifers have different properties):

| Property         | Read Only | Values                                 | Comment                                                                  |
|------------------|-----------|----------------------------------------|--------------------------------------------------------------------------|
| f_electricity    | x         | Integer                                |                                                                          |
| f_e_arkgrille    | x         | 0, 1                                   | Alarm from cabinet grille protection                                     |
| f_e_incoiltemp   | x         | 0, 1                                   | Indoor coil temperature sensor in fault                                  |
| f_e_incom        | x         | 0, 1                                   | Indoor and outdoor communication in fault                                |
| f_e_indisplay    | x         | 0, 1                                   | Communication faulty between indoor control panel and display panel      |
| f_e_ineeprom     | x         | 0, 1                                   | Error in EEPROM of indoor control panel                                  |
| f_e_inele        | x         | 0, 1                                   | Communication faulty between indoor control panel and indoor power panel |
| f_e_infanmotor   | x         | 0, 1                                   | Indoor fan motor operation abnormal                                      |
| f_e_inhumidity   | x         | 0, 1                                   | Indoor humidity sensor in fault                                          |
| f_e_inkeys       | x         | 0, 1                                   | Communication faulty between indoor control panel and keyboard plate     |
| f_e_inlow        | x         | 0, 1                                   |                                                                          |
| f_e_intemp       | x         | 0, 1                                   | Indoor temperature sensor in fault                                       |
| f_e_invzero      | x         | 0, 1                                   | Fault found from indoor voltage crossing zero detection                  |
| f_e_outcoiltemp  | x         | 0, 1                                   | The temperature sensor in outdoor coil faulty                            |
| f_e_outeeprom    | x         | 0, 1                                   | Outdoor EEPROM error                                                     |
| f_e_outgastemp   | x         | 0, 1                                   | Exhaust temperature sensor faulty                                        |
| f_e_outmachine2  | x         | 0, 1                                   |                                                                          |
| f_e_outmachine   | x         | 0, 1                                   |                                                                          |
| f_e_outtemp      | x         | 0, 1                                   | Outdoor ambient temperature sensor faulty                                |
| f_e_outtemplow   | x         | 0, 1                                   |                                                                          |
| f_e_push         | x         | 0, 1                                   | Communication faulty between WiFi control panel and indoor control panel |
| f_filterclean    | x         | 0, 1                                   | Does the filter require cleaning                                         |
| f_humidity       | x         | Integer                                | Relative humidity percent                                                |
| f_power_display  | x         | 0, 1                                   |                                                                          |
| f_temp_in        | x         | Decimal                                | Environment temperature in Fahrenheit                                    |
| f_voltage        | x         | Integer                                |                                                                          |
| t_backlight      |           | ON, OFF                                | Turn the display on/off                                                  |
| t_device_info    |           | 0, 1                                   |                                                                          |
| t_display_power  |           | 0, 1                                   |                                                                          |
| t_eco            |           | OFF, ON                                | Economy mode                                                             |
| t_fan_leftright  |           | OFF, ON                                | Horizontal air flow                                                      |
| t_fan_mute       |           | OFF, ON                                | Quite mode                                                               |
| t_fan_power      |           | OFF, ON                                | Vertical air flow                                                        |
| t_fan_speed      |           | AUTO, LOWER, LOW, MEDIUM, HIGH, HIGHER | Fan Speed                                                                |
| t_ftkt_start     |           | Integer                                |                                                                          |
| t_power          |           | OFF, ON                                | Power                                                                    |
| t_run_mode       |           | OFF, ON                                | Double frequency                                                         |
| t_setmulti_value |           | Integer                                |                                                                          |
| t_sleep          |           | STOP, ONE, TWO, THREE, FOUR            | Sleep mode                                                               |
| t_temp           |           | Integer                                | Temperature in Fahrenheit                                                |
| t_temptype       |           | CELSIUS, FAHRENHEIT                    | Displayed temperature unit                                               |
| t_temp_eight     |           | OFF, ON                                | Eight heat mode                                                          |
| t_temp_heatcold  |           | OFF, ON                                | Fast cool heat                                                           |
| t_work_mode      |           | FAN, HEAT, COOL, DRY, AUTO             | Work mode                                                                |

## Code Contributions
Pull requests are always welcome.

Please use [YAPF] with the style config defined here to style your code.
Single quotes are used throughout the code-base. Unfortunately YAPF still doesn't support mandating this (support exists in the [fixers branch](https://github.com/google/yapf/tree/fixers)), so please be mindful.

[HomeAssistant]: https://www.home-assistant.io/
[ESPHome]: https://esphome.io/
[aioesphomeserver]: https://github.com/peterkeen/aioesphomeserver
[SmartThings]: https://www.smartthings.com/
[YAPF]: https://github.com/google/yapf

Читати цей документ українською: [README.uk.md](README.uk.md).
