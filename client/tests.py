from django.test import TestCase

from webrtc import MediaStream, _SDPHelper, _ICEAgent, RTCPeerConnection

class SDPDecodeTest(TestCase):

    def test_decodesdp(self):
        with open("client/sdp_decodetest.txt", "r") as f:
            data = _SDPHelper().message_decode(f.read())

            # to do asserts

    def test_encodesdp(self):
        with open("client/sdp_decodetest.txt", "r") as f:
            filecontent = f.read()
            data = _SDPHelper().message_decode(f.read())

        encodedcontent = _SDPHelper().message_encode(data)

        self.assertTrue(filecontent == encodedcontent)


class ICEAgentTests(TestCase):
    def setUp(self):
        self.config = [ { "url": "stun:stun.l.google.com:19302" }, { "url": "stun:stun.services.mozilla.com"}, ]

        self.iceagent = _ICEAgent(self.config)
        self.test_stream = MediaStream([{'id' : 1, 'type': 'rtp'}, {'id': 2, 'type': 'rtcp'}])
        pass

    def test_gather_candidates(self):
        print self.iceagent.candidate_gather(self.test_stream)
        pass

    def test_establish_connection(self):
        pass


