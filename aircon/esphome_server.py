import asyncio
import logging
from typing import List, Optional

from aioesphomeapi.api_pb2 import (
    ClimateCommandRequest,
    ClimateMode,
    ClimateSwingMode,
    ListEntitiesBinarySensorResponse,
    ListEntitiesClimateResponse,
    ListEntitiesSensorResponse,
    ListEntitiesSwitchResponse,
    SensorStateClass,
    SwitchCommandRequest,
)
from aioesphomeserver import BinarySensorEntity, ClimateEntity, SensorEntity, SwitchEntity
from aioesphomeserver import Device as EspHomeDevice

from . import __version__
from .aircon import AcDevice, Device
from .properties import AirFlow, AirFlowState

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

_AIRFLOW_STATE_TO_SWING_MODE = {
    AirFlowState.OFF: ClimateSwingMode.CLIMATE_SWING_OFF,
    AirFlowState.VERTICAL_ONLY: ClimateSwingMode.CLIMATE_SWING_VERTICAL,
    AirFlowState.HORIZONTAL_ONLY: ClimateSwingMode.CLIMATE_SWING_HORIZONTAL,
    AirFlowState.VERTICAL_AND_HORIZONTAL: ClimateSwingMode.CLIMATE_SWING_BOTH,
}
_SWING_MODE_TO_AIRFLOW_STATE = {v: k for k, v in _AIRFLOW_STATE_TO_SWING_MODE.items()}

# Properties that, when changed on the physical A/C, should be reflected onto
# the ESPHome climate entity.
_RELEVANT_CLIMATE_PROPERTIES = frozenset(
    {'t_power', 't_work_mode', 't_temp', 'f_temp_in', 't_fan_speed', 't_fan_power',
     't_fan_leftright'})


def _format_mac(mac_address: str) -> str:
  mac = mac_address.replace(':', '').lower()
  return ':'.join(mac[i:i + 2] for i in range(0, len(mac), 2))


def _to_celsius(device: AcDevice, value: Optional[float]) -> Optional[float]:
  if value is None:
    return None
  return round((value - 32) / 1.8, 1) if device.is_fahrenheit else float(value)


def _from_celsius(device: AcDevice, value: float) -> int:
  return round(value * 1.8 + 32) if device.is_fahrenheit else round(value)


def _filtered(response_cls, **kwargs):
  """Builds a protobuf message from `kwargs`, dropping anything the message
  doesn't actually declare a field for.

  aioesphomeserver's entities are written against a slightly different
  aioesphomeapi protobuf schema than what ends up installed (its own
  dependency floor already crashes on some of these) - some fields it sets
  no longer exist (e.g. unique_id on List*Response messages), and it doesn't
  yet set some fields that do exist (e.g. supported_custom_fan_modes). This
  keeps entity registration working across schema drift either way.
  """
  valid_fields = {f.name for f in response_cls.DESCRIPTOR.fields}
  return response_cls(**{k: v for k, v in kwargs.items() if k in valid_fields})


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
    supports_swing = 'swing_mode' in hisense_device.topics and 'swing_horizontal_mode' in hisense_device.topics
    super().__init__(
        name=hisense_device.name,
        supported_modes=[_WORK_MODE_TO_CLIMATE_MODE[m] for m in work_modes],
        visual_min_temperature=61.0 if hisense_device.is_fahrenheit else 16.0,
        visual_max_temperature=86.0 if hisense_device.is_fahrenheit else 30.0,
        visual_target_temperature_step=1.0,
        supports_current_temperature='env_temp' in hisense_device.topics,
        supports_swing_mode=supports_swing,
        supported_swing_modes=list(_SWING_MODE_TO_AIRFLOW_STATE) if supports_swing else [],
        **kwargs,
    )
    self.supported_custom_fan_modes = fan_modes
    self.custom_fan_mode = fan_modes[0] if fan_modes else None
    hisense_device.add_property_change_listener(self._on_hisense_property_change)

  async def build_list_entities_response(self):
    return _filtered(
        ListEntitiesClimateResponse,
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
        supports_swing_mode=self.supports_swing_mode,
        supported_swing_modes=self.supported_swing_modes,
        supports_current_temperature=self.supports_current_temperature,
        supports_action=self.supports_action,
        supports_current_humidity=self.supports_current_humidity,
        supports_target_humidity=self.supports_target_humidity,
        visual_min_humidity=self.visual_min_humidity,
        visual_max_humidity=self.visual_max_humidity,
        supported_presets=self.supported_presets,
    )

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
      if command.has_swing_mode:
        airflow_state = _SWING_MODE_TO_AIRFLOW_STATE.get(command.swing_mode)
        if airflow_state is not None:
          # Not using AcDevice.set_swing(): it (like the other set_* control_value
          # helpers) unconditionally does `control & mask`, which crashes with a
          # TypeError if t_control_value hasn't been reported yet (its default is
          # None, not 0). queue_command() guards against that itself, so drive
          # the two independent properties directly instead.
          vertical_on = airflow_state in (AirFlowState.VERTICAL_ONLY,
                                          AirFlowState.VERTICAL_AND_HORIZONTAL)
          horizontal_on = airflow_state in (AirFlowState.HORIZONTAL_ONLY,
                                            AirFlowState.VERTICAL_AND_HORIZONTAL)
          device.queue_command('t_fan_power', 'ON' if vertical_on else 'OFF')
          device.queue_command('t_fan_leftright', 'ON' if horizontal_on else 'OFF')
    except Exception:
      logger.exception('Failed to apply ESPHome command to %s: %s', device.mac_address, command)
    # The actual state is only updated once the A/C reports the new property
    # value back (via _on_hisense_property_change), same as the old MQTT
    # bridge used to work.

  def _on_hisense_property_change(self, mac_address: str, prop_name: str, value, retain=False):
    if mac_address != self._device.mac_address or prop_name not in _RELEVANT_CLIMATE_PROPERTIES:
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

    if self.supports_swing_mode:
      vertical = device.get_fan_vertical()
      horizontal = device.get_fan_horizontal()
      if vertical is not None and horizontal is not None:
        airflow_state = AirFlowState((vertical is AirFlow.ON) | ((horizontal is AirFlow.ON) << 1))
        self.swing_mode = _AIRFLOW_STATE_TO_SWING_MODE[airflow_state]

    await self.notify_state_change()


