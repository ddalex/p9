import httplib, urllib
import json
import uuid

P9SERVER = 'localhost:8080'

class APIException(Exception):
    pass


import webrtc

class P9PeerConnection(webrtc.WebRTCPeerConnection):
    """  P9-specific peer connection; it streams the local configured file to the remote peer """
    def __init__(p9, remoteId):
        self.partnerID = remoteID
        self.p9 = p9
        return super(P9PeerConnection, self).__init__() 


    def process_message(self, msgtype, msgdata):
        if msgtype == 'candidate':
            self.remote_candidates.append(self._ICEAgent.candidate_decode(msgdata))

        if msgtype == 'sdp':
            # we got an offer
            self.receive_offer(msgdata)
            while msg
            self.p9.client_postmessage('sdp', self.create_answer())
            self.start_streaming()
        

class P9Client():
    """ Client for P9-based websites; it provides registration, channel creation, offer/answer exchanges, and
        disconnection from a signalling P9 server.

    """

    @staticmethod
    def _urlencode(data):
        if data is None:
            return None
        fields = []
        for i in data.keys():
            fields += [ "%s=%s" % (urllib.quote_plus(unicode(i)), urllib.quote_plus(unicode(data[i]))) ]
        return "&".join(fields)

    assert _urlencode({}) == ""
    assert _urlencode({'a':'b'}) == "a=b"
    assert _urlencode({'a':'b', 'c':'d'}) == "a=b&c=d"
    assert _urlencode({'&':'='}) == "%26=%3D", _urlencode({'&':'='})

    def __init__(self):
        self._cookies = []
        self._peers = {}

    def _xhr_call(self, method, url, data = None):
        global _cookies
        response = None
        if data is not None and method not in ["POST", "PUT"]:
            raise Exception("Are you trying to send data in a non-POST/PUT request")
        try:
            connection = httplib.HTTPConnection(P9SERVER)
            headers = {'User-Agent': 'p9 client (Python)', 'Content-Type': 'application/x-www-form-urlencoded'}
            if len(_cookies):
                headers['Cookie'] = "; ".join(_cookies)

            connection.request(method, url, _urlencode(data), headers)
            response = connection.getresponse()
            if response.status != 200:
                if response.status >= 300 and response.status < 400:
                    print vars(response.msg)
                raise APIException("Failed HTTP request: %s returned %d (%s)" % (url, response.status, response.read()))
            # save any cookies
            for h in response.getheaders():
                if h[0].lower()=="set-cookie":
                    _cookies.append(h[1].split(";")[0])
            return response.read()
        finally:
            connection.close()


    def connect_setup(self):
        return _xhr_call("GET", "/channelcreate")

    def client_register(self):
        import uuid
        my_id = str(uuid.uuid4())
        clients = json.loads(_xhr_call("POST", "/api/1.0/client?%s" % (_urlencode({'s' : my_id }) )))
        for client in clients:
            if client['s'] == my_id:
                return my_id            
        raise Exception("failed: client_register")

    def client_unregister(self, client_id):
        raise Exception("fixme: client_unregister")

    _lastmsgid = 0

    def client_getmessages(self, client_id):
        global _lastmsgid
        return json.loads(_xhr_call("GET", "/api/1.0/message?%s" % (_urlencode({'s': client_id, 'since': _lastmsgid}))))


    def client_postmessage(self, client_id, msgtype, msg):
        

    def channel_register(client_id, name):
        channels = json.loads(_xhr_call("POST", "/api/1.0/channel?%s" % (_urlencode({'s': client_id})), {'name': name, 'x': 0}))
        print "Online channels:", channels
        for channel in channels:
            print channel
            if name == channel['name']:
                return channel['channel']
        raise Exception("failed: channel_register")

    def channel_unregister(channel_id):
        channels = json.loads(_xhr_call("POST", "/api/1.0/channel?%s" % (_urlencode({'s': client_id})), {'channel': channel_id, 'x': 1}))
        

    def channel_getrelays(channel_id):
        relays = json.loads(_xhr_call("POST", "/api/1.0/channel/%s/relay?%s" % (channel_id, _urlencode({'s': client_id}))))
        return relays

    _inloop = False

    def message_process(self, msg):
        global  _lastmsgid
        if msg['c'] > _lastmsgid:
            _lastmsgid = msg['c']

        if not msg['s'] in self._peers:
            self._peers[msg['s']] = P9PeerConnection(self, msg['s'])

        self._peers[msg['s']].process_message(msg['t'], json.loads(msg['d']))
            

def main(p9):
    client_id = p9.client_register()
    print "registered client", client_id
    name = "Test Channel"
    channel_id = p9.channel_register(client_id, name)

    global _inloop
    _inloop = True
    while _inloop:
        try:
            messagelist = p9.client_getmessages(client_id)
            for i in messagelist:
                p9.message_process(i)
        except KeyboardInterrupt:
            _inloop = False

    p9.channel_unregister(client_id)

    return


if __name__ == "__main__":
    p9client = P9Client()
    try:
        p9client.connect_setup()
    except APIException as e:
        print "Connected, API error: ", e
    except IOError, Exception:
        print "Failed to connect to server" 
        raise

    # we can connect, run the main code.
    main(p9client)


