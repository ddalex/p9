# pure-Python webrtc implementation around gstreamer

import socket
import struct
import random
import datetime


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RTCPeerConnection():
    """ WebRTC connection encapsulation; provides Connection interface and lifecycle management according to http://www.w3.org/TR/webrtc/ """

    class StateException(Exception):
        pass

    def __init__(self, config):

        # helpers
        self.SDPHelper = SDPHelper()
        assert 'ice' in config.keys()
        self.ICEAgent = ICEAgent(config['iceServers'])

        # data we track
        self.sdp_offer = None
        self.sdp_answer = None

        self.port_pairs = []

        # media we receive
        self.remote_media = []

        # what we send
        self.local_media = []


    def receive_offer(self, message):
        self.sdp_offer = self.SDPHelper.decodeMessage(m['data'])

        self.remote_media = self.sdp_offer['media']

        self.local_candidates = self.ICEAgent.candidate_gather()

        self.generate_media_pairs()

        self.sdp_answer = self.build_answer()

    def build_answer():
        self.sdp_answer = {}
        self.sdp_answer['origin']
        for mp in self.media_pairs:
            if not 'media' in  self.sdp_answer:
                self.sdp_answer['media'] = []
            self.sdp_answer['media'].append(mp)


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
            port_pair = self.ICEAgent.verify_port_pairs(localsendvideo.candidates, remoterecv.candidates)
            self.media_pairs.append({'type': 'video', 'pair': port_pair, 'localstream': localsendvideo, 'remotestream': remoterecvvideo})

        return self.media_pairs



    def create_answer(self):
        """ creates internal representation using the offer and the port pairs """
        if not self.sdp_answer:
            raise
        return self.sdp.message_encode(self.sdp_answer)


    def streaming_start(self):
        raise Exception("must be implemented")


    def send_video(self, media, local_host, local_port, remote_host, remote_port):
        # inspired from http://blog.abourget.net/2009/6/14/gstreamer-rtp-and-live-streaming/
        # we send each stream on its own port pair


        import gobject, pygst
        pygst.require("0.10")
        import gst

        raise Exception("fixme: TODO send video on RTP/RTCP")


class MediaStream():
    def __init__(self, components):
        self.components = components
        for i in xrange(len(self.components)):
            self.components[i]['id'] = i


