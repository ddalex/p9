from django.test import TestCase

from webrtc import MediaStream, SDPHelper, ICEAgent, STUNAgent, RTCPeerConnection

class SDPDecodeTest(TestCase):

    def test_decodesdp(self):
        with open("client/sdp_decodetest.txt", "r") as f:
            data = SDPHelper().message_decode(f.read())

            # to do asserts

    def test_encodesdp(self):
        with open("client/sdp_decodetest.txt", "r") as f:
            filecontent = f.read()
            data = SDPHelper().message_decode(f.read())

        encodedcontent = SDPHelper().message_encode(data)

        self.assertTrue(filecontent == encodedcontent)

class MediaStreamTests(TestCase):
    def test_hasComponents(self):
        mediastream = MediaStream([{"type": "rtp"},{"type": "rtcp"}])
        self.assertTrue('components' in vars(mediastream), "MediaStream object must have a components array")
        self.assertTrue(len(mediastream.components) == 2, "Must have 2 components")


class ICEAgentTests(TestCase):
    def setUp(self):
        self.config = [ { "url": "stun:stun.l.google.com:19302" }, { "url": "stun:stun.services.mozilla.com"}, ]

        self.iceagent = ICEAgent(self.config)
        self.test_stream = MediaStream([{'id' : 1, 'type': 'rtp'}, {'id': 2, 'type': 'rtcp'}])
        pass

    def test_gather_candidates(self):
        candidates = self.iceagent.candidate_gather(self.test_stream)
        self.assertTrue(len(candidates) > 0, "Must have at least one candidate")
        for c in candidates:
            self.assertTrue(c['component'] in self.test_stream.components, "Candidate must link back to a valid component")

        pass

    def test_establish_connection(self):
        pass



import socket

class STUNHelperTests(TestCase):
    """ Verifies a STUN message building and protocol interoperability according to rtf5389 """
    def setUp(self):
        # we are using our own socket because we need to test received IP
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.stunagent = STUNAgent(self.socket)

    def _decode_stun_header(self, binarymsg):
        import struct
        # we expect 20 bytes
        self.assertTrue(len(binarymsg) >=20, "Message shorter than 20 bytes? %d %s" % (len(binarymsg), binarymsg))
        message = struct.unpack(">HHIIII", binarymsg)

        self.assertTrue(message[0] < 0x4000, "Message must start with first two bits 00")

        # deconstruct message type
        message_class = (message[0] & 0x10) >> 4 | ((message[0] & 0x100) >> 7)
        message_type = (message[0] & 0x0F) | ((message[0] & 0xE0) >> 1) | ((message[0] & 0x1E00) >> 2)
        message_length = message[1]
        self.assertTrue((message_length & 0x03) == 0, "Message length must be a multiple of 4")
        magic_cookie = message[2]

        self.assertTrue(magic_cookie == 0x2112A442, "Magic cookie must be 0x2112A442")
        transaction_id = (message[3], message[4], message[5])

        return (message_class, message_type, message_length, transaction_id)

    def _decode_stun_attribute(self, binarymsg):
        self.assertTrue(len(binarymsg) % 4 != 0, "We take multiple-of 4 byte messages")
        attribute = struct.unpack(">HH", binarymsg[:4])
        attribute_type = attribute[0]
        attribute_length = attribute[1]
        self.assertTrue(attribute_type in [0x0001, 0x0006, 0x0008, 0x0009, 0x000A, 0x0014, 0x0015, 0x0020, 0x8022, 0x8023, 0x8028], "Attribute type %x unknown" % attribute_type)
        value = binarymsg[4:attribute_length]
        return (attribute_type, attribute_length, value)


    def test_build_binding_request(self):
        binarymsg = self.stunagent.build_binding_request()

        (message_class, message_type, message_length, transaction_id) = self._decode_stun_header(binarymsg[:20])
        self.assertTrue(message_class == 0b00, "message class must be request")
        self.assertTrue(message_type == 1, "binding request must have message type binding")
        self.assertTrue(((len(binarymsg)-20) % 4) == 0, "message payload must be 32-bit multiple: %d" % (len(binarymsg),))

    def test_build_binding_response(self):
        request = self.stunagent.build_binding_request()
        (message_class, message_type, message_length, transaction_id) = self._decode_stun_header(request[:20])

        binarymsg = self.stunagent.build_binding_response(("0.0.0.0", 0), transaction_id)

        (message_class, message_type, message_length, transaction_id) = self._decode_stun_header(binarymsg[:20])
        self.assertTrue(message_class == 0b10, "message class must be response")
        self.assertTrue(message_type == 1, "binding request must have message type binding")
        self.assertTrue(((len(binarymsg)-20) % 4) == 0, "message payload must be 32-bit multiple")

    def _stun_client(self):
        # run the stun client on a localhost server; this should always return the IP and PORT of the local socket
        self.socket.bind(("127.0.0.1", 0))
        (sockip, sockport) = self.socket.getsockname()
        (ownip, ownport) = self.stunagent.run_client( ("127.0.0.1", 3478) )
        self.assertTrue(sockip == ownip, "Reflex IP on localhost STUN must be own IP")
        self.assertTrue(sockport == ownport, "Reflex port on localhost STUN must be own port")


    def test_stun_client(self):
        # set up an external server
        import subprocess
        try:

            external_server = subprocess.Popen(["/usr/sbin/stund", "-h", "127.0.0.1", "-a", "127.0.0.2", "-v"])
            self._stun_client()

        except Exception as e:
            import traceback
            self.fail(traceback.format_exc(e))

        finally:
            external_server.terminate()
            external_server.wait()

    def test_stun_server_internal_client(self):
        # create a stun server, and run the client test on it
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(("127.0.0.1", 3478))
        stunserver = STUNAgent(server_socket)
        stunserver.run_server()

        self._stun_client()

        stunserver.shutdown_server()

    def test_stun_server_external_client(self):
        # create a stun server, and wait for 30 seconds
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(("127.0.0.1", 3478))
        stunserver = STUNAgent(server_socket)
        stunserver.run_server()
        print "-----   RUN your client now !"
        import time
        time.sleep(30)

        stunserver.shutdown_server()
