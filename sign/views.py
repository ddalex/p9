# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from datetime import datetime, timedelta
import time
import json

from sign.models import Message, Client


def must_have_externid(function):
    def wrapper(request, *args, **kwargs):
        try:
            if not 's' in request.GET.keys():
                raise ValidationError("Must specify client Id")
            return function(request, *args, **kwargs)
        except ValidationError as e:
            response = HttpResponse(json.dumps([]), content_type = "application/json")
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
        except Client.DoesNotExist:
            response = HttpResponse(json.dumps([]), content_type = "application/json")
            response.status_code = 403
            return response

    return wrapper


def client_disconnect(clientlist):
    for c in clientlist:
        c.update(status = 1)


# messaging system

@csrf_exempt
@must_have_externid
def clients(request):
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
    if request.method == "POST":
        client_disconnect(Client.objects.filter(status=0).filter(updated__lt = datetime.now() - timedelta(seconds = 10)))

        # update client
        crtclient, created = Client.objects.get_or_create(
                externid=request.GET['s'],
            )
        crtclient.status = request.POST.get('x', 0)
        crtclient.updated = datetime.now()
        crtclient.save()

    # list currently alive clients
    clients = Client.objects.filter(status = Client.STATUS_ALIVE).order_by("-updated")
    return HttpResponse(json.dumps([{"s" : x.externid} for x in clients]), content_type='application/json')


@must_have_externid
@must_have_aliveclient
@csrf_exempt
def messages(request, **kwargs):
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
            rl = Client.objects.filter(status = Client.STATUS_ALIVE).filter(externid = request.POST.get('r',''))
            if rl.count() != 1:
                raise ValidationError("Recipient MUST be alive") 

            msg = Message.objects.get_or_create(
                    client  = client,
                    recipient = rl[0],
                    msgtype = request.POST['t'],
                    content = request.POST['d'],
                    created = datetime.now(),
                    );
        except Exception as e:
            response = HttpResponse(e, content_type = "application/json")
            response.status_code=403
            return response

    queryset = Message.objects.filter(client__status = Client.STATUS_ALIVE).filter(recipient = client)

    if 'since' in request.GET.keys() and float(request.GET['since']) > 0:
        msg = queryset.filter(id__gt=request.GET['since']).order_by("id")[:20]
    else:
        msg = queryset.order_by("id")[:20]
    return HttpResponse(json.dumps([
        {"s": x.client.externid, "t" : x.msgtype, "d" : x.content,
         "c" : x.id} for x in msg]),
      content_type="application/json")



# UI rendering

def home(request):
    return render(request, 'home.html')

# TODO: display a page viewing and relaying the channel created
def channelview(request, channelid):
    return render(request, 'channelview.html')

# TODO: on GET, display the page to create a channel
def channelcreate(request):   
    return render(request, 'channelcreate.html')

# TODO: register a client that relays a channel 
# or return list of clients relaying channels
def channelrelay(request, channelid):
    return HttpResponse( json.dumps([]),
      content_type="application/json")

# UI interaction
# TODO: create channel entry on POST
@must_have_externid
@must_have_aliveclient
def channel_xhrcreate(request, **kwargs):
    client = kwargs['client']
     


