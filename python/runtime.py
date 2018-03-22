import json
import random
import os

""" """
import gevent
import geventwebsocket

class DummyRuntime(object):
    """Trivial example of how one can represent an FBP-ish/dataflow runtime"""
    
    # Component library
    components = {
        "DummyComponent": {
            'description': "An example component which does exactly nothing",
            'inPorts': [
                {'id': 'portA', 'type': 'boolean', 'description': 'A boolean port',
                    'addressable': False, 'required': True  },
                {'id': 'portB', 'type': 'any'}
            ],
            'outPorts': [
                {'id': 'out1', 'type': 'string'}
            ],
        },
    }

    def __init__(self):
        # A runtime can have multiple graphs
        # Normally only one toplevel / "main" can be ran,
        # and the other "subgraphs" can be used as components
        self.graphs = {}
        self.started = False

    def start(self, graph_id):
        self.started = True
    def stop(self, graph_id):
        self.started = False

    def new_graph(self, graph_id):
        self.graphs[graph_id] = {
            'nodes': {},
            'connections': [],
            'iips': []
        }

    def add_node(self, graph_id, node_id, component_id):
        # Normally you'd instantiate the component here,
        # we just store the name
        nodes = self.graphs[graph_id]['nodes']
        nodes[node_id] = component_id
    def remove_node(self, graph_id, node_id):
        # Destroy node instance
        nodes = self.graphs[graph_id]['nodes']
        del nodes[node_id]
    def add_edge(self, graph_id, src, tgt):
        connections = self.graphs[graph_id]['connections']
        connections.append((src, tgt))
    def remove_edge(self, graph_id, src, tgt):
        connections = self.graphs[graph_id]['connections']
        connections = filter(lambda conn: conn[0] != src and conn[1] != tgt, connections)
    def add_iip(self, graph_id, src, data):
        iips = self.graphs[graph_id]['iips']
        iips.append((src, data))
    def remove_iip(self, graph_id, src):
        iips = self.graphs[graph_id]['iips']
        iips = filter(lambda iip: iip[0] != src, iips)

class RuntimeApplication(geventwebsocket.WebSocketApplication):

    def __init__(self, runtime):
        super(RuntimeApplication, self).__init__(self)
        self.runtime = DummyRuntime()

    ### WebSocket transport handling ###
    @staticmethod
    def protocol_name():
        # WebSocket sub-protocol
        return 'noflo'

    def on_open(self):
        print "INFO: Connection opened"

    def on_close(self, reason):
        print "INFO: Connection closed. Reason:", reason

    def on_message(self, message):
        if not message:
            print 'WARN: got empty message'
            return

        m = json.loads(message)
        dispatch = {
            'runtime': self.handle_runtime,
            'component': self.handle_component,
            'graph': self.handle_graph,
            'network': self.handle_network,
        }

        handler = None
        try:
            handler = dispatch[m.get('protocol')]
        except KeyError, e:
            print "WARN: Subprotocol '%s' not supported" % (p)
        else:
            handler(m['command'], m['payload'])

    def send(self, protocol, command, payload):
        """Send a message to UI/client""" 
        if isinstance(payload, dict) and 'secret' in payload:
            del payload['secret']
        m = json.dumps({'protocol': protocol, 'command': command, 'payload': payload})
        self.ws.send(m)

    ### Protocol send/responses ###
    def handle_runtime(self, command, payload):

        # Absolute minimum: be able to tell UI info about runtime and supported capabilities
        if command == 'getruntime':
            payload = {
                'type': 'fbp-python-example',
                'version': '0.7', # protocol version
                'capabilities': [
                    'protocol:graph'
                    'protocol:component',
                    'protocol:network'
                    'protocol:runtime'
                ],
            }
            self.send('runtime', 'runtime', payload)

        # network:packet, allows sending data in/out to networks in this runtime
        # can be used to represent the runtime as a FBP component in bigger system "remote subgraph"
        elif command == 'packet':
            # We don't actually run anything, just echo input back and pretend it came from "out"
            payload['port'] = 'out'
            self.send('runtime', 'packet', payload)

        else:
            print "WARN: Unknown command '%s' for protocol '%s' " % (command, 'runtime')

    def handle_component(self, command, payload):

        # Practical minimum: be able to tell UI which components are available
        # This allows them to be listed, added, removed and connected together in the UI
        if command == 'list':
            for component_name, component_data in self.runtime.components.items():
                # Normally you'd have to do a bit of mapping between
                # your internal/native representation of a component,
                # and what the FBP protocol expects.
                # We cheated and chose naming conventions that matched
                payload = component_data
                payload['name'] = component_name
                payload['subgraph'] = False
                self.send('component', 'component', payload)

            self.send('component', 'componentsready', len(self.runtime.components))

        else:
            print "WARN: Unknown command '%s' for protocol '%s' " % (command, 'component')

    def handle_graph(self, command, payload):

        # Modify our graph representation to match that of the UI/client
        # Note: if it is possible for the graph state to be changed by other things than the client
        # you must send a message on the same format, informing the client about the change
        # Normally done using signals,observer-pattern or similar

        send_ack = True

        # New graph
        if command == 'clear':
            self.runtime.new_graph(payload['id'])
        # Nodes
        elif command == 'addnode':
            self.runtime.add_node(payload['graph'], payload['id'], payload['component'])
        elif command == 'removenode':
            self.runtime.remove_node(payload['graph'], payload['id'])
        # Edges/connections
        elif command == 'addedge':
            self.runtime.add_edge(payload['graph'], payload['src'], payload['tgt'])
        elif command == 'removeedge':
            self.runtime.remove_edge(payload['graph'], payload['src'], payload['tgt'])
        # IIP / literals
        elif command == 'addinitial':
            self.runtime.add_iip(payload['graph'], payload['tgt'], payload['src']['data'])
        elif command == 'removeinitial':
            self.runtime.remove_iip(payload['graph'], payload['tgt'])
        # Exported ports
        elif command in ('addinport', 'addoutport'):
            pass # No support in this example
        # Metadata changes
        elif command in ('changenode'):
            pass
        else:
            send_ack = False
            print "WARN: Unknown command '%s' for protocol '%s' " % (command, 'graph')

        # For any message we respected, send same in return as acknowledgement
        if send_ack:
            self.send('graph', command, payload)


    def handle_network(self, command, payload):
        def send_status(cmd, g):
            started = self.runtime.started
            # NOTE: running indicates network is actively running, data being processed
            # for this example, we consider ourselves running as long as we have been started
            running = started
            payload = {
                graph: g,
                started: started,
                running: running,
            }
            self.send('network', cmd, payload)

        graph = payload.get('graph', None)
        if command == 'getstatus':
            send_status('status', graph)
        elif command == 'start':
            self.runtime.start(graph)
            send_status('started', graph)
        elif command == 'stop':
            self.runtime.stop(graph)
            send_status('stopped', graph)
        else:
            print "WARN: Unknown command '%s' for protocol '%s'" % (command, 'network')


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-p", "--port", default=3569, type='int',
                      help="Port to listen on", metavar="PORT")
    (options, args) = parser.parse_args()

    port = int(os.environ.get('PORT', options.port))
    r = geventwebsocket.Resource({'/': RuntimeApplication})
    s = geventwebsocket.WebSocketServer(('', port), r)
    print 'INFO: Runtime listening on port %d' % (port,)
    s.serve_forever()
