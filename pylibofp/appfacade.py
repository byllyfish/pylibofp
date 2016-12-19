from .compiledmessage import CompiledMessage
from .event import make_event


class AppFacade(object):
    """Facade that provides access to API functions.

    This object will be returned by `ofp_app` function.

    Module Example::

        from ofp_app import ofp_app, ofp_run

        ofp = ofp_app(loglevel='info')

        @ofp.message('packet_in')
        def packet_in(event):
            print(event)

        if __name__ == '__main__':
            ofp_run()

    Closure Example::

        from ofp_app import ofp_app, ofp_run

        def make_app(name):
            ofp = ofp_app(name=name)

            @ofp.message('packet_in')
            def packet_in(event):
                print('%s: %s' % (ofp.name, event))

        if __name__ == '__main__':
            for name in ['app1', 'app2']:
                make_app(name)
            ofp_run()

    Class Example::

        class App(object):
            def __init__(self, name):
                self.ofp = ofp_app(name=name)
                # We can't use `message` decorator.
                self.ofp.subscribe(self.packet_in, 'message', 'packet_in')

            def packet_in(self, event):
                print(event)

    Args:
        app (ControllerApp): Internal app object.

    Attributes:
        name (str): App name.
        logger (Logger): App's logger.
    """

    def __init__(self, app):
        self._app = app
        self.name = app.name
        self.logger = app.logger

        #self.send = app.send
        #self.request = app.request
        self.ensure_future = app.ensure_future
        self.subscribe = app.subscribe
        self.unsubscribe = app.subscribe
        #self.post_event = app.post_event
        #self.rpc_call = app.rpc_call

    # Decorators

    def message(self, subtype, **kwds):
        """ Message subscribe decorator.
        """
        def _wrap(func):
            self.subscribe(func, 'message', subtype, kwds)

        return _wrap

    def event(self, subtype, **kwds):
        """ Event subscribe decorator.
        """
        def _wrap(func):
            self.subscribe(func, 'event', subtype, kwds)

        return _wrap

    # Basic Functions

    def compile(self, msg):
        """ Compile an OpenFlow message template.
        """
        return CompiledMessage(self._app, msg)

    # RPC Functions

    async def connect(self, endpoint, options):
        """ Make an outgoing OpenFlow connection.
        """
        result = await self._app.rpc_call('OFP.CONNECT', endpoint=endpoint, options=options)
        return result.conn_id


    def post_event(self, event, **kwds):
        self._app.post_event(make_event(event=event.upper(), **kwds))

#    # Basic Functions
#
#    def send(self, msg, **kwds):
#        """ Send an OpenFlow message.
#        """
#        pass
#
#    def request(self, msg, **kwds):
#        """ Send an OpenFlow request and receive a response.
#        """
#        pass
#
#    # Task Management
#
#    def ensure_future(self, coroutine, *, datapath_id=None, conn_id=None):
#        """ Run an async coroutine, under a specific scope.
#        """
#        pass
#
#    # Advanced Functions
#
#    def subscribe(self, callback, type_, subtype, options):
#        """ Subscribe a callback.
#        """
#        pass
#
#    def unsubscribe(self, callback):
#        """ Unsubscribe a callback.
#        """
#        pass
#
#    def post_event(self, **event):
#        """ Post an internal event to all app modules.
#        """
#        pass
#
#    def rpc_call(self, method, **params):
#        """ Send a RPC request and receive a response.
#        """
#        pass
