from pyharmony.client import init_harmony
from datetime import datetime
import asyncio

HOSTNAME = '192.168.1.118'

SOUND_DEVICE_ID = 35465110


async def harmony_example():
    print('START {0}'.format(datetime.now()))

    client = await init_harmony(HOSTNAME)

    print('CLIENT INITIALIZED {0}'.format(datetime.now()))

    await client.get_device(SOUND_DEVICE_ID)

    print('DEVICE AQUIRED {0}'.format(datetime.now()))

    await client.send_command(SOUND_DEVICE_ID, 'VolumeUp')

    print('COMMAND SENT {0}'.format(datetime.now()))

    await asyncio.sleep(0.5)  # Some devices may not recognize commands sent too quickly
    await client.send_command(SOUND_DEVICE_ID, 'VolumeDown')

    print('COMMAND SENT {0}'.format(datetime.now()))

    client.disconnect()

    print('CONNECTION CLOSED {0}'.format(datetime.now()))

loop = asyncio.get_event_loop()
loop.run_until_complete(harmony_example())
