"""Docker HEALTHCHECK for the ESPHome native API server.

aioesphomeserver is alpha-quality: its connection handling has been observed
to wedge after a burst of simultaneous reconnects (e.g. right after Home
Assistant itself restarts and every ESPHome device it knows about tries to
reconnect at once), such that the TCP port stays open but new clients never
get past the Hello handshake. That leaves the process alive - a plain "is it
running" check wouldn't catch it - so this actually performs a minimal
handshake against the real API instead.

Exits 0 if the handshake completes, 1 otherwise (including if the ESPHome
server is disabled via esphome_port=0, in which case there's nothing to
check, so it exits 0 either way).
"""
import asyncio
import json
import os
import sys

from aioesphomeapi import APIClient

_TIMEOUT_SECONDS = 8.0


def _esphome_port() -> int:
  options_file = os.environ.get('OPTIONS_FILE')
  if options_file and os.path.exists(options_file):
    try:
      with open(options_file) as f:
        return int(json.load(f).get('esphome_port', 6053) or 0)
    except (OSError, ValueError, TypeError):
      pass
  return 6053


async def _check(port: int) -> bool:
  client = APIClient('127.0.0.1', port, None)
  try:
    await asyncio.wait_for(client.connect(), timeout=_TIMEOUT_SECONDS)
    await asyncio.wait_for(client.device_info(), timeout=_TIMEOUT_SECONDS)
    return True
  finally:
    await client.disconnect(force=True)


def main() -> int:
  port = _esphome_port()
  if port == 0:
    return 0
  try:
    ok = asyncio.run(_check(port))
  except Exception:
    ok = False
  return 0 if ok else 1


if __name__ == '__main__':
  sys.exit(main())
