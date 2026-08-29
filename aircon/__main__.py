import aiohttp
from aiohttp import web
import argparse
import asyncio
import base64
from http import HTTPStatus
from http.client import HTTPConnection, InvalidURL
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import logging.handlers
import os
from retry import retry
import signal
import socket
import sys
try:
  from systemd.journal import JournalHandler
except:
  JournalHandler = None
import textwrap
import threading
import time
import _thread
from urllib.parse import parse_qs, urlparse, ParseResult

from .app_mappings import SECRET_MAP
from .config import Config
from .error import Error
from .aircon import Device
from .discovery import perform_discovery
from .esphome_server import run_esphome_server
from .notifier import Notifier
from .query_handlers import QueryHandlers


async def query_status_device(device: Device):
  _STATUS_UPDATE_INTERVAL = 600.0
  _WAIT_FOR_EMPTY_QUEUE = 10.0
  while True:
    # In case the AC is stuck, and not fetching commands, avoid flooding
    # the queue with status updates.
    while device.commands_queue.qsize() > 10:
      await asyncio.sleep(_WAIT_FOR_EMPTY_QUEUE)
    device.queue_status()
    await asyncio.sleep(_STATUS_UPDATE_INTERVAL)


async def query_status_worker(devices: [Device]):
  await asyncio.wait([asyncio.create_task(query_status_device(device)) for device in devices])


def ParseArguments() -> argparse.Namespace:
  """Parse command line arguments."""
  arg_parser = argparse.ArgumentParser(description='JSON server for HiSense air conditioners.',
                                       allow_abbrev=False)
  arg_parser.add_argument('--log_level',
                          default='WARNING',
                          choices={'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'},
                          help='Minimal log level.')
  subparsers = arg_parser.add_subparsers(dest='cmd', help='Determines what server should do')
  subparsers.required = True

  parser_run = subparsers.add_parser('run', help='Runs the server to control the device')
  parser_run.add_argument('-p', '--port', required=True, type=int, help='Port for the server.')
  parser_run.add_argument('--local_ip',
                          required=False,
                          default=None,
                          help='The local IP address to report to the AC unit(s) as target server. Useful in case the server running this application has multiple IP addresses (e.g. in multiple VLANs), since some/most(?) AC units will refuse to report to an IP address outside of their subnet.')
  group_device = parser_run.add_argument_group('Device', 'Arguments that are related to the device')
  group_device.add_argument('--config', required=True, action='append', help='LAN Config file.')
  group_device.add_argument('--type',
                            required=False,
                            action='append',
                            choices={'ac', 'fgl', 'fgl_b', 'humidifier'},
                            help='Device type. Deprecated, now decided based on OEM model.')

  group_esphome = parser_run.add_argument_group(
      'ESPHome', 'Settings for exposing the A/C(s) as an ESPHome native API device, '
      'for auto-discovery by HomeAssistant\'s ESPHome integration.')
  group_esphome.add_argument('--esphome_port',
                             type=int,
                             default=6053,
                             help='Port for the ESPHome native API. Set to 0 to disable.')
  group_esphome.add_argument('--esphome_web_port',
                             type=int,
                             default=6052,
                             help='Port for the ESPHome debug web dashboard.')
  group_esphome.add_argument('--esphome_name',
                             default=None,
                             help='Name to advertise the virtual ESPHome device as. '
                             'Defaults to the name of the first configured A/C.')

  parser_discovery = subparsers.add_parser('discovery', help='Runs the device discovery')
  parser_discovery.add_argument('app', choices=set(SECRET_MAP), help='The app used for the login.')
  parser_discovery.add_argument('user', help='Username for the app login.')
  parser_discovery.add_argument('passwd', help='Password for the app login.')
  parser_discovery.add_argument('-d',
                                '--device',
                                default=None,
                                help='Device name to fetch data for. If not set, takes all.')
  parser_discovery.add_argument('--prefix',
                                required=False,
                                default='config_',
                                help='Config file prefix.')
  parser_discovery.add_argument('--properties',
                                action='store_true',
                                help='Fetch the properties for the device.')
  return arg_parser.parse_args()


def setup_logger(log_level, use_stderr=False):
  if use_stderr or os.environ.get('PLATFORM') == 'docker':
    logging_handler = logging.StreamHandler(sys.stderr)
  elif JournalHandler:
    logging_handler = JournalHandler()
  # Fallbacks when JournalHandler isn't available.
  elif sys.platform == 'linux':
    logging_handler = logging.handlers.SysLogHandler(address='/dev/log')
  elif sys.platform == 'darwin':
    logging_handler = logging.handlers.SysLogHandler(address='/var/run/syslog')
  elif sys.platform.lower() in ['windows', 'win32']:
    logging_handler = logging.handlers.SysLogHandler()
  else:  # Unknown platform, revert to stderr
    logging_handler = logging.StreamHandler(sys.stderr)
  logging_handler.setFormatter(
      logging.Formatter(fmt='{levelname[0]}{asctime}.{msecs:03.0f}  '
                        '{filename}:{lineno}] {message}',
                        datefmt='%m%d %H:%M:%S',
                        style='{'))
  logger = logging.getLogger()
  logger.setLevel(log_level)
  logger.addHandler(logging_handler)


