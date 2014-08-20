
import httplib
import uuid
import sys
import json

# Example of how to register a runtime with WebSocket transport with Flowhub / NoFlo UI
# This is used so that the UI can know which runtimes you have available
# It is possible to customize NoFlo UI to add other discovery mechanisms

def register_runtime(user_id, label, ip, port, runtime_type):
    runtime_id = str(uuid.uuid4())
    headers = {"Content-type": "application/json"}
    data = {
        'type': runtime_type, 'protocol': 'websocket',
        'address': ip+":"+str(port), 'id': runtime_id,
        'label': label, 'port': port, 'user': user_id,
        'secret': "aaaa",
    }

    conn = httplib.HTTPConnection("api.flowhub.io", 80)
    conn.connect()
    conn.request("PUT", "/runtimes/"+runtime_id, json.dumps(data), headers)
    response = conn.getresponse()
    if not response.status == 201:
        raise ValueError("Could not create runtime " + str(response.status) + str(response.read()))
    else:
        print "Runtime registered with ID", runtime_id

if __name__ == '__main__':
    from optparse import OptionParser

    usage = '%s USER_UUID LABEL' % sys.argv[0]
    parser = OptionParser(usage=usage)
    parser.add_option("-a", "--host", default='localhost',
                        help="Webscocket hostname")
    parser.add_option("-p", "--port", default='3569',
                      help="Websocket port")
    parser.add_option("-t", "--type", default='fbp-python-example',
                      help="Runtime type")

    (options, args) = parser.parse_args()
    if len(args) == 2:
        register_runtime(args[0], args[1], options.host, options.port, options.type)
    else:
        parser.error('Expected 2 arguments, got %d' % (len(args),))

