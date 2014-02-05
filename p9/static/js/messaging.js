/* vim: set tabstop=4 expandtab softab */
var msgCallbacks = {}
var lastRefreshTime = 0;

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

var myId = _smsCreateUUID();

// just for debug
(function (){
 console.log("My ID is ", myId);
 })();

function smsGetMessages(f) {
	var myRequest = new XMLHttpRequest();

	myRequest.onreadystatechange = function() {
		if (myRequest.readyState == XMLHttpRequest.DONE && myRequest.status == 200) {
			f(JSON.parse(myRequest.responseText));
		}
	};
	myRequest.open("GET", "http://localhost:8000/messages?s="+encodeURIComponent(myId)+"&since=" + encodeURIComponent(lastRefreshTime), true);
	myRequest.send();
}

function smsPostMessage(type, info, f ) {
	var myRequest = new XMLHttpRequest();
	if (f == undefined)
		f = _smsProcessMessages;

	myRequest.onreadystatechange = function() {
		if (myRequest.readyState == XMLHttpRequest.DONE && myRequest.status == 200) {
			console.log("POST: ", myRequest.responseText);
			f(JSON.parse(myRequest.responseText));
		}
	};
	myRequest.open("POST", "http://localhost:8000/messages?s=" + encodeURIComponent(myId), true);
	myRequest.setRequestHeader("Content-type","application/x-www-form-urlencoded");
	myRequest.send("t="+encodeURIComponent(type)+"&d=" + encodeURIComponent(info));
}

function smsRegisterCallback(msgtype, callable) {
	if (msgtype in msgCallbacks) {
		msgCallbacks[msgtype].concat([callable]);
	} else {
		msgCallbacks[msgtype] = [callable];
	}
	return callable;
}

function _smsDispatchMessage(type, data) {
	if (type in msgCallbacks)
		for (f in msgCallbacks[type]) {
			msgCallbacks[type][f](data);
		}
}

function _smsProcessMessages(data) {
	for (m in data) {
		if (data[m].c > lastRefreshTime) {
			lastRefreshTime = data[m].c;
			_smsDispatchMessage(data[m].t, data[m].d);
		}
	}
}

var handle;		// this is the handle for the interative setInterval

function smsStartSystem() {
	console.log("starting system");
	handle = setInterval(function() { 
			smsGetMessages( _smsProcessMessages ) },   
			1000);
}

function smsStopSystem() {
}

