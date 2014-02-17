# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.http import HttpResponse
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
            response = HttpResponse(content_type = "application/json")
            response.status_code=403
            return response

    return wrapper


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
        # update client
        crtclient, created = Client.objects.get_or_create(
                externid=request.GET['s'],
            )
        crtclient.status = request.POST.get('x', 0)
        crtclient.updated = datetime.now()
        crtclient.save()

    # all clients that have not updated in the last 10 seconds are dead
    Client.objects.filter(status=0).filter(updated__lt = datetime.now() - timedelta(seconds = 10)).update(status = 1)

    # list currently alive clients
    clients = Client.objects.filter(status = Client.STATUS_ALIVE).order_by("-updated")
    return HttpResponse(json.dumps([{"s" : x.externid} for x in clients]), content_type='application/json')


@csrf_exempt
@must_have_externid
def messages(request):
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
    try:
        crtclient = Client.objects.filter(externid=request.GET['s'])[0]
        crtclient.updated = datetime.now()
        crtclient.save()
    except IndexError:
        return HttpResponse(json.dumps([]))


    if request.method == "POST":
        try:
            rl = Client.objects.filter(status = Client.STATUS_ALIVE).filter(externid = request.POST.get('r',''))
            if rl.count() != 1:
                raise ValidationError("Recipient MUST be alive") 

            msg = Message.objects.get_or_create(
                    client  = crtclient,
                    recipient = rl[0],
                    msgtype = request.POST['t'],
                    content = request.POST['d'],
                    created = datetime.now(),
                    );
        except Exception as e:
            response = HttpResponse(e, content_type = "application/json")
            response.status_code=403
            return response

    queryset = Message.objects.filter(client__status = Client.STATUS_ALIVE).filter(recipient = crtclient)

    if 'since' in request.GET.keys() and float(request.GET['since']) > 0:
        msg = queryset.filter(id__gt=request.GET['since']).order_by("id")[:20]
    else:
        msg = queryset.order_by("id")[:20]
    return HttpResponse(json.dumps([
        {"s": x.client.externid, "t" : x.msgtype, "d" : x.content,
         "c" : x.id} for x in msg]),
      content_type="application/json")


