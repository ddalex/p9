# pure-Python webrtc implementation around gstreamer

class RTCPeerConnection():
    """ WebRTC connection encapsulation """

    class StateException(Exception):
        pass

    def __init__(self):

        # helpers
        self._SDPHelper = _SDPHelper()
        self._ICEAgent = _ICEAgent()

        # data we track
        self.sdp_offer = None
        self.sdp_answer = None

        self.port_pairs = []

        # media we receive
        self.remote_media = []

        # what we send
        self.local_media = []


    def receive_offer(self, message):
        self.sdp_offer = self._SDPHelper.decodeMessage(m['data'])

        self.remote_media = self.sdp_offer['media']

        self.local_candidates = self._ICEAgent.candidate_gather()
        
        self.generate_media_pairs()

        self.sdp_answer = self.build_answer()        

    def build_answer():
        self.sdp_answer = {}
        self.sdp_answer['origin']
        for mp in self.media_pairs:
            if not 'media' in  self.sdp_answer:
                self.sdp_answer['media'] = []
            self.sdp_answer['media'].append(


    def generate_media_pairs(self):
        # match up local media streams with remote media streams
        self.media_pairs = []

        def find_sending_stream(streamtype, media_streams):
            for m in media_streams:
                if streamtype in m:
                    if 'direction' in m[streamtype]:
                        if m[streamtype]['direction'] == "sendonly" or m[streamtype]['direction'] == "sendrecv":
                            return m
            return None
         def find_receiving_stream(streamtype, media_streams):
            for m in media_streams:
                if streamtype in m:
                    if 'direction' in m[streamtype]:
                        if m[streamtype]['direction'] == "recvonly" or m[streamtype]['direction'] == "sendrecv":
                            return m
            return None

        localsendvideo = find_sending_stream('video', self.local_media)
        remoterecvvideo = find_receiving_stream('video', self.remote_media)
        if localsendvideo and remoterecvvideo:
            port_pair = self._ICEAgent.verify_port_pairs(localsendvideo.candidates, remoterecv.candidates)
            self.media_pairs.append({'type': 'video', 'pair': port_pair, 'localstream': localsendvideo, 'remotestream': remoterecvvideo})

        return self.media_pairs
           


    def create_answer(self):
        """ creates internal representation using the offer and the port pairs """
        if not self.sdp_answer:
            raise
        return self.sdp.message_encode(self.sdp_answer))


    def streaming_start(self):
        


    def send_video(self, media, local_host, local_port, remote_host, remote_port):
        # inspired from http://blog.abourget.net/2009/6/14/gstreamer-rtp-and-live-streaming/
        # we send each stream on its own port pair


        import gobject, pygst
        pygst.require("0.10")
        import gst
    
        raise Exception("fixme: TODO send video on RTP/RTCP")
 

class _SDPHelper():
""" class for decoding/encoding SDP messages;
"""
    class NotSDPMessage(Exception):
        pass

    class ProcessingError(Exception):
        pass

    def message_encode(self, msg):
    """ takes an SDP message and returns a Python-readable object
    """
        raise ProcessingError()

    def message_decode(msg):
    """ takes a Python object and returns an SDP message
    """
        raise ProcessingError() 


class _ICEAgent():
    pass
