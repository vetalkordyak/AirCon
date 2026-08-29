import asyncio
import logging
from typing import List, Optional

from aioesphomeapi.api_pb2 import ClimateCommandRequest, ClimateMode, ListEntitiesClimateResponse
from aioesphomeserver import ClimateEntity
from aioesphomeserver import Device as EspHomeDevice

from . import __version__
from .aircon import AcDevice, Device

logger = logging.getLogger(__name__)

# AcDevice.work_modes are the lower-case strings from aircon.py, mapped onto
# the ESPHome protocol's ClimateMode enum. There's no ESPHome equivalent for
# "off" as a work mode (it's controlled via t_power on the AC side), but it's
# still a valid Home Assistant climate mode, so it's kept in both directions.
_WORK_MODE_TO_CLIMATE_MODE = {
    'off': ClimateMode.CLIMATE_MODE_OFF,
    'fan_only': ClimateMode.CLIMATE_MODE_FAN_ONLY,
    'heat': ClimateMode.CLIMATE_MODE_HEAT,
    'cool': ClimateMode.CLIMATE_MODE_COOL,
    'dry': ClimateMode.CLIMATE_MODE_DRY,
    'auto': ClimateMode.CLIMATE_MODE_AUTO,
}
_CLIMATE_MODE_TO_WORK_MODE = {v: k for k, v in _WORK_MODE_TO_CLIMATE_MODE.items()}

# Properties that, when changed on the physical A/C, should be reflected onto
# the ESPHome climate entity.
_RELEVANT_PROPERTIES = frozenset({'t_power', 't_work_mode', 't_temp', 'f_temp_in', 't_fan_speed'})


def _format_mac(mac_address: str) -> str:
  mac = mac_address.replace(':', '').lower()
  return ':'.join(mac[i:i + 2] for i in range(0, len(mac), 2))


def _to_celsius(device: AcDevice, value: Optional[float]) -> Optional[float]:
  if value is None:
    return None
  return round((value - 32) / 1.8, 1) if device.is_fahrenheit else float(value)


def _from_celsius(device: AcDevice, value: float) -> int:
  return round(value * 1.8 + 32) if device.is_fahrenheit else round(value)


