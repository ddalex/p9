/* vim: set tabstop=4 expandtab softab: */
//var HOMEURL = "http://localhost:8000";
var HOMEURL = "";

var _smsMsgCallbacks = {}
// start at most 5 seconds ago
var lastRefreshId = 0;

var smsDebug = 0;

function _smsCreateUUID() {
    // http://www.ietf.org/rfc/rfc4122.txt
    var s = [];
    var hexDigits = "0123456789abcdef";
    for (var i = 0; i < 36; i++) {
        s[i] = hexDigits.substr(Math.floor(Math.random() * 0x10), 1);
    }
    s[14] = "4";  // bits 12-15 of the time_hi_and_version field to 0010
    s[19] = hexDigits.substr((s[19] & 0x3) | 0x8, 1);  // bits 6-7 of the clock_seq_hi_and_reserved to 01
    s[8] = s[13] = s[18] = s[23] = "-";

    var uuid = s.join("");
    return uuid;
}

var smsMyId = _smsCreateUUID();

// just for debug
(function (){
 if(smsDebug)console.log("My ID is ", smsMyId);
})();

function smsGetMessages(f) {
    var myRequest = new XMLHttpRequest();

    myRequest.onreadystatechange = function() {
        if (myRequest.readyState == XMLHttpRequest.DONE && myRequest.status == 200) {
            f(JSON.parse(myRequest.responseText));
        }
    };
    myRequest.open("GET", HOMEURL+"/messages?s="+encodeURIComponent(smsMyId)+"&since=" + encodeURIComponent(lastRefreshId), true);
    myRequest.send();
}

function smsPostMessage(recipient, type, data, f ) {

    if (f === undefined)
        f = _smsProcessMessages;

    if (data === undefined)
        throw "smsPostMessage: Must specify data to be sent"

    if (type === undefined)
        throw "smsPostMessage: Must specify message type"

    if (recipient === undefined)
        throw "smsPostMessage: Cannot send message without recipient";

    var myRequest = new XMLHttpRequest();

    myRequest.onreadystatechange = function() {
        if (myRequest.readyState == XMLHttpRequest.DONE && myRequest.status == 200) {
            f(JSON.parse(myRequest.responseText));
        }
    };
    myRequest.open("POST", HOMEURL+"/messages?s=" + encodeURIComponent(smsMyId) + "&since=" + encodeURIComponent(lastRefreshId), true);
    myRequest.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    myRequest.send("r=" + encodeURIComponent(recipient) + "&t="+encodeURIComponent(type)+"&d=" + encodeURIComponent(data));
}

function smsRegisterCallback(msgtype, callable, sender) {
    o = { sender: sender, callable: callable }
    if(smsDebug)console.log("sms: registering callback for " + msgtype + " : ", o);
    if (msgtype in _smsMsgCallbacks) {
        _smsMsgCallbacks[msgtype].push(o);
    } else {
        _smsMsgCallbacks[msgtype] = [o];
    }
    return _smsMsgCallbacks[msgtype].indexOf(o);
}

function smsUnregisterCallback(msgtype, idx) {
    console.log("sms: updating " + msgtype + " pos ", idx);
    _smsMsgCallbacks[msgtype].splice(idx, 1);
}

function _smsDispatchMessage(type, sender, data) {
    if (type in _smsMsgCallbacks) {
        if(smsDebug)console.log("sms: callbacks for " + type, sender, _smsMsgCallbacks[type]);
        for (i = 0; i < _smsMsgCallbacks[type].length; i++) {
                f = _smsMsgCallbacks[type][i].callable
                s = _smsMsgCallbacks[type][i].sender
                if (s == sender || s === undefined) {
                if(smsDebug)console.log("sms:   matched " + i + " filter ", _smsMsgCallbacks[type][i]);
                     f(sender, data);
                }
        }
    }
}

function _smsProcessMessages(data) {
    for (m in data) {
        if (data[m].c > lastRefreshId) {
            lastRefreshId = data[m].c;
        }
        _smsDispatchMessage(data[m].t, data[m].s, data[m].d);
    }
}

function _smsUpdateClient(isdead) {
    if (isdead == undefined)
        isdead = 0;

    var myRequest = new XMLHttpRequest();

    myRequest.open("POST", HOMEURL+"/clients?s=" + encodeURIComponent(smsMyId), false);
    myRequest.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    myRequest.send("x="+encodeURIComponent(isdead));
}

function smsListClients(f) {
    var myRequest = new XMLHttpRequest();

    myRequest.onreadystatechange = function() {
        if (myRequest.readyState == XMLHttpRequest.DONE && myRequest.status == 200) {
            f(JSON.parse(myRequest.responseText));
        }
    };
    myRequest.open("GET", HOMEURL+"/clients?s="+encodeURIComponent(smsMyId), true);
    myRequest.send();
}


var handle;        // this is the handle for the interative setInterval

function smsStartSystem() {
    if(smsDebug)console.log("starting system");
    _smsUpdateClient();        // signal we're alive
    handle = setInterval(function() {
            smsGetMessages( _smsProcessMessages ) },
            1000);
}

function smsStopSystem() {
    clearInterval(handle);
    handle = undefined;
    _smsUpdateClient(1);        // mark dead client
}