class SDPHelper():
    """ Helper SDP for decoding/encoding SDP messages to/from internal structures. rtc????
    """
    class ProcessingError(Exception):
        pass

    def message_decode(self, msg):
        """ takes an SDP message and returns a internal-structure object
        """
        obj = {}
        target = obj    # context-dependent dictionary for filling in information
        first_line = True
        for line in msg.split("\n"):
            if len(line) == 0:
                continue
            try:
                attr, value = line.split("=",1)
            except ValueError:
                raise
            value = value.strip()
            if attr == "v":         # protocol version
                if not first_line:
                    raise SDPHelper.ProcessingError("v attribute not in the first line")
                obj["version"] = value

            elif attr == "o":       # owner/creator and session identifier
                (username, session_id, version, network_type, address_type, address) = value.split(" ")
                obj["identifier"] = (username, session_id, version, network_type, address_type, address)

            elif attr == "s":       # session name
                if "session_name" in obj:
                    raise SDPHelper.ProcessingError("encountered duplicate 's' attribute, was '%s', new value '%s'" %(obj["session_name"], value))
                obj["session_name"] = value

            elif attr == "i":       # session information
                if "session_description" in target:
                    raise SDPHelper.ProcessingError("encountered duplicate 'i' attribute on %s, was '%s', new value '%s'" %(str(target), target["session_description"], value))
                target["session_description"] = value

            elif attr == "u":       # URI of description
                if "uri" in obj:
                    raise SDPHelper.ProcessingError("encountered duplicate 'u' attribute, was '%s', new value '%s'" %(obj["uri"], value))
                obj["uri"] = value

            elif attr == "e" or attr == "p":       # email address or phone number
                if not "contact" in obj:
                    obj["contact"] = []
                obj["contact"].append("value")

            elif attr == "c":       # connection information
                if "connection" in target:
                    raise SDPHelper.ProcessingError("encountered duplicate 'c' attribute on %s, was '%s', new value '%s'" %(str(target), target["connection"], value))
                (network_type, address_type, address) = value.split(" ")
                if network_type != "IN":
                    raise SDPHelper.ProcessingError("unknown network type %s, expected 'IN'" % str(network_type))
                target["connection"] = (network_type, address_type, address)

            elif attr == "b":       # bandwidth information
                pass        # FIXME we ignore bandwidth for now
            elif attr == "z":       # time zone adjustment
                pass
            elif attr == "k":       # encryption key
                logger.warn("Unprocessed encryption key %s" % value)
                pass
            elif attr == "a":       # attribute lines !
                # extensible attribute, store in the current target
                if ":" in value:
                    extattr, extval = value.split(":", 1)
                    extattr = "extattr:" + extattr
                else:
                    extattr = "extattr"
                    extval = value

                if not extattr in target:
                    target[extattr] = []
                target[extattr].append(extval)

            elif attr == "t":       # time the session is active
                obj["time"] = map(lambda x: (int(x) - 2208988800), value.split(" "))    # start and stop time, converted from Network Time to Unix time
            elif attr == "r":       # repeat times
                logger.info("Unprocessed repeat times %s" % value)
                pass                # we ignore repeat times for now

            elif attr == "m":       # media name and transport addresses
                if not "mediastreams" in obj:
                    obj["mediastreams"] = []
                target = {}
                obj["mediastreams"].append(target)
                (media_type, port, transport, fmtlist)=value.split(" ", 3)
                if media_type not in ["audio", "video", "application", "data", "control"]:
                    raise SDPHelper.ProcessingError("unknown media type %s", media_type)
                target["media"] = media_type
                target["port"] = port
                target["transport"] = transport
                target["fmtlist"] = fmtlist


            elif attr == "i":       # media title
                pass
            else:
                # we must ignore any attributes we don't understand
                logger.warn("ignored unknown SDP attibute %s=%s" % (attr, value))

            first_line = False


        # message processing done, verify that we have at lest the required fields
        if not "version" in obj:
            raise SDPHelper.ProcessingError("v field missing %s" % obj)
        if obj["version"] != "0":
            raise SDPHelper.ProcessingError("unknown version %s, expected '0'" % obj["version"])
        # limit ourselves to internet connections
        if obj["identifier"][3] != "IN":
            raise SDPHelper.ProcessingError("unknown network type %s, expected 'IN'" % str(obj["identifier"]))


        # we're done
        return obj

    def message_encode(msg, obj):
        """ takes an internal structure Python object and returns an SDP message
        """
        out = ""

        # write the protocol version
        out += "v=0\r\n"

        # identifier must be "username sess-id sess-version nettype addrtype addr"
        if len(obj["identifier"]) != 6:
            raise SDPHelper.ProcessingError("identifier in unknown format %s" % (obj["identifier"],))
        out += "o=" + " ".join(obj["identifier"]) + "\r\n"

        # session name
        out += "s=" + obj["session_name"] + "\r\n"

        # time
        if "time" in obj:
            out += "t=" + " ".join(map(lambda x: str(x + 2208988800), obj["time"])) + "\r\n"

        # session information
        if "session_description" in obj:
            out += "i=" + obj["session_description"] + "\r\n"

        # description URI, if exists
        if "uri" in obj:
            out += "u=" + obj["uri"] + "\r\n"

        if "contacts" in obj:
            for c in obj["contacts"]:
                out += "e=%s\r\n" % c   # FIXME - proper detection of phone nos and other stuff

        def _save_conn(tgt):
            tmp = ""
            if "connection" in tgt:
                tmp += "c=" + " ".join(tgt["connection"]) + "\r\n"
            return tmp

        out += _save_conn(obj)


        # FIXME we don't do bandwidth, time or key fields at this time


        # save an attribute
        def _save_attr(tgt):
            tmp = ""
            for attr in tgt.keys():
                if attr.startswith("extattr:"):
                    name = attr.split(":",1)[1]
                    for v in tgt[attr]:
                        tmp += "a=" + name + ":" + v + "\r\n"
                elif attr.startswith("extattr"):
                    for v in tgt[attr]:
                        tmp += "a=" + v +"\r\n"
            return tmp

        out += _save_attr(obj)

        for m in obj["mediastreams"]:
            out += "m=" + "%s %s %s %s" % (m["media"], m["port"], m["transport"], m["fmtlist"]) + "\r\n"
            out += _save_conn(m)
            out += _save_attr(m)


        return out

