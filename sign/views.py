# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from datetime import datetime, timedelta
import time
import json

from sign.models import Message, Client
from sign.models import Channel, ChannelRelay

# parameter names definition
PARAM_ERROR = 'error'
PARAM_CHANNEL = 'channel'
PARAM_CHANNELNAME = 'channel_name'


class CallError(Exception):
    pass

def must_have_externid(function):
    def wrapper(request, *args, **kwargs):
        try:
            if not 's' in request.GET.keys():
                raise ValidationError("Must specify client Id")
            return function(request, *args, **kwargs)
        except ValidationError as e:
            response = HttpResponse(json.dumps({PARAM_ERROR : str(e)}), content_type = "application/json")
            response.status_code=403
            return response

    return wrapper

def must_have_aliveclient(function):
    def wrapper(request, *args, **kwargs):
        try:
            crtclient = Client.objects.get(externid=request.GET['s'], status = Client.STATUS_ALIVE)
            crtclient.updated = datetime.now()
            crtclient.save()
            return function(request, *args, client = crtclient, **kwargs)
        except Client.DoesNotExist as e:
            response = HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")
            response.status_code = 403
            return response

    return wrapper


def client_disconnect(clientlist):
    for c in clientlist:
        c.status = Client.STATUS_DEAD
        c.save()
    # TODO: delete all channel-related information

# messaging system

@csrf_exempt
@must_have_externid
def xhr_client(request):
    '''
    Clients API:
        GET: list alive clients
            no parameters
            returns list of alive clients, including self

        POST: create / update client
            GET parametr 's' Mandatory - the client ID
            POST parameter 'x' - the status; default:0 - alive, 1 - dead
            return list of alive clients, including self
    '''
    try:
        if request.method == "POST":
            client_disconnect(Client.objects.filter(status=0).filter(updated__lt = datetime.now() - timedelta(seconds = 10)))

            # update client
            crtclient, created = Client.objects.get_or_create(
                    externid=request.GET['s'],
                )
            if not created:
                if crtclient.status == Client.STATUS_ALIVE:
                    raise CallError("Client already registered")

            crtclient.status = request.POST.get('x', 0)
            crtclient.updated = datetime.now()
            crtclient.save()

        # list currently alive clients
        clients = Client.objects.filter(status = Client.STATUS_ALIVE).order_by("-updated")
        return HttpResponse(json.dumps([{"s" : x.externid} for x in clients]), content_type='application/json')
    except CallError as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")


@must_have_externid
@must_have_aliveclient
@csrf_exempt
def xhr_message(request, **kwargs):
    '''
    Messages API:
        Restriction: must have an alive client;
        GET: list available mesesages
            's' Mandatory - client id
            'since' Optional - the last message index that was processed on client side

        POST: submit a new message
            GET parameter 's' Mandatory - the client id
            POST parameter 'r' Mandatory - receiver client id, must be alive !
            POST parameter 't' Mandatory - message type
            POST parameter 'd' Mandatory - message data
    '''

    client = kwargs['client']
    if request.method == "POST":
        try:
            rl = Client.objects.get(status = Client.STATUS_ALIVE, externid = request.POST.get('r',''))

            msg = Message.objects.get_or_create(
                    client  = client,
                    recipient = rl,
                    msgtype = request.POST['t'],
                    content = request.POST['d'],
                    created = datetime.now(),
                    );
        except Client.DoesNotExist as e:
            response = HttpResponse(e, content_type = "application/json")
            response.status_code=403
            return response

    queryset = Message.objects.filter(client__status = Client.STATUS_ALIVE).filter(recipient = client)

    if 'since' in request.GET.keys() and float(request.GET['since']) > 0:
        msg = queryset.filter(id__gt=request.GET['since']).order_by("id")[:20]
    else:
        msg = queryset.order_by("id")[:20]
    return HttpResponse(json.dumps([{'s': x.client.externid, 't' : x.msgtype, 'd' : x.content, 'c' : x.id} for x in msg]),
      content_type="application/json")



# UI rendering

def home(request):
    return render(request, 'home.html')

def channelview(request, channelid):
    return render(request, 'channelview.html')

