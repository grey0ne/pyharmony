import asyncio

from slixmpp import ClientXMPP


class BaseXMPPClient(ClientXMPP):
    """An XMPP client for connecting to the Logitech Harmony Hub."""

    def __init__(self, jid, password):

        # Enables PLAIN authentication which is off by default.
        plugin_config = {
            'feature_mechanisms': {'unencrypted_plain': True},
        }

        super(BaseXMPPClient, self).__init__(jid, password, plugin_config=plugin_config)

        # slixmpp is using thread.Event() still.
        self.session_bind_event = asyncio.Event()
