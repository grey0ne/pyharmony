import json
import logging
import time
import asyncio

from slixmpp.xmlstream import ET
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp import ClientXMPP
from pyharmony.exceptions import HarmonyException


logger = logging.getLogger(__name__)

MIME_PREFIX = 'vnd.logitech.harmony/vnd.logitech.harmony.engine'
XMLNS = 'connect.logitech.com'
OFF_ACTIVITY_ID = -1


def get_mime(command):
    return '{0}?{1}'.format(MIME_PREFIX, command)


class Device(object):

    def __init__(self, id, label):
        self.id = id
        self.label = label
        self.commands = {}

    def get_commands(self):
        return self.commands.values()

    def __str__(self):
        return "{0}: {1}".format(self.id, self.label)


class Activity(object):
    def __init__(self, id, label):
        self.id = id
        self.label = label

    def __str__(self):
        return "{0}: {1}".format(self.id, self.label)


class Command(object):
    def __init__(self, name, label):
        self.name = name
        self.label = label

    def __str__(self):
        return "{0}: {1}".format(self.name, self.label)


class HarmonyClient(ClientXMPP):
    """An XMPP client for connecting to the Logitech Harmony."""

    def __init__(self, session_token):

        # Enables PLAIN authentication which is off by default.
        plugin_config = {'feature_mechanisms': {'unencrypted_plain': True}}

        jid = '{token}@connect.logitech.com/gatorade'.format(token=session_token)
        super(HarmonyClient, self).__init__(
            jid, session_token, plugin_config=plugin_config
        )

        self.raw_config = None
        self.devices = {}
        self.activities = {}

    async def connect(self, hostname, port='5222'):
        connected = asyncio.Future()

        async def session_start(event):
            connected.set_result(True)
        self.add_event_handler('session_start', session_start)
        super(HarmonyClient, self).connect(
            address=(hostname, port), disable_starttls=True, use_ssl=False
        )
        await connected

    async def get_activities(self):
        await self.get_config()
        return self.activities.values()

    async def get_activity(self, activity_id):
        await self.get_config()
        return self.activities.get(activity_id)

    async def get_devices(self):
        await self.get_config()
        return self.devices.values()

    async def get_device(self, device_id):
        await self.get_config()
        return self.devices.get(device_id)

    async def send_request(self, mime, command=None, block=True):
        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = XMLNS
        action_cmd.attrib['mime'] = mime
        if command is not None:
            action_cmd.text = command
        iq_cmd.set_payload(action_cmd)
        try:
            if block:
                result = await iq_cmd.send()
            else:
                iq_cmd.send()
        except (IqError, IqTimeout):
            raise HarmonyException('Error sending command to hub')

        if block:
            payload = result.get_payload()

            if len(payload) != 1:
                raise HarmonyException('Bad payload from hub')

            response = payload[0]

            result_code = response.attrib['errorcode']

            if result_code != '200':
                raise HarmonyException(
                    'Bad response code from hub: {0}'.format(result_code)
                )

            return response.text

    async def reload_config(self):
        self.raw_config = None
        self.devices = {}
        self.activities = {}
        await self.get_config()

    async def get_config(self):
        """
        Returns:
          A nested dictionary containing activities, devices, etc.
        """
        if self.raw_config is None:
            mime = get_mime('config')
            result_text = await self.send_request(mime)

            config = json.loads(result_text)

            for device_config in config['device']:
                device = Device(
                    id=int(device_config['id']), label=device_config['label']
                )

                for group_config in device_config['controlGroup']:
                    for command_config in group_config['function']:
                        command = Command(
                            name=command_config['name'],
                            label=command_config['label']
                        )
                        device.commands[command.name] = command

                self.devices[device.id] = device

            for activity_config in config['activity']:
                activity = Activity(
                    id=int(activity_config['id']), label=activity_config['label']
                )

                self.activities[activity.id] = activity

            self.raw_config = config
        return self.raw_config

    async def get_current_activity(self):
        mime = get_mime('getCurrentActivity')
        result_text = await self.send_request(mime)
        current_activity_id = result_text.split("=")[1]
        return int(current_activity_id)

    def _timestamp(self):
        return str(int(round(time.time() * 1000)))

    async def start_activity(self, activity_id):
        mime = 'harmony.activityengine?runactivity'
        command = 'activityId={0}:timestamp={1}:async=1'.format(
            activity_id, self._timestamp()
        )
        await self.send_request(mime, command, block=False)

    async def sync(self):
        """Syncs the harmony hub with the web service."""
        mime = 'setup.sync'
        await self.send_request(mime, block=False)

    async def send_command(self, device_id, command):
        """Send a simple command to the Harmony Hub."""

        mime = get_mime('holdAction')
        command = 'action={{"type"::"IRCommand","deviceId"::"{0}","command"::"{1}"}}:status=press'.format(
            device_id, command
        )
        await self.send_request(mime, command, block=False)

        mime = get_mime('holdAction')
        command = 'action={{"type"::"IRCommand","deviceId"::"{0}","command"::"{1}"}}:status=release'.format(
            device_id, command
        )
        await self.send_request(mime, command, block=False)

    async def turn_off(self):
        activity = await self.get_current_activity()
        if activity != OFF_ACTIVITY_ID:
            await self.start_activity(OFF_ACTIVITY_ID)