class _HisensePropertyEntityMixin:
  """Mixin for read-only aioesphomeserver entities that mirror a single
  Hisense property 1:1 (optionally through `transform`)."""

  def bind(self, hisense_device: AcDevice, prop_name: str, transform=lambda value: value):
    self._device = hisense_device
    self._prop_name = prop_name
    self._transform = transform
    hisense_device.add_property_change_listener(self._on_hisense_property_change)

  async def sync_now(self) -> None:
    value = self._device.get_property(self._prop_name)
    if value is not None:
      await self.set_state(self._transform(value))

  def _on_hisense_property_change(self, mac_address: str, prop_name: str, value, retain=False):
    if mac_address != self._device.mac_address or prop_name != self._prop_name:
      return
    asyncio.get_running_loop().create_task(self.set_state(self._transform(value)))


class HisenseSensorEntity(_HisensePropertyEntityMixin, SensorEntity):

  async def build_list_entities_response(self):
    return _filtered(
        ListEntitiesSensorResponse,
        object_id=self.object_id,
        name=self.name,
        key=self.key,
        unique_id=self.unique_id,
        icon=self.icon,
        unit_of_measurement=self.unit_of_measurement,
        accuracy_decimals=self.accuracy_decimals,
        device_class=self.device_class,
        state_class=self.state_class,
        entity_category=self.entity_category,
    )


class HisenseBinarySensorEntity(_HisensePropertyEntityMixin, BinarySensorEntity):

  async def build_list_entities_response(self):
    return _filtered(
        ListEntitiesBinarySensorResponse,
        object_id=self.object_id,
        name=self.name,
        key=self.key,
        unique_id=self.unique_id,
        device_class=self.device_class,
        icon=self.icon,
        entity_category=self.entity_category,
    )


