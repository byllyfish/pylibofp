"""Implements a Driver class for communicating with `oftr`."""

import asyncio
import shutil
import shlex
import logging

from zof.oftr import OftrProtocol


LOGGER = logging.getLogger(__package__)


class Driver:
    """Concrete class that communicates with oftr.

    The driver implements the basic OpenFlow RPC commands: listen, connect,
    send and request. It facilitates request/reply pairing and dispatches
    incoming events to higher layers.
    """

    def __init__(self, *, debug=False):
        """Initialize event callback."""
        self.event_queue = None
        self.pid = None
        self._debug = debug
        self._protocol = None
        self._last_xid = 0

    async def __aenter__(self):
        """Async context manager entry point."""
        assert not self._protocol, 'Driver already open'

        cmd = self._oftr_cmd()
        loop = asyncio.get_event_loop()
        self.event_queue = asyncio.Queue()

        def _proto_factory():
            return OftrProtocol(self.post_event, loop)

        # When we create the subprocess, make it a session leader.
        # We do not want SIGINT signals sent from the terminal to reach
        # the subprocess.
        transport, protocol = await loop.subprocess_exec(
            _proto_factory, *cmd, stderr=None,
            start_new_session=True)  # pytype: disable=wrong-arg-types

        self._protocol = protocol
        self.pid = transport.get_pid()

        return self

    async def __aexit__(self, *_args):
        """Async context manager exit point."""
        assert self._protocol, 'Driver not open'

        # Tell the subprocess to stop, then wait for it to exit.
        await self._protocol.stop()

        self._protocol = None
        self.pid = None

    def send(self, event):
        """Send a RPC or OpenFlow message."""
        assert self._protocol, 'Driver not open'

        if 'method' not in event:
            event = self._ofp_send(event)
        self._protocol.send(event)

    async def request(self, event):
        """Send a RPC or OpenFlow message and wait for a reply."""
        assert self._protocol, 'Driver not open'

        if 'method' not in event:
            event = self._ofp_send(event)
        return await self._protocol.request(event)

    async def listen(self, endpoint, options=(), versions=()):
        """Listen for OpenFlow connections on a given endpoint."""
        request = self._ofp_listen(endpoint, options, versions)
        reply = await self.request(request)
        return reply['conn_id']

    async def connect(self, endpoint):
        """Make outgoing OpenFlow connection to given endpoint."""
        request = self._ofp_connect(endpoint)
        reply = await self.request(request)
        return reply['conn_id']

    async def close(self, conn_id):
        """Close an OpenFlow connection."""
        request = self._ofp_close(conn_id)
        reply = await self.request(request)
        return reply['count']

    def post_event(self, event):
        """Dispatch event."""
        assert 'type' in event, repr(event)
        self.event_queue.put_nowait(event)

    def _oftr_cmd(self):
        """Return oftr command with args."""
        cmd = '%s jsonrpc'
        if self._debug:
            cmd += ' --trace=rpc'

        return shlex.split(cmd % shutil.which('oftr'))

    def _assign_xid(self):
        """Return the next xid to use for a request/send."""
        self._last_xid += 1
        return self._last_xid

    def _ofp_send(self, event):
        if 'type' not in event:
            raise ValueError('Invalid event: %r' % event)
        if 'xid' not in event:
            event['xid'] = self._assign_xid()
        return {'method': 'OFP.SEND', 'params': event}

    def _ofp_listen(self, endpoint, options, versions):
        return {
            'id': self._assign_xid(),
            'method': 'OFP.LISTEN',
            'params': {
                'endpoint': endpoint,
                'options': options,
                'versions': versions
            }
        }

    def _ofp_connect(self, endpoint):
        return {
            'id': self._assign_xid(),
            'method': 'OFP.CONNECT',
            'params': {
                'endpoint': endpoint
            }
        }

    def _ofp_close(self, conn_id):
        return {
            'id': self._assign_xid(),
            'method': 'OFP.CLOSE',
            'params': {
                'conn_id': conn_id
            }
        }