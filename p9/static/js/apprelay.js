// vim: set tabstop=4 expandtab ai:

visionApp.controller('viewCtrl', function($scope, $http, $q) {
    // both arrays hold "r" objects
    $scope.peers = [];
    $scope.remotes = [];

    // we need to build an 'r' object and call this with stateCB and data dataCB
    $scope._callRemote = function (r, stateCB, dataCB) {
        console.log("main: we call ", r.s);
        r.lpc = rtcGetConnection( ROLE.CALLER, r.s, function (state) { stateCB(r, state); }, $scope._streamCB, dataCB);
    }

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

            r.lpc = rtcGetConnection( ROLE.RECEIVER, sender, function(state) { stateCB(r, state); }, $scope._streamCB, dataCB );
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

    $scope.doDisconnect = function (r) {
        console.log("trigger disconnection");
         // TODO: trigger rtc disconnect
         r.lpc.close();
         $scope.removeConnection(r);
    }

    $scope.doConnect = function (r) {
        console.log("trigger connection to ", r);
        $scope.addConnection(r);
        $scope._callRemote(r, 
            function(r, state) { 
                console.log("we have state", r, state);
            },
            function(data) {
                console.log("we have data", data);
            });

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
    }


    $scope.startStreaming = function() {
        // retrieve client list for this channel
        $http.get("/api/1.0/channelrelaylist?" + $.param({s: $scope.local_id, channel: $scope.channel_id}))
            .success(function (retval) {
                console.log("channel relay list", retval);
                if (retval.error) {
                    $scope.alertAdd("danger", retval.error);
                    throw "error while receiving data";
                } else {
                    var c = new Object();
                    c.s = retval[0];
                    $scope.remotes.push(c);
                    $scope.doConnect(c);
                }

            });
    }

    /**
    *       media       
    */

    $scope._hasVideo = false;
    $scope._stream = undefined;

    $scope._streamCB = function (stream, op) {
        if (op === "add") {
            var video = document.querySelector('video#video');
            $scope._stream = stream;
            console.log("got stream ", stream);
            url = window.URL.createObjectURL(stream);
            console.log("localstream URL ",  url);
            video.src = url;
            video.onloadedmetadata = function(e) {
                $scope._hasVideo = true;
                video.play();
            };
        }
        else if (op === "remove") {
        }
        else {
            throw "Invalid stream op ";
        }
    }

    $scope.triggerBroadcast = function () {
        if ($scope._hasVideo === true) {
          return;
        }
        console.log("Get local video");
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
              $scope._streamCB(localMediaStream, "add");
           },
        
           // errorCallback
           function(err) {
            console.log("The following error occured: " + err);
           }
        
          );

    }

    /**
     *  UI logic
     *
     */

    $scope.all_alerts = [];
    $scope.channel_name = undefined;
    $scope.alertAdd = function(type, msg) {
        var lalert ={'type': type, 'msg': msg};
        console.log(lalert);
        return $scope.all_alerts.push(lalert);
    }
    $scope.alertClose = function(idx) {
        $scope.all_alerts.splice(idx, 1);
    }



});   // end of controller scope



/**
    Start the system
*/

$(document).ready( function () {
    var scope = angular.element("div#main").scope();

    scope.local_id  = smsMyId;
    smsStartSystem();
    scope.startStreaming();

});

window.onbeforeunload = function () {
    console.log("almost dead");
    smsStopSystem();
};



