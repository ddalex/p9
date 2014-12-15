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
    var config;

//    if (navigator.mozGetUserMedia) {
        config = {
            iceServers: [
                { "url": "stun:stun.l.google.com:19302" },
                { "url": "stun:stun.services.mozilla.com" },
                { "url": "turn:turn01.ddns01.com", "username": "test", "credential": "pass"  },
            ]
        };
  //  } else {
  //      config = {
  //          iceServers: [
  //              { url: 'stun:stun.l.google.com:19302' },
  //          ]
  //      }
  //   }



    var _RTCPeerConnection = undefined;
    if (window.RTCPeerConnection != undefined)
            _RTCPeerConnection =  window.RTCPeerConnection
    else if (window.mozRTCPeerConnection != undefined)
            _RTCPeerConnection =  window.mozRTCPeerConnection
    else if (window.webkitRTCPeerConnection != undefined)
            _RTCPeerConnection =  window.webkitRTCPeerConnection
    else throw "Your browser will not work - it is missing RTCPeerConnection. Please use Chrome.";

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
       // if(rtcDEBUG)console.log("rtc", "data Channel: 1", evt);
    // }

    // lPC.sendChannel.onmessage = onDRecvCB;

    lPC.onicecandidate = function(evt) {
        if (evt.candidate != null) {
            smsPostMessage(lPC.remoteId, "candidate", JSON.stringify(evt.candidate));
        }
    }

    lPC.onconnecting = function(evt) {
        if(rtcDEBUG)console.log("rtc", "2: !", evt);
    }


    lPC.onopen = function(evt) {
        if(rtcDEBUG)console.log("rtc", "3: !", evt);
    }

    lPC.ondatachannel = function(evt) {
        if(rtcDEBUG)console.log("rtc", "4: !", evt);
    }

    lPC.oniceconnectionstatechange = function(evt) {
        if(rtcDEBUG)console.log(lPC.iceConnectionState, "Ice connection state: ", lPC.iceConnectionState);
        if (lPC.iceConnectionState === "disconnected" || lPC.iceConnectionState === "failed") {
            console.log("rtc", "Close callbacks");
            if (lPC.candidateCallback != undefined) {
                smsUnregisterCallback("candidate", this.candidateCallback);
                lPC.candidateCallback = undefined;
            }
            if (lPC.sdpCallback != undefined) {
                smsUnregisterCallback("sdp", lPC.sdpCallback);
                lPC.sdpCallback = undefined;
            }
            lPC.close();
        }
        if (onStateCB != undefined) onStateCB(this.iceConnectionState);
    }

    lPC.onnegotiationneeded = function (evt) {
        if (lPC.role == ROLE.CALLER) {
            lPC.createSDPResponse();
        }
    }

    function messageError(arguments) {
        console.log("rtc", arguments);
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

    function setDefaultCodec(mLine, payload) {
      var elements = mLine.split(' ');
      var newLine = [];
      var index = 0;
      for (var i = 0; i < elements.length; i++) {
        if (index === 3) { // Format of media starts from the fourth.
          newLine[index++] = payload; // Put target payload to the first.
        }
        if (elements[i] !== payload) {
          newLine[index++] = elements[i];
        }
      }
      return newLine.join(' ');
    }


    function setPreferAudioCodec(sdp, codec) {
      var sdpLines = sdp.split('\r\n');

      // Search for m line.
      var mLineIndex = findLine(sdpLines, 'm=', 'audio');
      if (mLineIndex === null) {
        return sdp;
      }

      // If the codec is available, set it as the default in m line.
      var codecIndex = findLine(sdpLines, 'a=rtpmap', codec);
      if (codecIndex) {
        var payload = getCodecPayloadType(sdpLines[codecIndex]);
        if (payload) {
          sdpLines[mLineIndex] = setDefaultCodec(sdpLines[mLineIndex], payload);
        }
      }

      sdp = sdpLines.join('\r\n');
      return sdp;
    }

    function setSendRecvline(sdp) {
        var sdpLines = sdp.split('\r\n');
        var i = findLine(sdpLines, "a=sendonly", '');
        while ( i != null ) {
            sdpLines[i] = "a=sendrecv";
            i = findLine(sdpLines, 'a=sendonly', '')
        }
        return sdpLines.join('\r\n');
    }

    function localDescriptionCallback(sdp) {
        if(rtcDEBUG)console.log("rtc", "acquired local description", sdp);
        if (lPC.role == ROLE.RECEIVER) { // we'll send video
            sdp.sdp = setVideoSendInitialBitRate(sdp.sdp, 900);
            sdp.sdp = setPreferAudioCodec(sdp.sdp, 'opus/48000');
            sdp.sdp = setSendRecvline(sdp.sdp);
            if(rtcDEBUG)console.log("rtc", "modified local description", sdp);
        }
        lPC.setLocalDescription(sdp,
            function () {
                if(rtcDEBUG)console.log("rtc", "sending local description ", sdp);
                smsPostMessage(remoteId, "sdp", JSON.stringify(sdp)); // success, we post our description
            },
            function (error) { if(rtcDEBUG)console.log("rtc", "ERR: setLocalDescription ", error) } // errorCallback
    )}

    lPC._stream = undefined;
    lPC.setStream = function(stream) {
        lPC._stream = stream;
    }

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
            if(rtcDEBUG)console.log("rtc", ".. Creating Offer");
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
            if(rtcDEBUG)console.log("rtc", ".. Creating Answer");
            lPC.createAnswer(localDescriptionCallback,function (error) { if(rtcDEBUG)throw(error) } , mediaConstraints);
        }
        else {
            if(rtcDEBUG)console.log("rtc", "Role undefined, no idea what to do");
        }
    }


    lPC.onsignalingstatechange = function(evt) {
        if (lPC.signalingState == "stable" && lPC._stream != undefined) {
            if(rtcDEBUG)console.log("rtc", "signalstatechange: ", lPC.signalingState);
            lPC.addStream(lPC._stream);
        }
    }

    lPC.onaddstream = function(evt) {
        if(rtcDEBUG)console.log("rtc", "remoteaddedstream: !", evt);
        onStreamCB(evt.stream, "add");
    }

    lPC.onremovestream = function(evt) {
        if(rtcDEBUG)console.log("rtc", "remoteremovedstream: !", evt);
        onStreamCB(undefined, "remove");
    }

    lPC.buildSessionDescription = function(msg) {
        return new _RTCSessionDescription(msg);
    }


