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


    lPC = new _RTCPeerConnection(iceServers, {optional: [{RtpDataChannels: false}]});

    lPC.role = role;
    lPC.remoteId = remoteId;

    // lPC.sendChannel = lPC.createDataChannel("data1", {reliable: false});
    // lPC.sendChannel.onopen = function(evt) {
       // if(rtcDEBUG)smsLog("rtc", " data Channel: 1" , evt);
    // }

    // lPC.sendChannel.onmessage = onDRecvCB;

    lPC.onicecandidate = function(evt) {
        if (evt.candidate != null) {
            smsPostMessage(lPC.remoteId, "candidate", JSON.stringify(evt.candidate));
        }
    }

    lPC.onconnecting = function(evt) {
        if(rtcDEBUG)smsLog("rtc", " 2: !" , evt);
    }


    lPC.onopen = function(evt) {
        if(rtcDEBUG)smsLog("rtc", " 3: !" , evt);
    }

    lPC.ondatachannel = function(evt) {
        if(rtcDEBUG)smsLog("rtc", " 4: !" , evt);
    }

    lPC.oniceconnectionstatechange = function(evt) {
        if(rtcDEBUG)smsLog("rtc", " Ice connection state: ", lPC.iceConnectionState);
        if (lPC.iceConnectionState === "disconnected") {
            smsLog("rtc", "Close callbacks");
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

    function alterSDP(sdp) {
        var t = sdp.sdp.split("\n");
        var i = 0;
        var mode = 0;
        var start = 0;
        var stop = 0;
        console.log("original sdp", [ sdp ]);
        for (i = 0; i < t.length; i++ ) {
            switch(mode) {
                case 0: // not encountered application
                    if (t[i].indexOf("m=application") == 0) {
                        mode = 1;   // mark removal start
                        start = i;
                    }
                break;
                case 1:
                    if (t[i].indexOf("m=") == 0) {
                        stop = i;
                        mode = 2;   // mark removing
                        break;
                    }
            }
        }
        t.splice(start, stop - start);
        sdp.sdp = t.join("\n");
        console.log("altered sdp", [ sdp ]);
        return sdp;
    }

    function localDescriptionCallback(sdp) {
        sdp = alterSDP(sdp);
        if(rtcDEBUG)smsLog("rtc", " acquired local description", sdp);
        lPC.setLocalDescription(sdp,
            function () {
                if(rtcDEBUG)smsLog("rtc", " sending local description ", sdp);
                smsPostMessage(remoteId, "sdp", JSON.stringify(sdp)); // success, we post our description
            },
            function (error) { if(rtcDEBUG)smsLog("rtc", " ERR: setLocalDescription ", error) } // errorCallback
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
            if(rtcDEBUG)smsLog("rtc", " .. Creating Offer");
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
            if(rtcDEBUG)smsLog("rtc", " .. Creating Answer");
            lPC.createAnswer(localDescriptionCallback,function (error) { if(rtcDEBUG)throw(error) } , mediaConstraints);
        }
        else {
            if(rtcDEBUG)smsLog("rtc", " Role undefined, no idea what to do");
        }
    }

    lPC.onsignalingstatechange = function(evt) {
        if(rtcDEBUG)smsLog("rtc", " signalstatechange: " , lPC.signalingState);
    }

    lPC.onaddstream = function(evt) {
        if(rtcDEBUG)smsLog("rtc", " remoteaddedstream: !" , evt);
        onStreamCB(evt.stream, "add");
    }

    lPC.onremovestream = function(evt) {
        if(rtcDEBUG)smsLog("rtc", " remoteremovedstream: !" , evt);
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
            if(rtcDEBUG)smsLog("rtc", " negociation with our designed remote, received", msg);
            lPC.setRemoteDescription( new _RTCSessionDescription(msg),
                function () { if(rtcDEBUG)smsLog("rtc", " success setting remote"); },
                function (err) { if(rtcDEBUG)throw(err) }
            );
        } ,
        remoteId);

    // we want to register the candidates from the remote partner
    lPC.candidateCallback = smsRegisterCallback("candidate", function recvCandidate(sender, message) {
            msg = JSON.parse(message);
            //if(rtcDEBUG)smsLog("rtc", " got candidate from remote ", sender, msg )
            var candidate = new _RTCIceCandidate({sdpMLineIndex: msg.sdpMLineIndex,
                                    candidate: msg.candidate});
            try {
                lPC.addIceCandidate(candidate);
            } catch (err) {
                if (!(typeof(err, SyntaxError) || typeof(err, TypeError))) throw err;
            }
        },
        remoteId);

    smsLog("rtc", " we got basic objects");
    return lPC;
}


