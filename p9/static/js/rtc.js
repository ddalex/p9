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


/** 
    returns a modified RTCPeerConnection to the specified partner.
    if the role is RECEIVER, the partner may be unknown
*/
function rtcGetConnection(role, remoteId) {

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
            console.log("rtc: data Channel: 1" , evt);
        }


        lPC.onicecandidate = function(evt) {
            if (evt.candidate != null) {
                console.log("rtc: 0: got ice candidate", evt.candidate);
                smsPostMessage(lPC.remoteId, "candidate", JSON.stringify(evt.candidate));
            }
        }

        lPC.onconnecting = function(evt) {
            console.log("rtc: 2: !" , evt);
        }

        lPC.onopen = function(evt) {
            console.log("rtc: 3: !" , evt);
        }

        lPC.ondatachannel = function(evt) {
            console.log("rtc: 4: !" , evt);
        }

        lPC.oniceconnectionstatechange = function(evt) {
            console.log("rtc: 5: !" , evt);
            console.log("rtc: Ice connection state: ", this.iceConnectionState);
        }

        lPC.onnegotiationneeded = function (evt) {
            if (lPC.role == ROLE.CALLER) {
                lpc.createSDPResponse();
            }
        }

        function localDescriptionCallback(sdp) {
            console.log("rtc: we got local description", sdp);
            lPC.setLocalDescription(sdp,
                function () {
                    console.log("rtc: sending local description ", sdp);
                    smsPostMessage("sdp", JSON.stringify(sdp)); // success, we post our description
                },
                function (error) { console.log("rtc: ERR: setLocalDescription ", error) } // errorCallback
        )}

        lPC.createSDPResponse = function () {
            var mediaConstraints = {
                optional: [],
                mandatory: {
                    OfferToReceiveAudio: false, // Hmm!!
                    OfferToReceiveVideo: false // Hmm!!
                }
            };
            if (lPC.role == ROLE.CALLER) {
                console.log("rtc: .. Creating Offer");
                lPC.createOffer(localDescriptionCallback,function (error) { console.log(error) }, mediaConstraints);
            }
            else if (lPC.role == ROLE.RECEIVER) {
                console.log("rtc: .. Creating Answer");
                lPC.createAnswer(localDescriptionCallback,function (error) { console.log(error) } , mediaConstraints);
            }
            else {
                console.log("rtc: Role undefined, no idea what to do");
            }
        }

        lPC.onsignalingstatechange = function(evt) {
            console.log("rtc: signalstatechange: !" , this.signalingState);
        }

        lPC.onaddstream = function(evt) {
            console.log("rtc: remoteaddedstream: !" , evt);
        }

        lPC.onremovestream = function(evt) {
            console.log("rtc: remoteremovedstream: !" , evt);
        }

        return lPC;
}


</script>

<script>
/**
    Start the system when the page is loaded.
*/

function logoutput(text) {
    $('#output').text(text + "<br/>" + $('#output').text());
}


