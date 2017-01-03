# -*- coding: utf-8 -*-

# Copyright (c) 2013, Jeff Terrace
# All rights reserved.

"""Authentication routines to connect to Logitech web service and Harmony devices."""

import logging
import re
import asyncio

from slixmpp import ClientXMPP
from slixmpp.xmlstream import ET
from pyharmony.exceptions import HarmonyException

logger = logging.getLogger(__name__)


class AuthTokenClient(ClientXMPP):
    """

    After the client finishes processing, the uuid attribute of the class will
    contain the session token.
    """
    def __init__(self):
        plugin_config = {
            # Enables PLAIN authentication which is off by default.
            'feature_mechanisms': {'unencrypted_plain': True},
        }
        super(AuthTokenClient, self).__init__(
            'guest@connect.logitech.com/gatorade.', 'gatorade.', plugin_config=plugin_config
        )

    async def get_token(self):
        """Called when the XMPP session has been initialized."""
        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = 'vnd.logitech.connect/vnd.logitech.pair'
        action_cmd.text = 'method=pair:name={0}'.format('pyharmony#iOS10.1#iPhone')
        iq_cmd.set_payload(action_cmd)
        result = await iq_cmd.send()
        payload = result.get_payload()

        if len(payload) != 1:
            raise HarmonyException('Bad payload from hub')

        response = payload[0]

        result_code = response.attrib['errorcode']

        if result_code != '200':
            raise HarmonyException(
                'Bad response code from hub: {0}'.format(result_code)
            )

        match = re.search(r'identity=(?P<uuid>[\w-]+):status', response.text)
        if not match:
            raise HarmonyException(
                'Token not found in response'
            )
        return match.group('uuid')


def get_auth_token(hostname, port):
    login_client = AuthTokenClient()

    token = asyncio.Future()

    async def session_start(event):
        token.set_result(await login_client.get_token())
        login_client.disconnect()

    login_client.add_event_handler('session_start', session_start)
    login_client.connect(address=(hostname, port), disable_starttls=True, use_ssl=False)
    login_client.process(forever=False)
    return token.result()
