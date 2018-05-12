from zoflite.controller import Controller
from zoflite.backport import asyncio_run


class HubReactiveController(Controller):
    """Demo OpenFlow app that implements a reactive hub."""

    def CHANNEL_UP(self, dp, event):
        # Set up default flow table entry.
        action = {'action': 'OUTPUT', 'port_no': 'CONTROLLER', 'max_len': 'NO_BUFFER'}
        instruction = {'instruction': 'APPLY_ACTIONS', 'actions': [action]}
        ofmsg = {
            'type': 'FLOW_MOD',
            'msg': {
                'table_id': 0,
                'command': 'ADD',
                'priority': 0,
                'match': [],
                'instructions': [instruction]
            }  
        }
        dp.send(ofmsg)

    def PACKET_IN(self, dp, event):
        # Construct a PACKET_OUT message and send it.
        msg = event['msg']
        action = {'action': 'OUTPUT', 'port_no': 'ALL'}
        ofmsg = {
            'type': 'PACKET_OUT',
            'msg': {
                'in_port': msg['in_port'],
                'actions': [action],
                'data': msg['data']
            }
        }
        dp.send(ofmsg)


if __name__ == '__main__':
    asyncio_run(HubReactiveController().run())