class HisenseClimateEntity(ClimateEntity):
  """Exposes a Hisense `AcDevice` as an ESPHome native API climate entity.

  `aioesphomeserver`'s ClimateEntity doesn't yet wire up incoming commands
  (there's no `handle()` override for ClimateCommandRequest) nor custom fan
  modes, so both are added here rather than relying on the base class.
  """

  def __init__(self, hisense_device: AcDevice, **kwargs):
    self._device = hisense_device
    work_modes = [m for m in hisense_device.work_modes if m in _WORK_MODE_TO_CLIMATE_MODE]
    fan_modes = list(hisense_device.fan_modes) if 'fan_speed' in hisense_device.topics else []
    super().__init__(
        name=hisense_device.name,
        supported_modes=[_WORK_MODE_TO_CLIMATE_MODE[m] for m in work_modes],
        visual_min_temperature=61.0 if hisense_device.is_fahrenheit else 16.0,
        visual_max_temperature=86.0 if hisense_device.is_fahrenheit else 30.0,
        visual_target_temperature_step=1.0,
        supports_current_temperature='env_temp' in hisense_device.topics,
        **kwargs,
    )
    self.supported_custom_fan_modes = fan_modes
    self.custom_fan_mode = fan_modes[0] if fan_modes else None
    hisense_device.add_property_change_listener(self._on_hisense_property_change)

  async def build_list_entities_response(self):
    # Not calling super() here: aioesphomeapi has, at various points, both
    # added fields ClimateEntity doesn't know about yet (supported_custom_fan_modes)
    # and dropped ones it still tries to set (unique_id was removed from this
    # message at some point after aioesphomeserver was written against it).
    # Building the kwargs ourselves and filtering to whatever the installed
    # protobuf schema actually declares keeps this working across versions.
    kwargs = dict(
        object_id=self.object_id,
        key=self.key,
        name=self.name,
        unique_id=self.unique_id,
        supported_modes=self.supported_modes,
        visual_min_temperature=self.visual_min_temperature,
        visual_max_temperature=self.visual_max_temperature,
        visual_target_temperature_step=self.visual_target_temperature_step,
        supports_two_point_target_temperature=self.supports_two_point_target_temperature,
        supported_fan_modes=self.supported_fan_modes,
        supported_custom_fan_modes=self.supported_custom_fan_modes,
        supported_swing_modes=self.supported_swing_modes,
        supports_current_temperature=self.supports_current_temperature,
        supports_action=self.supports_action,
        supports_current_humidity=self.supports_current_humidity,
        supports_target_humidity=self.supports_target_humidity,
        visual_min_humidity=self.visual_min_humidity,
        visual_max_humidity=self.visual_max_humidity,
        supported_presets=self.supported_presets,
    )
    valid_fields = {f.name for f in ListEntitiesClimateResponse.DESCRIPTOR.fields}
    return ListEntitiesClimateResponse(**{k: v for k, v in kwargs.items() if k in valid_fields})

  async def build_state_response(self):
    response = await super().build_state_response()
    if self.custom_fan_mode is not None:
      response.custom_fan_mode = self.custom_fan_mode
    return response

  async def can_handle(self, key, message):
    if key == 'client_request':
      return isinstance(message, ClimateCommandRequest) and message.key == self.key
    return await super().can_handle(key, message)

  async def handle(self, key, message):
    if key != 'client_request':
      return await super().handle(key, message)
    await self._apply_command(message)

  async def _apply_command(self, command: ClimateCommandRequest) -> None:
    device = self._device
    try:
      if command.has_mode:
        work_mode = _CLIMATE_MODE_TO_WORK_MODE.get(command.mode)
        if work_mode is not None:
          device.queue_command('t_work_mode', work_mode.upper())
      if command.has_target_temperature:
        device.queue_command('t_temp', str(_from_celsius(device, command.target_temperature)))
      if command.has_custom_fan_mode and command.custom_fan_mode:
        device.queue_command('t_fan_speed', command.custom_fan_mode.upper())
    except Exception:
      logger.exception('Failed to apply ESPHome command to %s: %s', device.mac_address, command)
    # The actual state is only updated once the A/C reports the new property
    # value back (via _on_hisense_property_change), same as the old MQTT
    # bridge used to work.

  def _on_hisense_property_change(self, mac_address: str, prop_name: str, value, retain=False):
    if mac_address != self._device.mac_address or prop_name not in _RELEVANT_PROPERTIES:
      return
    asyncio.get_running_loop().create_task(self._sync_state())

  async def _sync_state(self) -> None:
    device = self._device
    power = device.get_power()
    if power is not None and power.name == 'OFF':
      self.mode = ClimateMode.CLIMATE_MODE_OFF
    else:
      work_mode = device.get_work_mode()
      if work_mode is not None:
        self.mode = _WORK_MODE_TO_CLIMATE_MODE.get(work_mode.name.lower(), self.mode)

    target_temp = device.get_temperature()
    if target_temp is not None:
      self.target_temperature = _to_celsius(device, target_temp)

    if self.supports_current_temperature:
      env_temp = device.get_env_temp()
      if env_temp is not None:
        self.current_temperature = _to_celsius(device, env_temp)

    if self.supported_custom_fan_modes:
      fan_speed = device.get_fan_speed()
      if fan_speed is not None:
        self.custom_fan_mode = fan_speed.name.lower()

    await self.notify_state_change()


async def run_esphome_server(devices: List[Device], api_port: int, web_port: int,
                             name: Optional[str] = None) -> None:
  """Exposes all supported `devices` as climate entities of a single virtual
  ESPHome node, so they show up in Home Assistant through the ESPHome
  integration instead of MQTT."""
  ac_devices = [d for d in devices if isinstance(d, AcDevice)]
  skipped = [d.name for d in devices if d not in ac_devices]
  if skipped:
    logger.warning('ESPHome bridge only supports A/C devices for now, skipping: %s', skipped)
  if not ac_devices:
    logger.warning('No supported devices to expose over the ESPHome API.')
    return

  primary = ac_devices[0]
  esp_device = EspHomeDevice(
      name=name or primary.name,
      mac_address=_format_mac(primary.mac_address),
      model=primary.model,
      project_name='AirCon',
      project_version=__version__,
      manufacturer=f'Hisense ({primary.app})',
  )
  entities = [HisenseClimateEntity(device) for device in ac_devices]
  for entity in entities:
    esp_device.add_entity(entity)
  for entity in entities:
    # Pull whatever the device already knows (even if that's just its
    # power-on defaults) rather than showing the ESPHome library's generic
    # visual_min_temperature/OFF placeholders until the next property change.
    await entity._sync_state()

  logger.info('Starting ESPHome native API on port %d (web dashboard on %d) as "%s"', api_port,
             web_port, esp_device.name)
  await esp_device.run(api_port=api_port, web_port=web_port)
