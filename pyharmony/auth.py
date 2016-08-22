import json
import logging
import re

from xml.etree import cElementTree as ET

import requests
import sleekxmpp

log = logging.getLogger(__name__)

# The Logitech authentication service URL.
LOGITECH_AUTH_URL = 'https://svcs.myharmony.com/CompositeSecurityServices/Security.svc/json/GetUserAuthToken'


class SwapAuthToken(sleekxmpp.ClientXMPP):
    """An XMPP client for swapping a Login Token for a Session Token.

    After the client finishes processing, the uuid attribute of the class will
    contain the session token.
    """

    def __init__(self, token):
        """Initializes the client.

        :param str token: The base64 string containing the 48-byte Login Token.
        """

        plugin_config = {
            # Enables PLAIN authentication which is off by default.
            'feature_mechanisms': {'unencrypted_plain': True},
        }

        super(SwapAuthToken, self).__init__('guest@connect.logitech.com/gatorade', 'guest', plugin_config=plugin_config)

        self.token = token
        self.uuid = None
        self.add_event_handler('session_start', self.session_start)

    def session_start(self, _):
        """Called when the XMPP session has been initialized."""

        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'

        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = 'vnd.logitech.connect/vnd.logitech.pair'
        action_cmd.text = 'token=%s:name=%s' % (self.token, 'foo#iOS6.0.1#iPhone')

        iq_cmd.set_payload(action_cmd)

        result = iq_cmd.send(block=True)
        payload = result.get_payload()

        assert len(payload) == 1
        oa_resp = payload[0]

        assert oa_response.attrib['errorcode'] == '200'

        match = re.search(r'identity=(?P<uuid>[\w-]+):status', oa_response.text)
        assert match

        self.uuid = match.group('uuid')

        log.debug('Received UUID from device: %s', self.uuid)

        self.disconnect(send_close=False)


def get_login_token(username, password):
    """Login to the Logitech Harmony web service & return a login token.

    :param str username: The username (email address).
    :param str password: The user's password.

    :returns: A base64-encoded string containing a 48-byte Login Token.
    :rtype: str
    """

    headers = {'content-type': 'application/json; charset=utf-8'}
    data = {'email': username, 'password': password}
    data = json.dumps(data)

    response = requests.post(LOGITECH_AUTH_URL, headers=headers, data=data)
    if response.status_code != requests.codes.ok:
        log.error('Received response code %d from Logitech.', response.status_code)
        log.error('Data: \n%s\n', response.text)
        return

    result = response.json().get('GetUserAuthTokenResult', None)
    if not result:
        log.error('Malformed JSON (GetUserAuthTokenResult): %s', response.json())
        return

    token = result.get('UserAuthToken', None)
    if not token:
        log.error('Malformed JSON (UserAuthToken): %s', response.json())
        return

    return token


def swap_auth_token(ip_address, port, login_token):
    """Swaps the Logitech auth token for a session token.

    :param str ip_address: IP Address of the Harmony device.
    :param int port: Port that the Harmony device is listening on.
    :param str token: A base64-encoded string containing a 48-byte Login Token.

    :rtype: str
    :returns: A string containing the session token.
    """
    login_client = SwapAuthToken(login_token)
    login_client.connect(address=(ip_address, port), use_tls=False, use_ssl=False)
    login_client.process(block=True)

    return login_client.uuid


def login(email, password, hostname, port=5222):
    """Performs a full login to Logitech, returning a session token from the local device.

    :param str email: The username (email) to login to Logitech's web service.
    :param str password: The password for the account.
    :param str hostname: The hostname (or IP) of the local Harmony device.
    :param int port: The port of the Harmony device. Defaults to 5222.

    :rtype: str
    """
    token = get_login_token(email, password)

    if not token:
        raise ValueError('Could not get a login token from the Logitech server.')

    session_token = swap_auth_token(hostname, port, token)

    if not session_token:
        raise ValueError('Could not swap login token for a session token.')

    return session_token
