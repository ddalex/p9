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

    $scope.triggerDisconnect = function (r) {
        console.log("trigger disconnection");
         // TODO: trigger rtc disconnect
         r.lpc.close();
         $scope.removeConnection(r);
    }

    $scope.triggerConnect = function (r) {
        console.log("trigger connection to ", r);
        $scope.addConnection(r);

        $scope._callRemote(r, $scope._p2pConnectionStateChange,
            function (data) {
                       console.log("recv " + data);
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
        setTimeout(function() { smsListClients($scope.updateRemoteClients); }, 2500);

        $scope.$digest();
    }


    /**
    *       media       
    */

    $scope._hasVideo = false;
    $scope._stream = undefined;

    $scope._streamCB = function (stream, op) {
        if (op === "add") {
            var video = document.querySelector('#localVideo');
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

});   // end of controller scope


function ext_updateRemoteClients(scope, clients) {
    scope.updateRemoteClients(clients);
    scope.$digest();
}

/**
    Start the system
*/

$(document).ready( function () {
    var scope = angular.element(document).scope();
    smsStartSystem();
    $('#localId').text(smsMyId);

    // for each client already existing, we will createOffers and send them
    smsListClients(function (clients) { ext_updateRemoteClients(scope, clients) });

    // wait calls
    console.log("we wait with id ", smsMyId);
    scope.callWait(scope._p2pConnectionStateChange, function (data) {
                       console.log("recv " + data);
            })

});

window.onbeforeunload = function () {
    console.log("almost dead");
    smsStopSystem();
};



