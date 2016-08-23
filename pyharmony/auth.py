import asyncio
import json
import logging
import re

from xml.etree import cElementTree as ET

import requests

from .xmpp import BaseXMPPClient

log = logging.getLogger(__name__)

# The Logitech authentication service URL.
LOGITECH_AUTH_URL = 'https://svcs.myharmony.com/CompositeSecurityServices/Security.svc/json/GetUserAuthToken'


class SessionTokenClient(BaseXMPPClient):
    """An XMPP Client for getting a session token given a login token for a Harmony Hub device."""

    def __init__(self, hostname, port, login_token):
        jid = 'guest@connect.logitech.com/gatorade'
        password = 'guest'

        super(SessionTokenClient, self).__init__(jid, password)

        self.token = login_token
        self.connect(address=(hostname, port), disable_starttls=True, use_ssl=False)

    async def session_start(self):
        """Called when the XMPP session has been initialized."""

        await self.session_bind_event.wait()

        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'

        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = 'vnd.logitech.connect/vnd.logitech.pair'
        action_cmd.text = 'token=%s:name=%s' % (self.token, 'foo#iOS6.0.1#iPhone')

        iq_cmd.set_payload(action_cmd)

        result = await iq_cmd.send()
        payload = result.get_payload()

        assert len(payload) == 1
        oa_response = payload[0]

        assert oa_response.attrib['errorcode'] == '200'

        match = re.search(r'identity=(?P<uuid>[\w-]+):status', oa_response.text)

        if not match:
          raise ValueError('Could not get a session token!')

        uuid = match.group('uuid')

        log.debug('Received UUID from device: %s', uuid)

        return uuid


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


def login(email, password, hostname, port=5222):
    """Performs a full login to Logitech, returning a session token from the local device.

    :param str email: The username (email) to login to Logitech's web service.
    :param str password: The password for the account.
    :param str hostname: The hostname (or IP) of the local Harmony device.
    :param int port: The port of the Harmony device. Defaults to 5222.

    :rtype: str
    """

    # This is syncronous
    login_token = get_login_token(email, password)

    if not login_token:
        raise ValueError('Could not get a login token from the Logitech server.')

    client = SessionTokenClient(hostname, port, login_token)

    tasks = asyncio.gather(*[client.session_start()])
    client.loop.run_until_complete(tasks)
    client.disconnect()

    return next(iter(tasks.result()), None)
