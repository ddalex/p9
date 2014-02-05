# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.http import HttpResponse
import datetime
import time
import json

from sign.models import Message, Client


def must_have_externid(function):
    def wrapper(request, *args, **kwargs):
        if not 's' in request.GET.keys():
            raise ValidationError("Must specify client Id")
        return function(request, *args, **kwargs)

    return wrapper
    

@csrf_exempt
@must_have_externid
def clients(request):
    if request.method == "POST":
        # update client 
        crtclient, created = Client.objects.get_or_create(
                externid=request.GET['s'],
            )
        crtclient.status = request.POST['x']
        crtclient.updated = datetime.datetime.now()
        crtclient.save()

    # list currently alive clients
    clients = Client.objects.filter(status = Client.STATUS_ALIVE).order_by("-updated")
    return HttpResponse(json.dumps([{"s" : x.externid} for x in clients]))
    

@csrf_exempt
@must_have_externid
def messages(request):
    crtclient = Client.objects.filter(externid=request.GET['s'])[0]

    if request.method == "POST":
        try:
            msg = Message.objects.get_or_create(
                    client  = crtclient,
                    msgtype = request.POST['t'],
                    content = request.POST['d'],
                    created = datetime.datetime.now(),
                    );
        except KeyError:
            pass

    queryset = Message.objects.filter()

    if 'since' in request.GET.keys() and float(request.GET['since']) > 0:
        msg = queryset.filter(created__gte=datetime.datetime.fromtimestamp(float(request.GET['since']))).order_by("created")[:20]
    else:
        msg = queryset.order_by("created")[:20]
    return HttpResponse(json.dumps([
        {"s": x.client.externid, "t" : x.msgtype, "d" : x.content, 
         "c" : int(time.mktime(x.created.timetuple()))} for x in msg]), 
      content_type="application/json")


