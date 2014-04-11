// vim: set tabstop=4 expandtab ai:

visionApp.controller('viewCtrl', function($scope, $http, $q) {
    // both arrays hold "r" objects
    $scope.peers = [];
    $scope.remotes = [];

    // we need to build an 'r' object and call this with stateCB and data dataCB
    $scope._callRemote = function (r, stateCB, dataCB) {
        console.log("main: we call ", r.s);
        $scope.broadcast_status = "CONNECTING";
        r.lpc = rtcGetConnection( ROLE.CALLER, r.s, function (state) { stateCB(r, state); }, $scope._streamCB, dataCB);
    }

    // waiting generates it's own r when it receives a call
    $scope.callWait = function (stateCB, dataCB) {
        // we want to receive calls
        
        function _receiveSDP(sender, message) {
            function _remoteForSender() {
                var i;
                for (i = 0; i < $scope.remotes.length; i++) 
                    if ($scope.remotes[i].s == sender) {
                        return $scope.remotes[i];
                    }
                return undefined;
            }

            function _setRtcConnection(r) {
                console.log("got remote call from ", r, msg);
    
                r.lpc = rtcGetConnection( ROLE.RECEIVER, sender, function(state) { stateCB(r, state); }, 
                        function(stream, op){}, dataCB );
                r.lpc.addStream($scope._stream);
                r.lpc.setRemoteDescription(r.lpc.buildSessionDescription(msg),
                    function () {
                        console.log("success setting remote");
                        r.lpc.createSDPResponse();
                    }, console.log); // we got another peer's offer
            }

            var msg = JSON.parse(message);
            // SDPs from already connected peers are to be ignored
            for (i = 0; i < $scope.peers.length; i++)
                if ($scope.peers[i].s == sender)
                    return;

            var r = _remoteForSender();

            if (r === undefined) {
                // fetch new remotes from the server
                console.log("fetching channelrelays");
                $http.get ("/api/1.0/channel/" + $scope.channel_id + "/relay?" + $.param({s: $scope.local_id}))
                  .success(
                    function (data) {
                        console.log("got channel relays", data);
                        var j;
                        $scope.remotes = [];
                        for (j = 0; j < data.length; j++) {
                          if (data[j].s != $scope.local_id) {
                            r = new Object();
                            r.s = data[j].s;
                            if ($scope.peers._indexOfS(r) == -1) {
                                $scope.remotes.push(r);
                            }
                          }
                        }
                        r = _remoteForSender();
                        if (r != undefined)
                            _setRtcConnection(r);
                    }
                )
                .error(
                    function() { console.log("error") }
                );
            } else {
                _setRtcConnection(r);
            }
         }
         
         smsRegisterCallback("sdp", _receiveSDP);
    }



    $scope._p2pConnectionStateChange = function (r, state) {
        // if r in remotes, we expect a connect
        if ( $scope.remotes._indexOfS(r) >= 0 ) {
            // we process the connect request
            if (state === "connected") {
                console.log("p2p: we have a connection ");
                $scope.addConnection(r);
                $scope.$digest();
            
                $scope.callWait(
                function(r, state) { console.log("p2p: incoming call state updated", r, state);  $scope._p2pConnectionStateChange(r, state); }, 
                function(data) { console.log("p2p: incoming call data callback", data); }
            );
}
        }
        // if r in peers, we expect a disconnect
        else if ( $scope.peers._indexOfS(r) >= 0 ) {
            if (state === "disconnected") {
                console.log("p2p: remote disconnected ");
                $scope.removeConnection(r);
                $scope.$digest();
            }
        }
        else {
          console.log("p2p: got a ", state, " for ", r);
        }
    }

    $scope.doDisconnect = function (r) {
        console.log("trigger disconnection");
         // TODO: trigger rtc disconnect
         r.lpc.close();
         $scope.removeConnection(r);
    }

    $scope.doConnect = function (r) {
        $scope.broadcast_status = "STARTING CONNECTION";
        console.log("trigger connection to ", r);
        $scope._callRemote(r, 
            function(r, state) { 
                $scope.broadcast_status = state;
                console.log("p2p: outgoing call state updated", r, state);
                $scope._p2pConnectionStateChange(r, state);
            },
            function(data) {
                console.log("p2p: outgoing call data callback", data);
            });

    }


    $scope.removeConnection = function (c) {
        $http.post("/api/1.0/channel/"+$scope.channel_id+"/relay?" + $.param({s: $scope.local_id}),
            {'x': 1}).success( function(data) {
        var p = $scope.peers._indexOfS(c);
        if (p > -1) {
            $scope.peers.splice(p, 1);
        }

        var p = $scope.remotes._indexOfS(c);
        if (p == -1)
          $scope.remotes.push(p);
        });
    }

    $scope.crtconnection = undefined;
    $scope.addConnection = function (c) {
        $http.post("/api/1.0/channel/"+$scope.channel_id+"/relay?" + $.param({s: $scope.local_id}),
            {'x': 0}).success( function(data) {
        var p = $scope.peers._indexOfS(c);
        if (p == -1)
            $scope.peers.push(c);

        var p = $scope.remotes._indexOfS(c);
        if (p > -1)
          $scope.remotes.splice(p, 1);
        });

        $scope.crtconnection = c;
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
        $scope.broadcast_status = "REGISTERING";
        $http.post("/api/1.0/channel/"+$scope.channel_id+"/relay?" + $.param({s: $scope.local_id})).success(
            function(retval) { 
            try {
                console.log("channel relay list", retval);
                if (retval.error) {
                    $scope.alertAdd("danger", retval.error);
                    console.log("error while receiving data", retval.error);
                } else {
                    var i;
                    $scope.remotes = [];
                    for (i = 0; i < retval.length; i++) {
                        if (retval[i].x == 0) {   // we only connect to STATUS_ALIVE remotes
                            var c = new Object();
                            c.s = retval[i].s;
                            $scope.remotes.push(c);
                        }
                    }
                    // TODO: do a better algorithm of selecting connecting peer
                    var r = $scope.remotes[0];
                    console.log("remotes: ", $scope.remotes );
                    if (r === undefined) throw "Cannot find alive peer";
                    $scope.doConnect(r);
                } 
            } catch (e) {
                $scope.broadcast_status = e;
            }
            }
        )
    }
    $scope.stopStreaming = function() {
        if ($scope.crtconnection)
           $scope.removeConnection($scope.crtconnection); 
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
            console.log("stateCB: got stream ", stream);
            url = window.URL.createObjectURL(stream);
            console.log("stateCB: localstream URL ",  url);
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

    
    $scope.broadcast_status = "WAITING";

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
    var scope = angular.element("div#main").scope();
    scope.stopStreaming();
    smsStopSystem();
};

