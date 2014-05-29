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
    var config = {
        iceServers: [
                    { url: 'stun:stun.l.google.com:19302' },
                    { url:"turn:192.158.30.23:3478?transport:udp", credential:"1401479939:78637771", username:"1401479939:78637771"},
                    { url:"turn:192.158.30.23:3478?transport:tcp", credential:"1401479939:78637771", username:"1401479939:78637771"},
                    { url:"turn:192.158.30.23:3479?transport:udp", credential:"1401479939:78637771", username:"1401479939:78637771"},
                    { url:"turn:192.158.30.23:3479?transport:tcp", credential:"1401479939:78637771", username:"1401479939:78637771"}
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


    lPC = new _RTCPeerConnection(config, {optional: [{RtpDataChannels: false}]});

    lPC.role = role;
    lPC.remoteId = remoteId;

    // lPC.sendChannel = lPC.createDataChannel("data1", {reliable: false});
    // lPC.sendChannel.onopen = function(evt) {
       // if(rtcDEBUG)smsLog("rtc", "data Channel: 1", evt);
    // }

    // lPC.sendChannel.onmessage = onDRecvCB;

    lPC.onicecandidate = function(evt) {
        if (evt.candidate != null) {
            smsPostMessage(lPC.remoteId, "candidate", JSON.stringify(evt.candidate));
        }
    }

    lPC.onconnecting = function(evt) {
        if(rtcDEBUG)smsLog("rtc", "2: !", evt);
    }


    lPC.onopen = function(evt) {
        if(rtcDEBUG)smsLog("rtc", "3: !", evt);
    }

    lPC.ondatachannel = function(evt) {
        if(rtcDEBUG)smsLog("rtc", "4: !", evt);
    }

    lPC.oniceconnectionstatechange = function(evt) {
        if(rtcDEBUG)smsLog("rtc", "Ice connection state: ", lPC.iceConnectionState);
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

function messageError(arguments) {
    smsLog("rtc", arguments);
}

// Find the line in sdpLines that starts with |prefix|, and, if specified,
// contains |substr| (case-insensitive search).
function findLine(sdpLines, prefix, substr) {
  return findLineInRange(sdpLines, 0, -1, prefix, substr)
}

// Find the line in sdpLines[startLine...endLine - 1] that starts with |prefix|
// and, if specified, contains |substr| (case-insensitive search).
function findLineInRange(sdpLines, startLine, endLine, prefix, substr) {
  var realEndLine = (endLine != -1) ? endLine : sdpLines.length;
  for (var i = startLine; i < realEndLine; ++i) {
    if (sdpLines[i].indexOf(prefix) === 0) {
      if (!substr ||
          sdpLines[i].toLowerCase().indexOf(substr.toLowerCase()) !== -1) {
        return i;
      }
    }
  }
  return null;
}

function preferBitRate(sdp, bitrate, mediaType) {
  var sdpLines = sdp.split('\r\n');

  // Find m line for the given mediaType.
  var mLineIndex = findLine(sdpLines, 'm=', mediaType);
  if (mLineIndex === null) {
    messageError('Failed to add bandwidth line to sdp, as no m-line found');
    return sdp;
  }

  // Find next m-line if any.
  var nextMLineIndex = findLineInRange(sdpLines, mLineIndex + 1, -1, 'm=');
  if (nextMLineIndex === null) {
    nextMLineIndex = sdpLines.length;
  }

  // Find c-line corresponding to the m-line.
  var cLineIndex = findLineInRange(sdpLines, mLineIndex + 1, nextMLineIndex,
                                   'c=');
  if (cLineIndex === null) {
    messageError('Failed to add bandwidth line to sdp, as no c-line found');
    return sdp;
  }

  // Check if bandwidth line already exists between c-line and next m-line.
  var bLineIndex = findLineInRange(sdpLines, cLineIndex + 1, nextMLineIndex,
                                   'b=AS');
  if (bLineIndex) {
    sdpLines.splice(bLineIndex, 1);
  }

  // Create the b (bandwidth) sdp line.
  var bwLine = "b=AS:"+ bitrate;
  // As per RFC 4566, the b line should follow after c-line.
  sdpLines.splice(cLineIndex + 1, 0, bwLine);
  sdp = sdpLines.join('\r\n');
  return sdp;
}

// Gets the codec payload type from an a=rtpmap:X line.
function getCodecPayloadType(sdpLine) {
  var pattern = new RegExp('a=rtpmap:(\\d+) \\w+\\/\\d+');
  var result = sdpLine.match(pattern);
  return (result && result.length == 2) ? result[1] : null;
}

function setVideoSendInitialBitRate(sdp, videoSendInitialBitrate) {

  // Validate the initial bitrate value.
  var maxBitrate = videoSendInitialBitrate;
  videoSendBitrate = videoSendInitialBitrate;
  if (videoSendBitrate) {
    if (videoSendInitialBitrate > videoSendBitrate) {
      messageError('Clamping initial bitrate to max bitrate of ' +
          videoSendBitrate + ' kbps.')
      videoSendInitialBitrate = videoSendBitrate;
    }
    maxBitrate = videoSendBitrate;
  }

  var sdpLines = sdp.split('\r\n');

  // Search for m line.
  var mLineIndex = findLine(sdpLines, 'm=', 'video');
  if (mLineIndex === null) {
    messageError('Failed to find video m-line');
    return sdp;
  }

  var vp8RtpmapIndex = findLine(sdpLines, "a=rtpmap", "VP8/90000")
  var vp8Payload = getCodecPayloadType(sdpLines[vp8RtpmapIndex]);
  var vp8Fmtp = "a=fmtp:"+ vp8Payload + "x-google-min-bitrate="+
     videoSendInitialBitrate.toString() + "; x-google-max-bitrate="+
     maxBitrate.toString();
  sdpLines.splice(vp8RtpmapIndex + 1, 0, vp8Fmtp);
  return sdpLines.join('\r\n');
}

    function localDescriptionCallback(sdp) {
        if(rtcDEBUG)smsLog("rtc", "acquired local description", sdp);
        if (lPC.role == ROLE.RECEIVER) { // we'll send video
            sdp.sdp = setVideoSendInitialBitRate(sdp.sdp, 900);
            if(rtcDEBUG)smsLog("rtc", "modified local description", sdp);
        }
        lPC.setLocalDescription(sdp,
            function () {
                if(rtcDEBUG)smsLog("rtc", "sending local description ", sdp);
                smsPostMessage(remoteId, "sdp", JSON.stringify(sdp)); // success, we post our description
            },
            function (error) { if(rtcDEBUG)smsLog("rtc", "ERR: setLocalDescription ", error) } // errorCallback
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
            if(rtcDEBUG)smsLog("rtc", ".. Creating Offer");
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
            if(rtcDEBUG)smsLog("rtc", ".. Creating Answer");
            lPC.createAnswer(localDescriptionCallback,function (error) { if(rtcDEBUG)throw(error) } , mediaConstraints);
        }
        else {
            if(rtcDEBUG)smsLog("rtc", "Role undefined, no idea what to do");
        }
    }

    lPC.onsignalingstatechange = function(evt) {
        if(rtcDEBUG)smsLog("rtc", "signalstatechange: ", lPC.signalingState);
    }

    lPC.onaddstream = function(evt) {
        if(rtcDEBUG)smsLog("rtc", "remoteaddedstream: !", evt);
        onStreamCB(evt.stream, "add");
    }

    lPC.onremovestream = function(evt) {
        if(rtcDEBUG)smsLog("rtc", "remoteremovedstream: !", evt);
        onStreamCB(undefined, "remove");
    }

    lPC.buildSessionDescription = function(msg) {
        return new _RTCSessionDescription(msg);
    }

    lPC.gotSDP = 0;
    // we need to receive any renegociation from the remote ID
    lPC.sdpCallback = smsRegisterCallback("sdp", 
        function (sender, message) {
            if (lPC.gotSDP) return;
            lPC.gotSDP = 1;
            msg = JSON.parse(message);
            if(rtcDEBUG)smsLog("rtc", "negociation with our designed remote, received", msg);
            lPC.setRemoteDescription( new _RTCSessionDescription(msg),
                function () { if(rtcDEBUG)smsLog("rtc", "success setting remote"); },
                function (err) { if(rtcDEBUG)smsLog("rtc", err, message) }
            );
        } ,
        remoteId);

    // we want to register the candidates from the remote partner
    lPC.candidateCallback = smsRegisterCallback("candidate", function recvCandidate(sender, message) {
            msg = JSON.parse(message);
            //if(rtcDEBUG)smsLog("rtc", "got candidate from remote ", sender, msg )
            var candidate = new _RTCIceCandidate({sdpMLineIndex: msg.sdpMLineIndex,
                                    candidate: msg.candidate});
            try {
                lPC.addIceCandidate(candidate);
            } catch (err) {
                if (!(typeof(err, SyntaxError) || typeof(err, TypeError))) throw err;
            }
        },
        remoteId);

    smsLog("rtc", "we got basic objects");
    return lPC;
}


