# Home Assistant Add-on: HiSense Air Conditioners

## Prerequisites

1. Air Conditioner with HiSense AEH-W4B1 or AEH-W4E1 WiFi module installed, or
   Fujitsu FGLair.
   These include A/Cs by multiple brands, including Beko, Westinghouse, Winia,
   Tornado, York and more.
1. The ESPHome integration set up in Home Assistant (it usually already is, if
   you have any ESPHome devices) - no MQTT broker required.

# Configuration

1. Find your application code from the list
   [here](https://github.com/vetalkordyak/AirCon#prerequisites).
1. Set the configuration as follows:
   ```yaml
   app:
     - username: App user name
       password: App password
       code: App code
   log_level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL. Default is INFO.
   esphome_port: Port for the ESPHome native API. Default is 6053.
   esphome_web_port: Port for the ESPHome debug web dashboard. Default is 6052.
   esphome_name: Name to advertise the virtual ESPHome device as. Optional, defaults to the first A/C's name.
   esphome_advertise_ip: Override for the address advertised over Zeroconf/mDNS. Optional, only needed if Home Assistant can't reach this add-on's own address directly - see the main README's "ESPHome integration" section.
   port: Port number for the web server.
   ```
   * Note: _If multiple apps are used, add them as separate values under `app`_
1. Once started, add the device in Home Assistant through **Settings → Devices
   & Services → Add Integration → ESPHome**, using this add-on's IP address
   and the `esphome_port` above.
