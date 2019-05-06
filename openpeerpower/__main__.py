#!/usr/bin/env python3.7

"""Start OPP and use WS server to synchronizes component state across clients """
import argparse
import sys
import asyncio
import json
import logging
import websockets
import subprocess
from openpeerpower.const import (
    __version__,
    EVENT_OPENPEERPOWER_START,
    REQUIRED_PYTHON_VER
)
def validate_python() -> None:
    """Validate that the right Python version is running."""
    if sys.version_info[:3] < REQUIRED_PYTHON_VER:
        print("Open Peer Power requires at least Python {}.{}.{}".format(
            *REQUIRED_PYTHON_VER))
        sys.exit(1)

def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = argparse.ArgumentParser(
        description="Open Peer Power: Take Control of your Power.")
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Start Open Peer Power in debug mode')
    parser.add_argument(
        '--skip-pip',
        action='store_true',
        help='Skips pip install of required packages on startup')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose logging to file.")
    parser.add_argument(
        '--log-rotate-days',
        type=int,
        default=None,
        help='Enables daily log rotation and keeps up to the specified days')
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Log file to write to.  If not set, CONFIG/open-peer-power.log '
             'is used')
    parser.add_argument(
        '--log-no-color',
        action='store_true',
        help="Disable color logs")
    arguments = parser.parse_args()
    return arguments

def setup_and_run_opp() -> int:
    """Set up OPP and run."""
    from openpeerpower import core
    opp = core.OpenPeerPower()

def state_event():
    return json.dumps({'type': 'state', **STATE})


def appliance_string():
    return json.dumps(appliance_list)

def users_event():
    return json.dumps({'type': 'users', 'count': len(USERS)})

async def notify_state():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = state_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_users():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_appliances():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = appliance_string()
        await asyncio.wait([user.send(message) for user in USERS])

async def register(websocket):
    USERS.add(websocket)
#    await notify_users()

async def unregister(websocket):
    USERS.remove(websocket)
#    await notify_users()

async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket

    await register(websocket)
    try:
        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            if data['action'] == 'minus':
                STATE['value'] -= 1
                await notify_state()
            elif data['action'] == 'plus':
                STATE['value'] += 1
                await notify_state()
            else:
                logging.error(
                    "unsupported event: {}", data)
    finally:
        await unregister(websocket)

async def appliances_ws(websocket, path):
    # register(websocket) sends appliance list to websocket
    await register(websocket)
    try:
        await websocket.send(appliance_string())
        global appliance_list
        async for message in websocket:
            appliance_list = json.loads(message)
            await notify_appliances()
    finally:
        await unregister(websocket)

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')

def main() -> int:
    """Start OPP."""
    validate_python()
    args = get_arguments()

    logging.basicConfig()
    global STATE
    STATE = {'value': 0}
    global USERS
    USERS = set()
    APPLIANCE_LIST = {
    'NILM-65': {'appliance': {'id': 'NILM-65', 'name': 'Lights', 'type': 'LIGHTING'},
    'usage': {'value': 3.552, 'unit': 'KILO_WATT_HOUR'},
    'cost': {'currency': 'AUD', 'value': 1.32}},
    'NILM-33': {'appliance': {'id': 'NILM-33', 'name': 'Refrigerator', 'type': 'REFRIGERATOR'},
    'usage': {'value': 138.393, 'unit': 'KILO_WATT_HOUR'},
    'cost': {'currency': 'AUD', 'value': 51.2}},
    'NILM-1': {'appliance': {'id': 'NILM-1', 'name': 'Outside Refrigerator', 'type': 'REFRIGERATOR'},
    'usage': {'value': 84.98, 'unit': 'KILO_WATT_HOUR'},
    'cost': {'currency': 'AUD', 'value': 31.43}},
    'NILM-52': {'appliance': {'id': 'NILM-52', 'name': 'Lights', 'type': 'LIGHTING'},
    'usage': {'value': 8.157, 'unit': 'KILO_WATT_HOUR'},
    'cost': {'currency': 'AUD', 'value': 3.02}},
    'NILM-4': {'appliance': {'id': 'NILM-4', 'name': 'Refrigerator', 'type': 'REFRIGERATOR'},
    'usage': {'value': 196.312, 'unit': 'KILO_WATT_HOUR'},
    'cost': {'currency': 'AUD', 'value': 72.63}},
    'NILM-7': {'appliance': {'id': 'NILM-7', 'name': 'Lights 7', 'type': 'LIGHTING'},
    'usage': {'value': 5.516, 'unit': 'KILO_WATT_HOUR'},
    'cost': {'currency': 'AUD', 'value': 2.04}},
    'NILM-25': {'appliance': {'id': 'NILM-25', 'name': 'Water Pump', 'type': 'WATER_PUMP'},
    'usage': {'value': 0.689, 'unit': 'KILO_WATT_HOUR'},
    'cost': {'currency': 'AUD', 'value': 0.25}}
    }

    global appliance_list
    appliance_list = APPLIANCE_LIST
    from .components import smappy
    import datetime
    client_id = 'pcaston'
    client_secret = '2EgQ8BeJBh'
    token = smappy.Smappee(client_id, client_secret)
    username = client_id
    password = 'Boswald0'
    token.authenticate(username, password)
    service_locations_dict = token.get_service_locations()
    service_locations = service_locations_dict['serviceLocations']
    #info=token.get_service_location_info(service_locations[0]['serviceLocationId'])
    #smappee_list = info["appliances"]
    #print(smappee_list)
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days = 365)
    smappee_list = token.get_costanalysis(service_locations[0]['serviceLocationId'], yesterday, today, 3)
    appliance_list = {}
    for i, v in enumerate(smappee_list):
        appliance_list[v['appliance']['id']] = v
    #print(appliance_list)
    #exit_code = setup_and_run_opp()
    #pid = subprocess.Popen(["python", "scriptname.py"], creationflags=subprocess.DETACHED_PROCESS).pid
    #pid = subprocess.Popen(["c:/temp/OPP-ui/npm", "start"], cwd='c:/temp/OPP-ui').pid
    # latest pid = subprocess.Popen(["npm", "start"], cwd='C:/Users/Paul/Documents/github/OpenPeerPower/OPP-ui').pid
    #asyncio.get_event_loop().run_until_complete(
    #    websockets.serve(counter, 'localhost', 6789))
    asyncio.get_event_loop().run_until_complete(
        websockets.serve(appliances_ws, 'localhost', 6789))
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    sys.exit(main())