//--------

//--------------------
    lPC.gotSDP = 0;

    lPC.setRemoteSDP = function (message, successCB, failCB ) {
            if (lPC.gotSDP) return;
            lPC.gotSDP = 1;
            msg = JSON.parse(message);
            if(rtcDEBUG)console.log("rtc", "negociation with our designed remote, received", msg);
            lPC.setRemoteDescription( new _RTCSessionDescription(msg),
                successCB !== undefined ? successCB : function () { if(rtcDEBUG)console.log("rtc", "success setting remote"); },
                failCB !== undefined ? failCB : function (err) { if(rtcDEBUG)console.log("rtc", err, message) }
            );
    }

    // we need to receive any renegociation from the remote ID
    lPC.sdpCallback = smsRegisterCallback("sdp", function (s,m) { if (s == remoteId) { lPC.setRemoteSDP(m);} }, remoteId);

    // we want to register the candidates from the remote partner
    lPC.candidateCallback = smsRegisterCallback("candidate", function recvCandidate(sender, message) {
            if (sender != remoteId)
            {
                throw "received candidate from invalid remote ";
                return;
            }
            msg = JSON.parse(message);
            //if(rtcDEBUG)console.log("rtc", "got candidate from remote ", sender, msg )
            var candidate = new _RTCIceCandidate({sdpMLineIndex: msg.sdpMLineIndex,
                                    candidate: msg.candidate});
            try {
                lPC.addIceCandidate(candidate,
                    function () {console.log("ice success ");},
                    function () {console.log("ice failure ");}
                );
            } catch (err) {
                if (!(typeof(err, SyntaxError) || typeof(err, TypeError))) throw err;
            }
        },
        remoteId);

    if (rtcDEBUG)console.log("rtc", "we got basic objects");
    return lPC;
}