async def setup_and_run_http_server(parsed_args, devices: [Device]):
  query_handlers = QueryHandlers(devices)
  app = web.Application()
  app.add_routes([
      web.get('/hisense/status', query_handlers.get_status_handler),
      web.get('/hisense/command', query_handlers.queue_command_handler),
      web.post('/local_lan/key_exchange.json', query_handlers.key_exchange_handler),
      web.get('/local_lan/commands.json', query_handlers.command_handler),
      web.post('/local_lan/property/datapoint.json', query_handlers.property_update_handler),
      web.post('/local_lan/property/datapoint/ack.json', query_handlers.property_update_handler),
      web.post('/local_lan/node/property/datapoint.json', query_handlers.property_update_handler),
      web.post('/local_lan/node/property/datapoint/ack.json',
               query_handlers.property_update_handler),
      # TODO: Handle these if needed.
      # '/local_lan/node/conn_status.json': query_handlers.connection_status_handler,
      # '/local_lan/connect_status': query_handlers.module_request_handler,
      # '/local_lan/status.json': query_handlers.setup_device_details_handler,
      # '/local_lan/wifi_scan.json': query_handlers.module_request_handler,
      # '/local_lan/wifi_scan_results.json': query_handlers.module_request_handler,
      # '/local_lan/wifi_status.json': query_handlers.module_request_handler,
      # '/local_lan/regtoken.json': query_handlers.module_request_handler,
      # '/local_lan/wifi_stop_ap.json': query_handlers.module_request_handler
  ])
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, port=parsed_args.port)
  await site.start()


async def run(parsed_args):
  notifier = Notifier(parsed_args.port, parsed_args.local_ip)
  devices = []
  for i in range(len(parsed_args.config)):
    with open(parsed_args.config[i], 'rb') as f:
      config = json.load(f)
    device = Device.create(config, notifier.notify)
    notifier.register_device(device)
    devices.append(device)

  tasks = [setup_and_run_http_server(parsed_args, devices), query_status_worker(devices)]
  if parsed_args.esphome_port:
    tasks.append(
        run_esphome_server(devices, parsed_args.esphome_port, parsed_args.esphome_web_port,
                           parsed_args.esphome_name))

  async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(connect=5.0)) as session:
    await asyncio.gather(*tasks, notifier.start(session))


def _escape_name(name: str):
  safe_name = name.replace(' ', '_').lower()
  return ''.join(x for x in safe_name if x.isalnum())


async def discovery(parsed_args):
  async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(connect=5.0)) as session:
    try:
      all_configs = await perform_discovery(session, parsed_args.app, parsed_args.user,
                                            parsed_args.passwd, parsed_args.device,
                                            parsed_args.properties)
    except Exception as e:
      print(f'Error occurred:\n{e!r}')
      sys.exit(1)

  for config in all_configs:
    properties_text = ''
    if 'properties' in config.keys():
      properties_text = f'Properties:\n{json.dumps(config["properties"], indent=2)}'
    print(
        textwrap.dedent(f"""Device {config['product_name']} has:
                              IP address: {config['lan_ip']}
                              lanip_key: {config['lanip_key']}
                              lanip_key_id: {config['lanip_key_id']}
                              {properties_text}
                              """))

    file_content = {
        'name': config['product_name'],
        'app': parsed_args.app,
        'model': config['oem_model'],
        'sw_version': config['sw_version'],
        'dsn': config['dsn'],
        'temp_type': config['temp_type'],
        'mac_address': config['mac'],
        'ip_address': config['lan_ip'],
        'lanip_key': config['lanip_key'],
        'lanip_key_id': config['lanip_key_id'],
    }
    with open(parsed_args.prefix + _escape_name(config['product_name']) + '.json', 'w') as f:
      f.write(json.dumps(file_content))


if __name__ == '__main__':
  parsed_args = ParseArguments()  # type: argparse.Namespace

  if parsed_args.cmd == 'run':
    setup_logger(parsed_args.log_level)
    asyncio.run(run(parsed_args))
  elif parsed_args.cmd == 'discovery':
    setup_logger(parsed_args.log_level, use_stderr=True)
    asyncio.run(discovery(parsed_args))
