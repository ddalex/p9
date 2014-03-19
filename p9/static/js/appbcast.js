// vim: set tabstop=4 expandtab ai: 

Array.prototype._indexOfS = function(element) {
    var i;
    for (i = 0; i < this.length; i++)
        if (element.s === this[i].s)
            return i;
    return -1;
}


var visionApp = angular.module('vision', ['ui.bootstrap']);


visionApp.controller('viewCtrl', function($scope) {
    // both arrays hold "r" objects
    $scope.peers = [];
    $scope.remotes = [];
    $scope.hasVideo

    // waiting generates it's own r
    $scope.callWait = function (stateCB, dataCB) {
        // we want to receive calls
        smsRegisterCallback("sdp", function receiveSDP(sender, message) {
            var i;
            var msg = JSON.parse(message);
            // SDPs from already connected peers are to be ignored
            for (i = 0; i < $scope.peers.length; i++)
                if ($scope.peers[i].s == sender)
                    return;

            var r = undefined;
            for (i = 0; i < $scope.remotes.length; i++)
                if ($scope.remotes[i].s == sender) {
                  r = $scope.remotes[i];
                }

            if (r === undefined) {
              // we don't accept calls from unregistered peers
              throw "Cannot accept call from unknown peer " + sender;
            }
            console.log("got remote call from ", r, msg);

            // if we dont' have video, create it
            // for now, just refuse to answer
            if (! $scope._hasVideo ) {
              return;
            }

            r.lpc = rtcGetConnection( ROLE.RECEIVER, sender, function(state) { stateCB(r, state); }, $scope.streamCB, dataCB );
            // get local playback stream
            r.lpc.addStream($scope._stream);

            r.lpc.setRemoteDescription(r.lpc.buildSessionDescription(msg),
                function () {
                        console.log("success setting remote");
                        r.lpc.createSDPResponse();
                }, console.log); // we got another peer's offer
         });
    }


    $scope._p2pConnectionStateChange = function (r, state) {
        // if r in remotes, we expect a connect
        if ( $scope.remotes._indexOfS(r) >= 0 ) {
            // we process the connect request
            if (state === "connected") {
                console.log("we have a connection ");
                $scope.addConnection(r);
                $scope.$digest();
            }
        }
        // if r in peers, we expect a disconnect
        else if ( $scope.peers._indexOfS(r) >= 0 ) {
            if (state === "disconnected") {
                console.log("remote disconnected ");
                $scope.removeConnection(r);
                $scope.$digest();
            }
        }
        else {
          console.log("got a ", state, " for ", r);
        }
    }

    $scope.removeConnection = function (c) {
        var p = $scope.peers._indexOfS(c);
        if (p > -1) {
            $scope.peers.splice(p, 1);
        }

        var p = $scope.remotes._indexOfS(c);
        if (p == -1)
          $scope.remotes.push(p);
    }

    $scope.addConnection = function (c) {
        var p = $scope.peers._indexOfS(c);
        if (p == -1)
            $scope.peers.push(c);

        var p = $scope.remotes._indexOfS(c);
        if (p > -1)
          $scope.remotes.splice(p, 1);
    }

    $scope.updateRemoteClients = function(clients) {
        if (clients === undefined)
            return;

        $scope.remotes = [];

        for (i = 0 ; i < clients.length; i++) {
            j = clients[i];
            if (j.s != smsMyId && $scope.peers._indexOfS(j) < 0) {
                $scope.remotes.push(j);
            }
        }

        for (i = 0; i < $scope.peers.length; i++) {
            if (clients._indexOfS($scope.peers[i]) < 0) {
                    $scope.removeConnection($scope.peers[i])
            }
        }


        // we will refresh the client list
        setTimeout(function() { smsListClients($scope.updateRemoteClients); }, 2500);

        $scope.$digest();
    }


    /**
    *       media       
    */

    $scope._hasVideo = false;
    $scope._stream = undefined;

    $scope.streamCB = function (stream, op) {
        if (op === "add") {
            // we got a video stream, let's display it
            var video = angular.element('video#video')[0];
            $scope._stream = stream;
            console.log("streamCB: got stream ", stream);
            url = window.URL.createObjectURL(stream);
            console.log("streamCB: localstream URL ",  url);
            video.src = url;
            video.onloadedmetadata = function(e) {
                $scope._hasVideo = true;
                video.play();
            };

            // we have video, let's wait for calls
            console.log("streamCB: we wait with id ", smsMyId);
            $scope.callWait($scope._p2pConnectionStateChange, function (data) {
                           console.log("recv " + data);
            });

            $scope.broadcast_status = "WAITING TO BROADCAST";
            $scope.$apply();
        }
        else if (op === "remove") {
            // TODO: disconnect all counterparts
            // TODO: close this channel
        }
        else {
            throw "streamCB: Invalid stream operation";
        }
    }

    /** 
     *  UI logic
     *
     */

        $scope.all_alerts = [
    { type: 'danger', msg: 'Oh snap! Change a few things up and try submitting again.' },
    { type: 'success', msg: 'Well done! You successfully read this important alert message.' }
  ];;
    $scope.channel_name = undefined;
    $scope.alertAdd = function(type, msg) {
        var lalert ={'type': type, 'msg': msg}; 
        console.log(lalert);
        return $scope.all_alerts.push(lalert);
    }
    $scope.alertClose = function(idx) {
        $scope.all_alerts.splice(idx, 1);
    }

    $scope.broadcast_status = "STOPPED";

    $scope.doBroadcast = function () {
        $scope.all_alerts = [];
        var fail = 0;
        // step 1. verify that we have enough data to start streaming
        // - we have video ?
        if ($scope._hasVideo !== true) {
	        $scope.alertAdd("danger", "You need to have video !");
            fail += 1;

        }
        // - we have channel setup ?
        if ($scope.channel_name === undefined) {
            $scope.alertAdd("danger", "There is no channel name. Please set the channel name to start broadcast.");
            fail += 2;
        }

        console.log("channel name is ", $scope.channel_name);

        if (fail > 0) {
            return;
        }

        // register the channel with the server

        // update the UI to mark broadcasting

        // update channel stats
    }

});   // end of controller scope


function ext_updateRemoteClients(scope, clients) {
    scope.updateRemoteClients(clients);
    scope.$digest();
}

function ext_getMedia(f) {
    if (f === undefined) { 
        throw "getMedia: Invalid success callback";
    }
    navigator.getMedia = ( navigator.getUserMedia ||
        navigator.webkitGetUserMedia ||
        navigator.mozGetUserMedia ||
        navigator.msGetUserMedia);

    navigator.getMedia (
  
         // constraints
         {
            video: true,
            audio: false, 
         },
  
         // successCallback
         function(localMediaStream) {
            f(localMediaStream, "add");
         },
  
         // errorCallback
         function(err) {
          // TODO: upload error to server
          console.log("getMedia: The following error occured: " + err);
         }
  
    );
}

/**
    Start the system
*/

$(document).ready( function () {

    var scope = angular.element("div#main").scope();

    ext_getMedia(scope.streamCB);
    scope.local_id  = smsMyId;
    scope.$apply();
    smsStartSystem();

});

window.onbeforeunload = function () {
    console.log("almost dead");
    // TODO: close the channel if we're broadcasting
    smsStopSystem();
};