def channeladd(request):
    return render(request, 'channeladd.html')

# UI interaction
@csrf_exempt    # TODO: remove after ALPHA stage, implement proper CSRF protection
@must_have_externid
@must_have_aliveclient
def xhr_channeladd(request, **kwargs):
    try:
        if request.method != "POST":
            raise CallError("must be POST-called")

        client = kwargs['client']
        channel_name = request.POST.get('name', '')
        if len(channel_name) == 0:
            raise CallError("did not get the name parameter")

        channel, created = Channel.objects.get_or_create(master = client, name = channel_name)
        if not created:
            if channel.status == Channel.STATUS_ALIVE or channel.master != client:
                raise CallError("channel already existing")
        channel.created = datetime.now()
        channel.save()

        return HttpResponse(json.dumps({'s': client.externid, PARAM_CHANNEL: channel.pk}), content_type = "application/json")
    except CallError as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")

@csrf_exempt    # TODO: remove after ALPHA stage, implement proper CSRF protection
@must_have_externid
@must_have_aliveclient
def xhr_channeldel(request, **kwargs):
    try:
        if request.method != "POST":
            raise CallError("must be POST-called")

        client = kwargs['client']
        channel_pk = int(request.POST.get(PARAM_CHANNEL, -1))
        if channel_pk < 0:
            raise CallError("did not get the channel parameter")

        channel = Channel.objects.get( pk = channel_pk, master = client, status = Channel.STATUS_ALIVE )
        channel.status = Channel.STATUS_DEAD
        channel.save()

        return HttpResponse(json.dumps({'s': client.externid}), content_type = "application/json")
    except (CallError, Channel.DoesNotExist) as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")


@csrf_exempt    # TODO: remove after ALPHA stage, implement proper CSRF protection
@must_have_externid
@must_have_aliveclient
def xhr_channellist(request, **kwargs):
    try:
        return HttpResponse(json.dumps( [{PARAM_CHANNEL: x.pk, PARAM_CHANNELNAME: x.name} for x in Channel.objects.filter(status = Channel.STATUS_ALIVE)]), content_type = "application/json")
    except CallError as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")

@csrf_exempt    # TODO: remove after ALPHA stage, implement proper CSRF protection
@must_have_externid
@must_have_aliveclient
def xhr_channelrelayadd(request, **kwargs):
    try:
        if request.method != "POST":
            raise CallError("must be POST-called")

        client = kwargs['client']
        channel = Channel.objects.get(pk = request.POST.get(PARAM_CHANNEL, -1), status = Channel.STATUS_ALIVE)
        cr = ChannelRelay.objects.get_or_create(channel = channel, client = client)
        cr.status = ChannelRelay.STATUS_ALIVE
        cr.updated = datetime.now()
        cr.save()
    except (Channel.DoesNotExist, CallError) as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")

@csrf_exempt    # TODO: remove after ALPHA stage, implement proper CSRF protection
@must_have_externid
@must_have_aliveclient
def xhr_channelrelaydel(request, **kwargs):
    try:
        if request.method != "POST":
            raise CallError("must be POST-called")

        client = kwargs['client']
        channel = Channel.objects.get(pk = request.POST.get(PARAM_CHANNEL, -1), status = Channel.STATUS_ALIVE)
        cr = ChannelRelay.objects.get_or_create(channel = channel, client = client)
        cr.status = ChannelRelay.STATUS_DEAD
        cr.updated = datetime.now()
        cr.save()
    except (Channel.DoesNotExist, CallError) as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")

@csrf_exempt    # TODO: remove after ALPHA stage, implement proper CSRF protection
@must_have_externid
@must_have_aliveclient
def xhr_channelrelaylist(request, **kwargs):
    try:
        channel = Channel.objects.get(pk = request.GET.get(PARAM_CHANNEL, -1), status = Channel.STATUS_ALIVE)
        return HttpResponse(json.dumps( [{'c': x.client.externid} for x in ChannelRelay.objects.filter(channel = channel, status = ChannelRelay.STATUS_ALIVE)]
                + [{'c': channel.master}]), content_type = "application/json")
    except (Channel.DoesNotExist, CallError) as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")

