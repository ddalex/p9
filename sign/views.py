# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import datetime
import time
import json

from sign.models import Messages

@csrf_exempt
def messages(request):
    if request.method == "POST":
        try:
            msg = Messages.objects.get_or_create(
                    msgtype = request.POST['t'],
                    content = request.POST['d'],
                    created = datetime.datetime.now(),
                    );
        except KeyError:
            pass

    if 'since' in request.GET.keys() and float(request.GET['since']) > 0:
        msg = Messages.objects.filter(created__gte=datetime.datetime.fromtimestamp(float(request.GET['since']))).order_by("created")[:20]
    else:
        msg = Messages.objects.order_by("created")[:20]
    return HttpResponse(json.dumps([{"t" : x.msgtype, "d" : x.content, "c" : int(time.mktime(x.created.timetuple()))} for x in msg]), content_type="application/json")


