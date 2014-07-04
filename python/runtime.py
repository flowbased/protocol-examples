import json
import random

""" """
import gevent
import geventwebsocket

class Runtime(object):
    """Trivial example of how one can represent an FBP-ish runtime"""
    
    # Component library
    components = {
        "MyComponent": {
            'description': "An example component which does exactly nothing"
            'inPorts': [
                {'id': 'portA', 'type': 'boolean', 'description': 'A boolean port',
                    'addressable': false, 'required': true  },
                {'id': 'portB', 'type': ''}
            ]
        }
    }

    def __init__(self):
        # A runtime can have multiple graphs
        # Normally only one toplevel / "main" can be ran, and the other "subgraphs" can be used as components
        self.graphs = {}



class RuntimeProtocol(geventwebsocket.WebSocketApplication):

    def __init__(self, runtime):
        self.runtime = runtime

    ### WebSocket transport handling ###
    def on_open(self):send
        print "Connection opened"

    def on_close(self, reason):
        print "Connection closed", reason

    def on_message(self, message):
        m = json.loads(message)
        dispatch = {
            'runtime': self.handle_runtime
            'component': self.handle_runtime
            'graph': self.handle_graph
            'network': self.handle_network
        }
        try
            dispatch[m.get(protocol)](m['command'], m['payload'])

    def send(self, protocol, command, payload):
        """Send a message to UI/client""" 
        m = json.dumps({'protocol': protocol, 'command': command, 'payload': payload})
        self.ws.send(m)

    ### Protocol send/responses ###
    def handle_runtime(self, command, payload):

        # Absolute minimum: be able to tell UI info about runtime and supported capabilities
        if command == 'getruntime':
            pay = {
                'type': 'fbp-python-example'
                'version': '0.4' # protocol version
                'capabilities': [ 
                    'protocol:component'
                ]
            }
            self.send('runtime', 'runtime', response)
        else:
            print "WARN: Unknown command '%s' for protocol '%s' " % (command, 'runtime')

    def handle_component(self, command, payload):

        # Practical minimum: be able to tell UI which components are available
        # This allows them to be listed, added, removed and connected together in the UI
        if command == 'list':
            for component_name, component_data in self.runtime.components:
                # Normally you'd have to do a bit of mapping between your internal/native representation
                # of a component, and what the FBP protocol expects. We cheated and chose naming conventions that matched

                self.send

        else:
            print "WARN: Unknown command '%s' for protocol '%s' " % (command, 'runtime')

    def handle_graph(self, command, payload):

        # Modify our graph representation to match that of the UI
        # Note: if it is possible for the graph state to be changed by other things than the UI
        # you must send a message on the same format, informing the UI about the change

        graph = self.graphs.get(payload['graph'], None)

        # New graph
        if command == 'clear':
            self.graphs[payload['id']] = {
                nodes: {},
                connections: []
        }

        # Nodes
        elif command == 'addnode':
            # This is where you'd normally instantiate your component. We just store the name
            graph['nodes'][payload['id']] = payload['component']
        elif command == 'removenode':
            # Destroy your instance
            del graph['nodes'][payload['id']

        # Edges/connections
        elif command == 'addedge':

        elif command == 'removeedge':

        # IIP / literals
        elif command == 'addiip':

        elif command == 'removeiip':


        # No support for exported in/out-ports
        else:
            print "WARN: Unknown command '%s' for protocol '%s' " % (command, 'graph')



    def handle_network(self, command, payload):

        # 

r = geventwebsocket.Resource({'/': RuntimeApplication}
s = geventwebsocket.WebSocketServer(('', 8000), r)
s.serve_forever()
