// vim: set tabstop=4 expandtab ai:

visionApp.controller('viewCtrl', function ($scope, $http, $q, $interval, $location) {
    // both arrays hold "r" objects
    $scope.peers = [];
    $scope.remotes = [];


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
                smsLog("bcast", "got remote call from ", r, msg);
    
                r.lpc = rtcGetConnection( ROLE.RECEIVER, sender, function(state) { stateCB(r, state); }, $scope.streamCB, dataCB );
                r.lpc.addStream($scope._stream);
                r.lpc.setRemoteDescription(r.lpc.buildSessionDescription(msg),
                    function () {
                        smsLog("bcast", "success setting remote");
                        r.lpc.createSDPResponse();
                    }, console.log); // we got another peer's offer
            }

            var msg = JSON.parse(message);
            // SDPs from already connected peers are to be ignored
            for (i = 0; i < $scope.peers.length; i++) {
                if ($scope.peers[i].s == sender) {
                    return;
                }
            }

            var r = _remoteForSender();

            if (r === undefined) {
                // fetch new remotes from the server
                smsLog("bcast", "fetching channelrelays");
                $http.get ("/api/1.0/channel/" + $scope.channel_id + "/relay?" + $.param({s: $scope.local_id}))
                  .success(
                    function (data) {
                        smsLog("bcast", "got channel relays", data);
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
                    function() { smsLog("bcast", "error fetching channelrelays") }
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
                smsLog("bcast", "p2p: we have a connection ");
                $scope.addConnection(r);
                $scope.$digest();
            }
        }
        // if r in peers, we expect a disconnect
        else if ( $scope.peers._indexOfS(r) >= 0 ) {
            if (state === "disconnected") {
                smsLog("bcast", "p2p: remote disconnected ");
                $scope.removeConnection(r);
                $scope.$digest();
            }
        }
        else {
          smsLog("bcast", "p2p: unknown - got a ", state, " for ", r);
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

        $scope.broadcast_usersno = $scope.peers.length;
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

    $scope._stream = undefined;

    $scope.streamCB = function (stream, op) {
        if (op === "add") {
            // we got a video stream, let's display it
            var video = angular.element('video#video')[0];
            $scope._stream = stream;
            url = window.URL.createObjectURL(stream);
            smsLog("bcast", "got local stream ", stream, "url ", url);
            video.src = url;
            video.onloadedmetadata = function(e) {
                video.play();
            };
        }
        else if (op === "remove") {
            // TODO: disconnect all counterparts
            // TODO: close this channel
        }
        else {
            throw "appbcast: streamCB: Invalid stream operation";
        }
    }

    /**
     *  UI logic
     *
     */

    $scope.all_alerts = [];
    $scope.channel_name = undefined;
    $scope.alertAdd = function(type, msg) {
        var lalert ={'type': type, 'msg': msg};
        smsLog("bcast", "user facing alert", lalert);
        return $scope.all_alerts.push(lalert);
    }
    $scope.alertClose = function(idx) {
        $scope.all_alerts.splice(idx, 1);
    }

    var broadcastStatusEnum = {
        STOP: "STOPPED",
        BCAST: "BROADCASTING",
    }

    var bcastButtonLabelEnum = {
        STOP: "End Transmission",
        BCAST: "Start Transmission",
    }

    $scope.broadcast_status = broadcastStatusEnum.STOP;
    $scope.broadcast_button_label = bcastButtonLabelEnum.BCAST;

    $scope.broadcast_url = undefined;
    $scope.broadcast_usersno = 0;

    $scope._setStateBcast = function() {
                $scope.broadcast_status = broadcastStatusEnum.BCAST;
                $scope.broadcast_button_label = bcastButtonLabelEnum.STOP;
    }
    $scope._setStateStop  = function() {
                $scope.broadcast_status = broadcastStatusEnum.STOP;
                $scope.broadcast_button_label = bcastButtonLabelEnum.BCAST;
    }

    $scope.doButtonClick = function () {
        if ($scope.broadcast_status == broadcastStatusEnum.STOP) {
            $scope._bcastStart();
        }
        else if ($scope.broadcast_status == broadcastStatusEnum.BCAST) {
            $scope.bcastStop();
        }
        else
            throw "appbcast: Invalid action ! " + $scope.broadcast_status;
    }

    $scope.bcastStop = function () {
        $http.post("/api/1.0/channel?" + $.param({s : $scope.local_id}), {'channel' : $scope.channel_id, 's': 1})
            .success( function (data) {
                smsLog("bcast", "channeldel", data);
                // to do: drop p2p connections
                $scope._setStateStop();
            }
        )
    }

    $scope._bcastStart = function() {
        $scope.all_alerts = [];
        var promise = undefined;

        // step 1. verify that we have enough data to start streaming
        // - we have channel setup ?
        if ($scope.channel_name === undefined || $scope.channel_name.length < 3) {
            $scope.alertAdd("danger", "We need a channel name.");
            return;
        }
        if ($scope._stream === undefined) {
            promise = $scope.getLocalMedia();
        }
        else
        {
            var d = $q.defer();
            promise = d.promise;
            d.resolve({});
        }

        // step 2. we have all that's needed
	    promise.then(
                // make the call to the server
                function(data) {
                    if ($scope._stream === undefined) { $scope.streamCB(data.data, data.msg); }
                    // register the channel with the server
                    return $http.post("/api/1.0/channel?" + $.param({s : $scope.local_id}), {'name' : $scope.channel_name, 'x': 0});
                },
                function(data) {
                    $scope.alertAdd("danger", "We do not have a local video.");
                    smsLog("bcast", data);
                }
        ).then( function (retval) {
            // we got call result back
            smsLog("bcast", "channeladd", retval);
            if ('error' in retval.data) {
                $scope.alertAdd("danger", retval.data.error);
                smsLog("bcast", "error while receiving data", retval);
            }
            $scope.channel_id = undefined;
            var i;
            for (i = 0; i < retval.data.length; i++) {
                if (retval.data[i].name == $scope.channel_name) {
                    $scope.channel_id = retval.data[i].channel;
                    break;
                }
            }

            if ($scope.channel_id === undefined) {
                $scope.alertAdd("danger", "Registration failed");
                return;
            }

            // we set up the channel on the remote, update the UI
            $scope.broadcast_url = $location.protocol() + "://" + $location.host() + ":" + $location.port + "/channelview/"+$scope.channel_id + "/";

            $scope.callWait(
                function(r, state) { smsLog("bcast", "incoming call state updated", r, state);  $scope._p2pConnectionStateChange(r, state); }, 
                function(data) { smsLog("bcast", "incoming call data callback", data); }
            );
            // update the UI to mark broadcasting
            $scope._setStateBcast();
        },  function (data) { 
            smsLog("bcast", "channel add failed ", data);
        });
    }


    $scope.getLocalMedia = function () {

        var deffered = $q.defer();

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
                 deffered.resolve({msg: 'add', data: localMediaStream});
             },

             // errorCallback
             function(err) {
                smsLog("bcast", "The following error occured: " + err);
                deffered.reject({msg:'err', data: err});
             }

        );
        return deffered.promise;
    }

});   // end of controller scope
/**
    Start the system
*/

$(document).ready( function () {

    var scope = angular.element("div#main").scope();

    scope.local_id  = smsMyId;
    smsStartSystem();
    scope.getLocalMedia().then(function (data) {scope.streamCB(data.data, data.msg); }) ;

});

window.onbeforeunload = function () {
    smsLog("bcast", "application closing");
    // TODO: close the channel if we're broadcasting
    var scope = angular.element("div#main").scope();
    scope.bcastStop();
    smsStopSystem();
};