class HisenseSwitchEntity(_HisensePropertyEntityMixin, SwitchEntity):
  """A switch that mirrors a boolean OFF/ON Hisense property.

  Unlike the read-only sensor/binary_sensor mixins above, this also accepts
  commands from Home Assistant: SwitchEntity.handle() already routes
  SwitchCommandRequest into set_state(), so it's overridden here to queue the
  command on the physical A/C instead of just flipping a local flag. The
  switch only reflects the real state once the A/C acks it, same as the
  climate entity.
  """

  async def build_list_entities_response(self):
    return _filtered(
        ListEntitiesSwitchResponse,
        object_id=self.object_id,
        key=self.key,
        name=self.name,
        unique_id=self.unique_id,
        icon=self.icon,
        entity_category=self.entity_category,
        device_class=self.device_class,
        assumed_state=self.assumed_state,
    )

  async def can_handle(self, key, message):
    if key == 'client_request':
      return isinstance(message, SwitchCommandRequest) and message.key == self.key
    return await super().can_handle(key, message)

  async def handle(self, key, message):
    if key != 'client_request':
      return await super().handle(key, message)
    self._device.queue_command(self._prop_name, 'ON' if message.state else 'OFF')


def _add_diagnostic_entities(esp_device: EspHomeDevice, device: AcDevice) -> None:
  """Adds the read-only sensors and simple ON/OFF switches the Hisense API
  exposes beyond the core climate properties (humidity, voltage, filter
  status, backlight/eco/quiet toggles)."""
  prefix = f'{device.name} '

  humidity = HisenseSensorEntity(name=f'{prefix}Humidity', unit_of_measurement='%',
                                 accuracy_decimals=0, device_class='humidity',
                                 state_class=SensorStateClass.STATE_CLASS_MEASUREMENT)
  humidity.bind(device, 'f_humidity')
  esp_device.add_entity(humidity)

  voltage = HisenseSensorEntity(name=f'{prefix}Voltage', unit_of_measurement='V',
                                accuracy_decimals=0, device_class='voltage',
                                state_class=SensorStateClass.STATE_CLASS_MEASUREMENT)
  voltage.bind(device, 'f_voltage')
  esp_device.add_entity(voltage)

  filter_clean = HisenseBinarySensorEntity(name=f'{prefix}Filter Clean Required',
                                           device_class='problem')
  filter_clean.bind(device, 'f_filterclean', transform=bool)
  esp_device.add_entity(filter_clean)

  backlight = HisenseSwitchEntity(name=f'{prefix}Backlight')
  backlight.bind(device, 't_backlight', transform=lambda v: v.name == 'ON')
  esp_device.add_entity(backlight)

  eco = HisenseSwitchEntity(name=f'{prefix}Eco Mode')
  eco.bind(device, 't_eco', transform=lambda v: v.name == 'ON')
  esp_device.add_entity(eco)

  quiet = HisenseSwitchEntity(name=f'{prefix}Quiet Mode')
  quiet.bind(device, 't_fan_mute', transform=lambda v: v.name == 'ON')
  esp_device.add_entity(quiet)

  return [humidity, voltage, filter_clean, backlight, eco, quiet]


async def run_esphome_server(devices: List[Device], api_port: int, web_port: int,
                             name: Optional[str] = None,
                             advertise_ip: Optional[str] = None) -> None:
  """Exposes all supported `devices` as climate entities of a single virtual
  ESPHome node, so they show up in Home Assistant through the ESPHome
  integration instead of MQTT.

  `advertise_ip`, if set, overrides the address the device announces over
  Zeroconf/mDNS. This matters when the machine running this server is
  reachable from Home Assistant only through a different address than the
  one its network stack would pick on its own - e.g. Home Assistant running
  in a container on a macvlan network typically can't reach the Docker
  host's own LAN IP directly, only e.g. the bridge network gateway IP.
  Without this override, Home Assistant's ESPHome integration will
  eventually re-resolve the device to its self-reported (unreachable)
  address and mark it unavailable, even if it was reachable at setup time.
  """
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
  if advertise_ip:
    esp_device._get_ip_address = lambda: advertise_ip

  climate_entities = [HisenseClimateEntity(device) for device in ac_devices]
  diagnostic_entities = []
  for entity in climate_entities:
    esp_device.add_entity(entity)
  for device in ac_devices:
    diagnostic_entities.extend(_add_diagnostic_entities(esp_device, device))

  for entity in climate_entities:
    # Pull whatever the device already knows (even if that's just its
    # power-on defaults) rather than showing the ESPHome library's generic
    # visual_min_temperature/OFF placeholders until the next property change.
    await entity._sync_state()
  for entity in diagnostic_entities:
    await entity.sync_now()

  logger.info('Starting ESPHome native API on port %d (web dashboard on %d) as "%s"', api_port,
             web_port, esp_device.name)
  await esp_device.run(api_port=api_port, web_port=web_port)
