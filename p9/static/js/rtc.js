/* vim: set tabstop=4 expandtab softab: */
/**
    P2P single connection
*/

var ROLE = {
    UNDEF : "undefined",
    CALLER : "caller",
    RECEIVER : "receive",
    };

var RTCSTATUS = {
    IDLE : "idle",
    CONNECTED    : "connected",
};

var rtcDEBUG = 0;

/**
    returns a modified RTCPeerConnection to the specified partner.
    if the role is RECEIVER, the partner may be unknown
*/
function rtcGetConnection(role, remoteId, stateCB, dataChannelRecvCB) {

        if (role === undefined) {
            role = ROLE.UNDEF;
        }

        if (role == ROLE.CALLER && remoteId === undefined) {
            throw "rtcGetConnection: cannot call an unknown remoteId"
        }

        var lPC = undefined;
        var sendChannel = undefined;

        // called on either createOffer or createAnswer
       var iceServers = {
            iceServers: [
                        { url: 'stun:stun.sipgate.net' },
                        { url: 'stun:stun.ekiga.net' },
                        { url: 'stun:stun.l.google.com:19302' },
            ]
        };

        if (window.RTCPeerConnection != undefined )
                RPCObject =  window.RTCPeerConnection
        else if (window.mozRTCPeerConnection != undefined )
                RPCObject =  window.mozRTCPeerConnection
        else if (window.webkitRTCPeerConnection != undefined )
                RPCObject =  window.webkitRTCPeerConnection
        else throw "Error finding RPCObject";

        lPC = new RPCObject(iceServers, {optional: [{RtpDataChannels: true}]});

        lPC.role = role;
        lPC.remoteId = remoteId;

        lPC.sendChannel = lPC.createDataChannel("data1", {reliable: false});
        lPC.sendChannel.onopen = function(evt) {
            if(rtcDEBUG)console.log("rtc: data Channel: 1" , evt);
        }

        lPC.sendChannel.onmessage = dataChannelRecvCB;


        lPC.onicecandidate = function(evt) {
            if (evt.candidate != null) {
                smsPostMessage(lPC.remoteId, "candidate", JSON.stringify(evt.candidate));
            }
        }

        lPC.onconnecting = function(evt) {
            if(rtcDEBUG)console.log("rtc: 2: !" , evt);
        }

        lPC.onopen = function(evt) {
            if(rtcDEBUG)console.log("rtc: 3: !" , evt);
        }

        lPC.ondatachannel = function(evt) {
            if(rtcDEBUG)console.log("rtc: 4: !" , evt);
        }

        lPC.oniceconnectionstatechange = function(evt) {
            if(rtcDEBUG)console.log("rtc: Ice connection state: ", this.iceConnectionState);
            if (this.iceConnectionState === "disconnected") {
                console.log("Close callbacks");
                if (this.candidateCallback != undefined) {
                    smsUnregisterCallback("candidate", this.candidateCallback);
                    this.candidateCallback = undefined;
                }
                if (this.sdpCallback != undefined) {
                    smsUnregisterCallback("sdp", lPC.sdpCallback);
                    this.sdpCallback = undefined;
                }
            }
            if (stateCB != undefined) stateCB(this.iceConnectionState);
        }

        lPC.onnegotiationneeded = function (evt) {
            if (lPC.role == ROLE.CALLER) {
                lPC.createSDPResponse();
            }
        }

        function localDescriptionCallback(sdp) {
            if(rtcDEBUG)console.log("rtc: we got local description", sdp);
            lPC.setLocalDescription(sdp,
                function () {
                    if(rtcDEBUG)console.log("rtc: sending local description ", sdp);
                    smsPostMessage(remoteId, "sdp", JSON.stringify(sdp)); // success, we post our description
                },
                function (error) { if(rtcDEBUG)console.log("rtc: ERR: setLocalDescription ", error) } // errorCallback
        )}

        lPC.createSDPResponse = function () {
            var mediaConstraints;
            if (lPC.role == ROLE.CALLER) {
                mediaConstraints= {
                    optional: [],
                    mandatory: {
                        OfferToReceiveAudio: true,
                        OfferToReceiveVideo: true,
                    }
                };
                if(rtcDEBUG)console.log("rtc: .. Creating Offer");
                lPC.createOffer(localDescriptionCallback,function (error) { if(rtcDEBUG)console.log(error) }, mediaConstraints);
            }
            else if (lPC.role == ROLE.RECEIVER) {
                mediaConstraints= {
                    optional: [],
                    mandatory: {
                        OfferToReceiveAudio: false,
                        OfferToReceiveVideo: false,
                    }
                };
                if(rtcDEBUG)console.log("rtc: .. Creating Answer");
                lPC.createAnswer(localDescriptionCallback,function (error) { if(rtcDEBUG)console.log(error) } , mediaConstraints);
            }
            else {
                if(rtcDEBUG)console.log("rtc: Role undefined, no idea what to do");
            }
        }

        lPC.onsignalingstatechange = function(evt) {
            if(rtcDEBUG)console.log("rtc: signalstatechange: !" , this.signalingState);
        }

        lPC.onaddstream = function(evt) {
            if(rtcDEBUG)console.log("rtc: remoteaddedstream: !" , evt);
        }

        lPC.onremovestream = function(evt) {
            if(rtcDEBUG)console.log("rtc: remoteremovedstream: !" , evt);
        }

        // we need to receive any renegociation from the remote ID
        lPC.sdpCallback = smsRegisterCallback("sdp", function (sender, message) {
                if(rtcDEBUG)console.log("renegociation with our designed remote");
                msg = JSON.parse(message);
                lPC.setRemoteDescription(new RTCSessionDescription(msg),
                    function () { if(rtcDEBUG)console.log("rtc: success setting remote"); },
                    function (err) { if(rtcDEBUG)console.log(err) }
                );
            } ,
            remoteId);

        // we want to register the candidates from the remote partner
        lPC.candidateCallback = smsRegisterCallback("candidate", function recvCandidate(sender, message) {
                msg = JSON.parse(message);
                if(rtcDEBUG)console.log("rtc: ", sender, msg )
                var candidate = new RTCIceCandidate({sdpMLineIndex: msg.sdpMLineIndex,
                                        candidate: msg.candidate});
                try {
                    lPC.addIceCandidate(candidate);
                } catch (err) {
                    if (!(typeof(err, SyntaxError) || typeof(err, TypeError))) throw err;
                }
            },
            remoteId);


        return lPC;
}


