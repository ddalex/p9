from django.test import TestCase

from webrtc import _SDP, _ICE, RTCPeerConnection

class SDPDecodeTest(TestCase):
    
    def test_decodesdp(self):
        with open("client/sdp_decodetest.txt", "r") as f:
            data = _SDP().decodeMessage(f.read())

            # to do asserts
       
    def test_encodesdp(self):
        with open("client/sdp_decodetest.txt", "r") as f:
            filecontent = f.read()

        data = _SDP().decodeMessage(f.read())
        encodedcontent = _SDP().encodeMessage(data)

        self.assertTrue(filecontent == encodedcontent)


class ICEAgentTests(TestCase):
    def setup(self):
        # TODO: create an external ICE agent; 
        pass

    def test_gather_candidates(self):
        pass

    def test_establish_connection(self):
        pass


