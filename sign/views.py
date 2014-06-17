# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from datetime import datetime, timedelta
from django.db import IntegrityError
import time
import json

from sign.models import Message, Client, ClientLog
from sign.models import Channel, ChannelRelay, Feedback

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required


# parameter names definition
PARAM_ERROR = 'error'
PARAM_CHANNEL = 'channel'
PARAM_CHANNELNAME = 'name'
PARAM_STATUS = 'x'


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

def must_have_user(function):
    def wrapper(request, *args, **kwargs):
        try:
            if request.user.is_anonymous():
                user = authenticate(username = '__anon', password = 'secret')
                if user is None:
                    user = User.objects.create_user(username = '__anon', password = 'secret')
                    user = authenticate(username = '__anon', password = 'secret')
                user.is_active = False
                user.save()
                login(request, user)
            return function(request, *args, **kwargs)
        except Exception as e:
            import traceback
            response = HttpResponse("error on user:" + str(e) +"\n" + traceback.format_exc(), content_type = "text/plain")
            response.status_code = 500
            return response
    return wrapper

def client_disconnect(clientlist):
    for c in clientlist:
        c.channelrelay_set.update(status = ChannelRelay.STATUS_DEAD)
        c.channel_set.update(status = Channel.STATUS_DEAD)
        map(lambda y: y.delete(), c.message_set.all())
        map(lambda y: y.delete(), c.recipient.all())
        c.status = Client.STATUS_DEAD
        c.save()        
        
    # TODO: delete all channel-related information    

# messaging system
def __get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
@must_have_externid
@login_required
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
                    ip  = __get_client_ip(request),
                    useragent = request.META.get('HTTP_USER_AGENT')
                )

            if not created:
                if crtclient.status == Client.STATUS_ALIVE:
                    raise CallError("Client already registered")

            request.session['smsClientId'] = crtclient.externid
            crtclient.status = request.POST.get('x', 0)
            crtclient.updated = datetime.now()
            crtclient.save()
            if crtclient.status == 1:
                client_disconnect([crtclient])

        # list currently alive clients
        clients = Client.objects.filter(status = Client.STATUS_ALIVE).order_by("-updated")
        return HttpResponse(json.dumps([{"s" : x.externid} for x in clients]), content_type='application/json')
    except CallError as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")


@csrf_exempt
@must_have_externid
@must_have_aliveclient
@login_required
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
@must_have_user
def home(request):
    client_disconnect(Client.objects.filter(status=0).filter(updated__lt = datetime.now() - timedelta(seconds = 10)))
    context = {
        "channels": Channel.objects.filter(status = Channel.STATUS_ALIVE),
        "ua": request.META.get('HTTP_USER_AGENT'),
    }

    return render(request, 'home.html', context)

@must_have_user
def channelview(request, channelid):
    client_disconnect(Client.objects.filter(status=0).filter(updated__lt = datetime.now() - timedelta(seconds = 10)))

    c = Channel.objects.get(pk = channelid)
    if c.status != 0:
        return redirect('home')
    context = {
        "channel" : c,
        "ua": request.META.get('HTTP_USER_AGENT'),
        "smsClientId": request.session['smsClientId'] if 'smsClientId' in request.session else "",
    }
    return render(request, 'channelview.html', context)

@must_have_user
@login_required
def channelcreate(request):
    context = {
        "ua": request.META.get('HTTP_USER_AGENT'),
        "smsClientId": request.session['smsClientId'] if 'smsClientId' in request.session else "",
    }
    return render(request, 'channelcreate.html', context)

# UI interaction

@csrf_exempt    # TODO: remove after ALPHA stage, implement proper CSRF protection
@must_have_externid
@must_have_aliveclient
@login_required
def xhr_channel(request, **kwargs):
    try:
        client_disconnect(Client.objects.filter(status=0).filter(updated__lt = datetime.now() - timedelta(seconds = 10)))

        client = kwargs['client']        
        if request.method == "POST":
            channel_pk = int(request.POST.get(PARAM_CHANNEL, -1))
            channel_name = request.POST.get(PARAM_CHANNELNAME, '')
            channel_desc = request.POST.get('description', '')
            status = int(request.POST.get(PARAM_STATUS, -1))
            if (len(channel_name) > 0 and status == Channel.STATUS_ALIVE):
                # create - allow name reuse if the users match

                try:
                    channel = Channel.objects.get(
                         name = channel_name
                    )
                    if channel.owner and channel.owner.id != request.user.id:
                        raise CallError("You do not own this channel!")

                except Channel.DoesNotExist:
                    channel = Channel.objects.create(
                        master = client,
                        name = channel_name
                    )

                if (channel.status == Channel.STATUS_ALIVE):
                    raise CallError("Channel already exists!")

                channel.master = client
                channel.description = channel_desc
                channel.owner = User.objects.get(username = request.user.username)
                channel.status = Channel.STATUS_ALIVE;
                channel.created = datetime.now()
                channel.save()

            elif (channel_pk > -1 and status == Channel.STATUS_DEAD):
                # delete
                channel = Channel.objects.get( pk = channel_pk, master = client, status = Channel.STATUS_ALIVE )
                channel.status = Channel.STATUS_DEAD
                channel.save()
            else:   
                raise CallError("Unknown action requested") 
        
        return HttpResponse(json.dumps( [{PARAM_CHANNEL: x.pk, PARAM_CHANNELNAME: x.name} for x in Channel.objects.filter(status = Channel.STATUS_ALIVE)]), content_type = "application/json")
    except (IntegrityError, CallError, Channel.DoesNotExist) as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")


