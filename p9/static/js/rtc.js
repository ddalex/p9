/* vim: set tabstop=4 expandtab ai: */
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

var rtcDEBUG = 1;

/**
    returns a modified RTCPeerConnection to the specified partner.
    if the role is RECEIVER, the partner may be unknown
*/
function rtcGetConnection(role, remoteId, onStateCB, onStreamCB, onDRecvCB) {
    
    if (role === undefined) {
        role = ROLE.UNDEF;
    }

    if (role == ROLE.CALLER && remoteId === undefined) {
        throw "rtcGetConnection: cannot call an unknown remoteId"
    }

    if (onStateCB === undefined) {
        throw "rtc: no onStateCB handler";
    }
    if (onStreamCB === undefined) {
        throw "rtc: no onStreamCB handler";
    }
    if (onDRecvCB === undefined) {
        throw "rtc: no onDRecvCB handler";
    }


    var lPC = undefined;
    var sendChannel = undefined;

    // called on either createOffer or createAnswer
    var iceServers = {
        iceServers: [
                    { url: 'stun:stun.l.google.com:19302' },
        ]
    };

    var _RTCPeerConnection = undefined;
    if (window.RTCPeerConnection != undefined)
            _RTCPeerConnection =  window.RTCPeerConnection
    else if (window.mozRTCPeerConnection != undefined)
            _RTCPeerConnection =  window.mozRTCPeerConnection
    else if (window.webkitRTCPeerConnection != undefined)
            _RTCPeerConnection =  window.webkitRTCPeerConnection
    else throw "Error finding RTCPeerConnection";

    var _RTCSessionDescription = undefined;
    if (window.RTCSessionDescription != undefined)
            _RTCSessionDescription = window.RTCSessionDescription
    else if (window.mozRTCSessionDescription != undefined)
            _RTCSessionDescription = window.mozRTCSessionDescription
    else throw "Error finding RTCSessionDescription";

    var _RTCIceCandidate = undefined;
    if (window.RTCIceCandidate != undefined)
            _RTCIceCandidate = window.RTCIceCandidate
    else if (window.mozRTCIceCandidate != undefined)
            _RTCIceCandidate = window.mozRTCIceCandidate
    else throw "Error finding RTCIceCandidate";


    lPC = new _RTCPeerConnection(iceServers, {optional: [{RtpDataChannels: true}]});

    lPC.role = role;
    lPC.remoteId = remoteId;

    lPC.sendChannel = lPC.createDataChannel("data1", {reliable: false});
    lPC.sendChannel.onopen = function(evt) {
        if(rtcDEBUG)console.log("rtc: data Channel: 1" , evt);
    }

    lPC.sendChannel.onmessage = onDRecvCB;

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
        if(rtcDEBUG)console.log("rtc: Ice connection state: ", lPC.iceConnectionState);
        if (lPC.iceConnectionState === "disconnected") {
            console.log("Close callbacks");
            if (lPC.candidateCallback != undefined) {
                smsUnregisterCallback("candidate", this.candidateCallback);
                lPC.candidateCallback = undefined;
            }
            if (lPC.sdpCallback != undefined) {
                smsUnregisterCallback("sdp", lPC.sdpCallback);
                lPC.sdpCallback = undefined;
            }
        }
        if (onStateCB != undefined) onStateCB(this.iceConnectionState);
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
            lPC.createOffer(localDescriptionCallback,function (error) { if(rtcDEBUG)throw(error) }, mediaConstraints);
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
            lPC.createAnswer(localDescriptionCallback,function (error) { if(rtcDEBUG)throw(error) } , mediaConstraints);
        }
        else {
            if(rtcDEBUG)console.log("rtc: Role undefined, no idea what to do");
        }
    }

    lPC.onsignalingstatechange = function(evt) {
        if(rtcDEBUG)console.log("rtc: signalstatechange: " , lPC.signalingState);
    }

    lPC.onaddstream = function(evt) {
        if(rtcDEBUG)console.log("rtc: remoteaddedstream: !" , evt);
        onStreamCB(evt.stream, "add");
    }

    lPC.onremovestream = function(evt) {
        if(rtcDEBUG)console.log("rtc: remoteremovedstream: !" , evt);
        onStreamCB(undefined, "remove");
    }

    lPC.buildSessionDescription = function(msg) {
        return new _RTCSessionDescription(msg);
    }

    lPC.gotSDP = 0;
    // we need to receive any renegociation from the remote ID
    lPC.sdpCallback = smsRegisterCallback("sdp", function (sender, message) {
            if (lPC.gotSDP) return;
            lPC.gotSDP = 1;
            msg = JSON.parse(message);
            if(rtcDEBUG)console.log("rtc: negociation with our designed remote, received", msg);
            lPC.setRemoteDescription( new _RTCSessionDescription(msg),
                function () { if(rtcDEBUG)console.log("rtc: success setting remote"); },
                function (err) { if(rtcDEBUG)throw(err) }
            );
        } ,
        remoteId);

    // we want to register the candidates from the remote partner
    lPC.candidateCallback = smsRegisterCallback("candidate", function recvCandidate(sender, message) {
            msg = JSON.parse(message);
            if(rtcDEBUG)console.log("rtc: got candidate from remote ", sender, msg )
            var candidate = new _RTCIceCandidate({sdpMLineIndex: msg.sdpMLineIndex,
                                    candidate: msg.candidate});
            try {
                lPC.addIceCandidate(candidate);
            } catch (err) {
                if (!(typeof(err, SyntaxError) || typeof(err, TypeError))) throw err;
            }
        },
        remoteId);

    console.log("rtc: we got basic objects");
    return lPC;
}