class ICEAgent():
    """ Implements an agent that talks RFC5245 over UDP to establish a Peer-to-Peer connection over NAT """
    PREFERENCE_TYPE = {}
    PREFERENCE_TYPE['host'] = 126
    PREFERENCE_TYPE['srflx'] = 100
    PREFERENCE_TYPE['prflx'] = 110  # peer reflex
    PREFERENCE_TYPE['stun'] = 63
    PREFERENCE_TYPE['turn'] = 1

    CANDIDATE_STATE_WAITING = 1
    CANDIDATE_STATE_INPROGRESS = 2
    CANDIDATE_STATE_SUCCEEDED = 3
    CANDIDATE_STATE_FAILED = 4
    CANDIDATE_STATE_FROZEN = 5

    def __init__(self, config):
        self.config = config
        self.local_candidates = []
        self.remote_candidates = []

    def candidate_gather(self, media_stream):

        def _ip_preference(ip):
            if ip.startswith('127.'):
                return 65535
            return 32512

        def _candidate_priority(candidate_type, local_preference, component_id):
            return (16777216 * ICEAgent.PREFERENCE_TYPE[candidate_type])  + (256 * local_preference) + (256 - component_id)

        # HOST CANDIDATES
        # bind ports on all interfaces
        candidates = []
        local_ip4s = []
        import netifaces
        for i in netifaces.interfaces():
            for j in netifaces.ifaddresses(i)[netifaces.AF_INET]:
                local_ip4s.append(j['addr'])

        for component in media_stream.components:
            for ip in local_ip4s:
                candidate = {}
                candidate['component_id'] = component['id']
                candidate['base'] = candidate
                candidate['type'] = 'host'
                candidate['ip'] = ip
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind((ip, 0))
                candidate['port'] = s.getsockname()[1]
                candidate['transport'] = 'udp'
                candidate['foundation'] = 0
                candidate['priority'] = _candidate_priority('host', _ip_preference(ip), component['id'])
                candidate['_socket'] = s
                candidates.append(candidate)


        # SERVER REFLEXIVE CANDIDATES / STUN
        # FIXME noop
        # RELAYED CANDIDATES / TURN
        # FIXME noop


        # order by priority
        self.local_candidates = sorted(candidates, key = lambda x: x['priority'], reverse = True)

        # eliminate duplicates
        for i in xrange(len(self.local_candidates)):
            for j in xrange(i+1, len(self.local_candidates)):
                try:
                    l = self.local_candidates[i]
                    r = self.local_candidates[j]
                    if l['ip'] == r['ip'] and l['port'] == r['port'] and l['base'] == r['base']:
                        del self.local_candidates[j]
                except IndexError:
                    continue

        return self.local_candidates

    def candidate_set_remote(self, candidates):
        self.remote_candidates = candidates

    def _start_check(self, cp):
        cp[2]['stunagent'] = STUNAgent(cp['_socket'])
        # peer address
        peeraddress = ( cp[1]['ip'], cp[1]['port'] )
        cp[2]['stunagent'].run_client( peeraddress )

    def connectivity_checks(self):
        # Connectivity Checks
        self.candidate_pairs = []

        def _combine_foundation(self, f1, f2):
            return f1 + f2

        def _compute_priority(self, p1, p2):
            pmin = p1 if p1 < p2 else p2
            pmax = p1 if p1 > p2 else p2
            flag = 1 if p1 > p2 else 0

            return (4294967296 * pmin + 2 * pmax + flag)


        for i in self.local_candidates:
            for j in self.remote_candidates:
                if self.local_candidates[i]['component_id'] == self.remote_candidates[i]['component_id']:
                    self.candidate_pairs.append(
                        (self.local_candidates[i], self.remote_candidates[j],
                        {
                            'foundation' : _combine_foundation(self.local_candidates[i]['foundation'], self.remote_candidates[j]['foundation']),
                            'state': CANDIDATE_STATE_FROZEN,
                            'priority': _compute_priority(self.local_candidates[i]['priority'], self.remote_candidates[j]['priority']),
                        })
                    )

        # 1. sort candidate pairs
        self.candidate_pairs = sorted(self.candidate_pairs, key = lambda x: x['priority'])

        for cp in self.candidate_pairs:
            if cp[3]['state'] == CANDIDATE_STATE_FROZEN:
                #FIXME: determine which frozen candidate should be started
                cp[3]['state'] = CANDIDATE_STATE_WAITING

            if cp[3]['state'] == CANDIDATE_STATE_WAITING:
                cp[3]['state'] = CANDIDATE_STATE_INPROGRESS
                self._start_check(cp)

    def verify_candidates(self):
        for cp in self.candidate_pairs:
            if cp[3]['state'] == CANDIDATE_STATE_INPROGRESS:
                if cp[3]['stunagent'].is_verified():
                    cp[3]['state'] == CANDIDATE_STATE_SUCCEEDED
                elif cp[3]['stunagent'].is_timeouted():
                    cp[3]['state'] == CANDIDATE_STATE_FAILED




