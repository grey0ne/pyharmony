import json
import logging
import time

from sleekxmpp.xmlstream import ET
from sleekxmpp import ClientXMPP
from pyharmony.auth import get_auth_token


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


class HarmonyException(Exception):
    pass


class HarmonyClient(ClientXMPP):
    """An XMPP client for connecting to the Logitech Harmony."""

    def __init__(self, hostname, port='5222'):
        session_token = get_auth_token(hostname, port)

        # Enables PLAIN authentication which is off by default.
        plugin_config = {'feature_mechanisms': {'unencrypted_plain': True}}

        jid = '%s@connect.logitech.com/gatorade' % session_token
        super(HarmonyClient, self).__init__(
            jid, session_token, plugin_config=plugin_config
        )

        self.connect(address=(hostname, port), use_tls=False, use_ssl=False)
        self.process(block=False)

        self.raw_config = None
        self.devices = {}
        self.activities = {}

        while not self.sessionstarted:
            time.sleep(0.1)

    def get_activities(self):
        self.get_config()
        return self.activities.values()

    def get_activity(self, activity_id):
        self.get_config()
        return self.activities.get(activity_id)

    def get_devices(self):
        self.get_config()
        return self.devices.values()

    def get_device(self, device_id):
        self.get_config()
        return self.devices.get(device_id)

    def send_request(self, mime, command=None, block=True):
        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = XMLNS
        action_cmd.attrib['mime'] = mime
        if command is not None:
            action_cmd.text = command
        iq_cmd.set_payload(action_cmd)
        try:
            result = iq_cmd.send(block=block)
        except:
            raise HarmonyException('Error sending command to hub')

        if block:
            payload = result.get_payload()

            if len(payload) != 1:
                raise HarmonyException('Bad payload from hub')

            action_cmd = payload[0]

            result_code = action_cmd.attrib['errorcode']

            if result_code != '200':
                raise HarmonyException(
                    'Bad response code from hub: {0}'.format(result_code)
                )

            return action_cmd.text

    def reload_config(self):
        self.raw_config = None
        self.devices = {}
        self.activities = {}
        self.get_config()

    def get_config(self):
        """
        Returns:
          A nested dictionary containing activities, devices, etc.
        """
        if self.raw_config is None:
            mime = get_mime('config')
            result_text = self.send_request(mime)

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

    def get_current_activity(self):
        mime = get_mime('getCurrentActivity')
        result_text = self.send_request(mime)
        current_activity_id = result_text.split("=")[1]
        return current_activity_id

    def _timestamp(self):
        return str(int(round(time.time() * 1000)))

    def start_activity(self, activity_id):
        mime = 'harmony.activityengine?runactivity'
        command = 'activityId={0}:timestamp={1}:async=1'.format(
            activity_id, self._timestamp()
        )
        self.send_request(mime, command)

    def sync(self):
        """Syncs the harmony hub with the web service."""
        mime = 'setup.sync'
        self.send_request(mime)

    def send_command(self, device_id, command):
        """Send a simple command to the Harmony Hub."""

        mime = get_mime('holdAction')
        command = 'action={{"type"::"IRCommand","deviceId"::"{0}","command"::"{1}"}}:status=press'.format(
            device_id, command
        )
        self.send_request(mime, command, block=False)

        mime = get_mime('holdAction')
        command = 'action={{"type"::"IRCommand","deviceId"::"{0}","command"::"{1}"}}:status=release'.format(
            device_id, command
        )
        self.send_request(mime, command, block=False)

    def turn_off(self):
        activity = self.get_current_activity()
        if activity != OFF_ACTIVITY_ID:
            self.start_activity(OFF_ACTIVITY_ID)
