"""Client class for connecting to the Logitech Harmony."""

import json
import logging
import time

from sleekxmpp.xmlstream import ET
from sleekxmpp import ClientXMPP
from pyharmony.auth import get_auth_token


LOGGER = logging.getLogger(__name__)

MIME_PREFIX = 'vnd.logitech.harmony/vnd.logitech.harmony.engine'
XMLNS = 'connect.logitech.com'
OFF_ACTIVITY_ID = -1


def get_mime(command):
    return '{0}?{1}'.format(MIME_PREFIX, command)


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

        while not self.sessionstarted:
            time.sleep(0.1)

    def send_request(self, mime, command=None):
        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = XMLNS
        action_cmd.attrib['mime'] = mime
        if command is not None:
            action_cmd.text = command
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=True)
        payload = result.get_payload()

        assert len(payload) == 1
        action_cmd = payload[0]
        assert action_cmd.attrib['errorcode'] == '200'

        return action_cmd.text

    def get_config(self):
        """
        Returns:
          A nested dictionary containing activities, devices, etc.
        """
        mime = get_mime('config')
        result_text = self.send_request(mime)
        return json.loads(result_text)

    def get_current_activity(self):
        """
        Returns:
          A int with the activity ID.
        """
        mime = get_mime('getCurrentActivity')
        result_text = self.send_request(mime)
        activity = result_text.split("=")
        return int(activity[1])

    def _timestamp(self):
        return str(int(round(time.time() * 1000)))

    def start_activity(self, activity_id):
        mime = 'harmony.activityengine?runactivity'
        command = 'activityId=' + str(activity_id) + ':timestamp=' + self._timestamp() + ':async=1'
        self.send_request(mime, command)

    def sync(self):
        """Syncs the harmony hub with the web service."""
        mime = 'setup.sync'
        self.send_request(mime)

    def send_command(self, device_id, command):
        """Send a simple command to the Harmony Hub."""

        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        iq_cmd['id'] = '5e518d07-bcc2-4634-ba3d-c20f338d8927-2'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = get_mime('holdAction')
        action_cmd.text = 'action={"type"::"IRCommand","deviceId"::"'+str(device_id)+'","command"::"'+command+'"}:status=press'
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=False)

        action_cmd.attrib['mime'] = get_mime('holdAction')
        action_cmd.text = 'action={"type"::"IRCommand","deviceId"::"'+device_id+'","command"::"'+command+'"}:status=release'
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=False)

        return result

    def turn_off(self):
        activity = self.get_current_activity()
        print(activity)
        if activity != OFF_ACTIVITY_ID:
            print("OFF")
            self.start_activity(OFF_ACTIVITY_ID)