class STUNAgent():
    """ implements a Stun Client/Server (agent) in conformance with rfc5389 """

    SOFTWARE_ID = "P9 WebRTC STUNAgent 0.1"

    TIMEOUT_INITIAL = 1
    TIMEOUT_MAXIMUM = 2
    MAXCOUNT_TIMEOUT = 3


    MSGCLASS_REQUEST = 0b00
    MSGCLASS_INDICATION = 0b01
    MSGCLASS_SUCC_RESPONSE = 0b10
    MSGCLASS_ERR_RESPONSE = 0b11

    MSGTYPE_BINDING = 0x001
    MSGTYPE_RESERVED = 0x000
    MSGTYPE_RESERVED_SHARED_SECRET = 0x002

    MSGATTR_RESERVED_TYPES = [0x0000, 0x0002, 0x0003, 0x0004, 0x0005, 0x0007, 0x000B, 0x8020]   # added 8020 in spite of rtc5389 since it was defined in rfc3489bis2-draft
    MSGATTR_MAPPED_ADDRESS      = 0x0001
    MSGATTR_USERNAME            = 0x0006
    MSGATTR_MESSAGE_INTEGRITY   = 0x0008
    MSGATTR_ERROR_CODE          = 0x0009
    MSGATTR_UNKNOWN_ATTRIBUTES  = 0x000A
    MSGATTR_REALM               = 0x0014
    MSGATTR_NONCE               = 0x0015
    MSGATTR_XOR_MAPPED_ADDRESS  = 0x0020

    MSGATTR_SOFTWARE            = 0x8022
    MSGATTR_ALTERNATE_SERVER    = 0x8023
    MSGATTR_FINGERPRINT         = 0x8028

    ADDR_FAMILY_IPV4            = 0x01
    ADDR_FAMILY_IPV6            = 0x02


    def __init__(self, socket = None):
        self._tracked_transactions = {}
        random.seed(self)
        self.socket = socket

    def _create_transaction_id(self):
        r1 = random.randint(0, 2**32 - 1)
        r2 = random.randint(0, 2**32 - 1)
        r3 = random.randint(0, 2**32 - 1)
        return (r1, r2, r3)

    def _encode_message_header(self, msg_cls, msg_type, msg_len, msg_transaction):
        assert msg_cls < 4, "STUN0001: message class is invalid"
        _magic_cookie = 0x2112A442
        _msg_clstyp = ((msg_cls & 0x02) << 7) | ((msg_cls & 0x01) << 4)
        _msg_clstyp = _msg_clstyp | (msg_type & 0x0F) | ((msg_type & 0x70) << 1) | ((msg_type & 0xf80) << 2)
        msg = struct.pack(">HHIIII", _msg_clstyp, msg_len, _magic_cookie, *msg_transaction)
        assert len(msg) == 20, "STUN0002: invalid message length"
        return msg

    def _encode_message_attribute(self, attr_type, attr_value):

        if attr_type == STUNAgent.MSGATTR_SOFTWARE:
            # compute value
            if len(attr_value) % 4 != 0:
                attr_value += (4 - len(attr_value)%4) * "\x00"
            attr = struct.pack(">HH", attr_type, len(attr_value))
            attr = attr + attr_value

        elif attr_type == STUNAgent.MSGATTR_MAPPED_ADDRESS:
            logger.info("DEBUG: encoding mapped address ", attr_value)
            if len(attr_value[0].split(".")) == 4:
                value = struct.pack(">HHBBBB", STUNAgent.ADDR_FAMILY_IPV4, attr_value[1], *map(int, attr_value[0].split(".")))
                attr = struct.pack(">HH", attr_type, len(value))
                attr += value
            elif len(attr_value.split(":")) == 8:
                raise Exception("STUN0024: FIXME - implement ipv6 packing" % attr_value)
            else:
                raise Exception("STUN0023: unknown IP address family %s " % attr_value)

        else:
            raise Exception("STUN0022: don't know how to pack attribute %x" % attr_type)

        assert len(attr) % 4 == 0, "STUN0003: message attribute length must be a multiple of 4 bytes"
        return attr


    def _decode_message_header(self, binarymsg):
        import struct
        # we expect 20 bytes
        message = struct.unpack(">HHIIII", binarymsg)

        # deconstruct message type
        message_class = (message[0] & 0x10) >> 4 | ((message[0] & 0x100) >> 7)
        message_type = (message[0] & 0x0F) | ((message[0] & 0xE0) >> 1) | ((message[0] & 0x1E00) >> 2)
        message_length = message[1]
        magic_cookie = message[2]

        assert magic_cookie == 0x2112A442, "STUN0005: Magic cookie must be 0x2112A442"
        transaction_id = (message[3], message[4], message[5])

        return (message_class, message_type, message_length, transaction_id)

    def _decode_attribute_header(self, binarymsg):
        attribute = struct.unpack(">HH", binarymsg[:4])
        attribute_type = attribute[0]
        attribute_length = attribute[1]

        assert ((attribute_length) % 4) == 0, "STUN0006: attribute length must be multiple-of-4 byte: %d, %d" % (attribute_type, attribute_length )
        value = None
        if attribute_type == STUNAgent.MSGATTR_SOFTWARE:
            value = binarymsg[4:attribute_length+4]

        elif attribute_type == STUNAgent.MSGATTR_MAPPED_ADDRESS:
            # we got a mapped address, translate and store it as value
            (addr_family, addr_port) = struct.unpack(">HH", binarymsg[4:8])
            def _ip_value_to_string(family, number):
                if family == STUNAgent.ADDR_FAMILY_IPV4:
                    return "%d.%d.%d.%d" % ((number >> 24), (number >> 16) & 0xFF, (number >> 8) & 0xFF, (number & 0xFF))
                raise Exception("STUN0014: FIXME: implement ipv6 to string")

            if (addr_family == STUNAgent.ADDR_FAMILY_IPV4):
                assert attribute_length == 8, "STUN0007: IPv4 address length must be 4: %d" % attribute_length - 4
                value = (_ip_value_to_string(addr_family, struct.unpack(">I", binarymsg[8:12])[0]), addr_port)

            elif (addr_family == STUNAgent.ADDR_FAMILY_IPV6):
                assert attribute_length == 20, "STUN0008: IPv6 address length must be 16: %d" % attribute_length - 4
                value = (_ip_value_to_string(addr_family, struct.unpack(">IIII", binarymsg[8:24])[0]), addr_port)


            else:
                raise Exception("STUN0010:  unknown address family %x" % addr_family)

        elif attribute_type in STUNAgent.MSGATTR_RESERVED_TYPES:
            # we ignore the reserved attributes
            pass
        else:
            raise Exception("STUN0009: unknown attribute %x" % attribute_type)

        return (attribute_type, attribute_length, value)

    def decode_packet(self, recvdata):
        response = {}
        i = 20
        response["class"], response["type"], response["len"], response["transaction_id"] = self._decode_message_header(recvdata[:i])
        response["attributes"] = {}
        while i < response["len"]:
            (attr_type, attr_len, value) = self._decode_attribute_header(recvdata[i:])
            if not attr_type in response["attributes"]:
                response["attributes"][attr_type] = value

            # skip the padding
            if attr_len % 4 != 0:
                attr_len += (4 - attr_len%4) * "\x00"
            i += attr_len + 4

        return response


    def build_binding_request(self, _msg_transaction = None):
        if _msg_transaction == None:
            _msg_transaction = self._create_transaction_id()

        msgattrib = b""
        msgattrib += self._encode_message_attribute(STUNAgent.MSGATTR_SOFTWARE, STUNAgent.SOFTWARE_ID)

        msgdata = self._encode_message_header( STUNAgent.MSGCLASS_REQUEST, STUNAgent.MSGTYPE_BINDING, len(msgattrib), _msg_transaction )
        msgdata += msgattrib

        return msgdata

    def build_binding_response(self, addr, transaction_id):

        msgattrib = self._encode_message_attribute( STUNAgent.MSGATTR_MAPPED_ADDRESS, addr)
        msgattrib += self._encode_message_attribute(STUNAgent.MSGATTR_SOFTWARE, STUNAgent.SOFTWARE_ID)

        msgdata = self._encode_message_header( STUNAgent.MSGCLASS_SUCC_RESPONSE, STUNAgent.MSGTYPE_BINDING, len(msgattrib), transaction_id)
        return msgdata + msgattrib


    def _housekeeping_update(self):
        # house keeping, update internal timeout structures
        for _transaction in self._tracked_transactions:
            td = self._tracked_transactions[_transaction]

            # update timeout counters on sent requests
            if "client" in td and td["client"]["status"] == "requestsent":
                if (datetime.datetime.now() - td["client"]["sent"]).total_seconds() > td["client"]["timeout"]:
                    if td["client"]["timeout"] < STUNAgent.TIMEOUT_MAXIMUM:
                        td["client"]["timeout"] *= 2

            # re-send timed-out packets
            if "client" in td:
                if (datetime.datetime.now() - td["client"]["sent"]).total_seconds() > td["client"]["timeout"]:
                    self.socket.sendto(self.build_binding_request(_transaction), self.server)
                    td["client"]["sent"] = datetime.datetime.now()
                    td["client"]["count"] += 1
                    if td["client"]["count"] > STUNAgent.MAXCOUNT_TIMEOUT:
                        raise Exception("STUN0015: No answer from server")



    def process_packet(self, packet, addr):

        # process an incoming packet; returns a string to be sent as reply, if needed
        packetdata = self.decode_packet(packet)

        if (packetdata["class"] == STUNAgent.MSGCLASS_SUCC_RESPONSE) or (packetdata["class"] == STUNAgent.MSGCLASS_ERR_RESPONSE):
            # we have a response, match it up to a connection
            if not packetdata["transaction_id"] in self._tracked_transactions or not "client" in self._tracked_transactions[packetdata["transaction_id"]]:
               raise Exception("STUN0011: invalid packetdata transaction_id %s" % ( response["class"], "{0:x} {1:x} {2:x}".format(*packetdata["transaction_id"]) ))

            c = self._tracked_transactions[packetdata["transaction_id"]]["client"]
            if c["status"] != "requestsent":
                raise Exception("STUN0021: received response for packet we didn't send")

            c["status"] = "replyrecvd"
            c["rflxip"] = packetdata["attributes"][STUNAgent.MSGATTR_MAPPED_ADDRESS][0]
            c["rflxport"] = packetdata["attributes"][STUNAgent.MSGATTR_MAPPED_ADDRESS][1]


        elif packetdata["class"] == STUNAgent.MSGCLASS_REQUEST:
            self._tracked_transactions[packetdata["transaction_id"]] = {"server":{"status": "responsesent", "sent": datetime.datetime.now()}}
            return self.build_binding_response(addr, packetdata["transaction_id"])

        elif packetdata["class"] == STUNAgent.MSGCLASS_INDICATION:
            pass

        else:
            raise Exception("STUN0020: unknown message class %s" % packetdata)





    def run_client(self, server = None):
        if not "server" in vars(self) or self.server is None:
            self.server = server

        if self.socket is None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._msg_transaction =  self._create_transaction_id()

        import threading
        self.client_thread = threading.Thread(target = STUNAgent._stun_client, args = (self,))
        self.client_thread.daemon = True
        self.client_thread.start()

    def shutdown_client(self):
        if not "client_thread" in vars(self):
            raise Exception("STUN0016: no client running")

        self.client_running = False
        while self.client_thread.is_alive():
            import time
            time.sleep(0.01)
            self.client_thread.join(1)

    def _stun_client(self):

        _msg_transaction = self._msg_transaction

        self._tracked_transactions[_msg_transaction] = {"client" :
            {   "status": "requestsent",
                "sent" : datetime.datetime(1970, 1, 1),
                "timeout" : STUNAgent.TIMEOUT_INITIAL,
                "localip" : self.socket.getsockname()[0],
                "localport" : self.socket.getsockname()[1],
                "count": 0,
            }
        }

        reflex_ip = None
        reflex_port = None

        # start the packet processing thread so we can receive replies
        self.run_server()

        try:
            # if we time-out, we'll raise an Exception
            while True:
                # wait for response; the first request will actually be sent by the first retry :)
                self._housekeeping_update()

                if self._tracked_transactions[self._msg_transaction]["client"]["status"] == "replyrecvd":
                    reflex_ip =  self._tracked_transactions[_msg_transaction]["client"]["rflxip"]
                    reflex_port = self._tracked_transactions[_msg_transaction]["client"]["rflxport"]
                    break

                # yield control
                import time
                time.sleep(0.01)
        except:
            self._tracked_transactions[_msg_transaction]["client"]["status"] == "failed"

        finally:
            # clean up
            self.shutdown_server()

        return (reflex_ip, reflex_port)



    def _stun_server(self):
        logger.info("-- Running the stun server", self)
        self.server_running = True
        self.socket.settimeout(0.01)
        while self.server_running:
            try:
                (packet, addr) = self.socket.recvfrom(2048)
                logger.info("-- Got packet from ", addr, " to ", self.socket.getsockname())
                reply = self.process_packet(packet, addr)
                if reply is not None:
                    self.socket.sendto(reply, addr)
            except socket.timeout:
                # yield execution
                import time
                time.sleep(0.01)

    def run_server(self):
        if self.socket is None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        import threading
        self.server_thread = threading.Thread(target = STUNAgent._stun_server, args = (self,))
        self.server_thread.daemon = True
        self.server_thread.start()

    def shutdown_server(self):
        if not "server_thread" in vars(self):
            raise Exception("STUN0016: no server running")

        self.server_running = False
        while self.server_thread.is_alive():
            import time
            time.sleep(0.01)
            self.server_thread.join(1)
