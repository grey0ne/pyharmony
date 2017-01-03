from pyharmony.client import HarmonyClient
from datetime import datetime

HOSTNAME = '192.168.1.118'
PORT = 5222

SOUND_DEVICE_ID = 35465110

print('START {0}'.format(datetime.now()))
client = HarmonyClient(HOSTNAME, PORT)

async def start(event):
    print('CLIENT INITIALIZED {0}'.format(datetime.now()))
    await client.get_device(SOUND_DEVICE_ID)

    print('DEVICE AQUIRED {0}'.format(datetime.now()))

    await client.send_command(SOUND_DEVICE_ID, 'VolumeUp')

    print('COMMAND SENT {0}'.format(datetime.now()))

    await client.send_command(SOUND_DEVICE_ID, 'VolumeUp')

    print('COMMAND SENT {0}'.format(datetime.now()))

    await client.disconnect()

    print('CONNECTION CLOSED {0}'.format(datetime.now()))

client.add_event_handler('session_start', start)
client.process(forever=False)