@csrf_exempt    # TODO: remove after ALPHA stage, implement proper CSRF protection
@must_have_externid
@must_have_aliveclient
@login_required
def xhr_channelrelay(request, *args, **kwargs):
    try:
        client_disconnect(Client.objects.filter(status=0).filter(updated__lt = datetime.now() - timedelta(seconds = 10)))

        client = kwargs['client']
        channel_pk = kwargs['channel_id']
        channel = Channel.objects.get(pk = channel_pk, status = Channel.STATUS_ALIVE)
        if request.method == "POST":    
            status = int(request.POST.get(PARAM_STATUS, ChannelRelay.STATUS_PROSPECTIVE))
            cr, created = ChannelRelay.objects.get_or_create(channel = channel, client = client)
            # enforce transition PROSPECTIVE -> ALIVE -> DEAD
            cr.status = status
            cr.updated = datetime.now()
            cr.save()

        return HttpResponse(json.dumps( 
                [{ 's': x.client.externid, 'x':x.status }
                      for x in ChannelRelay.objects.filter(channel = channel, 
                        status__in = [ChannelRelay.STATUS_ALIVE, ChannelRelay.STATUS_PROSPECTIVE])]
                 + [{ 's': channel.master.externid, 'x': channel.master.status}]), 
                content_type = "application/json")
    except (IntegrityError, CallError, Channel.DoesNotExist, ChannelRelay.DoesNotExist) as e:
        return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")

@csrf_exempt
@must_have_externid
@must_have_aliveclient
@login_required
def xhr_logpost(request, *args, **kwargs):
    if request.method == "POST":
        try:
            client = kwargs['client']
            tag = request.POST.get("tag", '')
            log = request.POST.get("log", '')

            if len(tag) > 0 or len(log) > 0:
                logobject = ClientLog.objects.create(client = client, tag = tag, log = log)
                logobject.save()

            return HttpResponse(json.dumps({}), content_type = "application/json")

        except Exception as e:
            return HttpResponse(json.dumps({PARAM_ERROR: str(e)}), content_type = "application/json")
    return HttpResponse(json.dumps({PARAM_ERROR: "call not valid"}), content_type = "application/json")

@csrf_exempt
def xhr_feedback(request, *args, **kwargs):
    if request.method == "POST":
        useremail = request.POST.get("e", '')
        usertext  = request.POST.get("t", '')
        ip  = __get_client_ip(request)
        useragent = request.META.get('HTTP_USER_AGENT')
       
        Feedback.objects.create(useremail = useremail, usertext = usertext, ip = ip, useragent = useragent)
        return HttpResponse(json.dumps({}), content_type = "application/json")
    return HttpResponse(json.dumps({PARAM_ERROR: "call not valid"}), content_type = "application/json")


from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_superuser)
def log(request, *args, **kwargs):
    if request.method == "GET":
        t = request.GET.get("t", None)
        if t is not None:
            pass
            return HttpResponse(json.dumps([{"tag": x.tag, "log": x.log, "updated":str(x.updated)} for x in Client.objects.get(externid = t).clientlog_set.order_by('id')]),
                 content_type = "application/json")

        t = request.GET.get("type", None)
        if t is not None:
            return HttpResponse(json.dumps([
                {   "externid": x.externid, 
                    "clientlog_count": x.clientlog_set.count(),
                    "ip" : x.ip,
                    "useragent" : x.useragent,
                    "updated" : str(x.updated),
                } for x in Client.objects.filter(status=0).order_by('id')]), content_type = "application/json")
        return render(request, "clientlog.html", { 'clients': Client.objects.filter(status=0).order_by('id') })
    else:
        return HttpResponse(json.dumps({PARAM_ERROR: "call not valid"}), content_type = "application/json")

@user_passes_test(lambda u: u.is_superuser)
def oview(request, *args, **kwargs):
    if request.GET.get("deadclients", 0):
        clients = Client.objects.all()
    else:
        clients = Client.objects.filter(status = 0)
    context = {
        "deadclients": int(request.GET.get("deadclients", 0)),
        "clients": clients.order_by('id'),
        "channels": Channel.objects.filter(status = Channel.STATUS_ALIVE).select_related(),
    }
    return render(request, "clientoview.html", context)
