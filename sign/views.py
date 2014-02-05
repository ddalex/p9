# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.http import HttpResponse
import datetime
import time
import json

from sign.models import Messages

@csrf_exempt
def messages(request):
    if not 's' in request.GET.keys():
        raise ValidationError("Must specify source")
    if request.method == "POST":
        try:
            msg = Messages.objects.get_or_create(
                    source  = request.GET['s'],
                    msgtype = request.POST['t'],
                    content = request.POST['d'],
                    created = datetime.datetime.now(),
                    );
        except KeyError:
            pass

    queryset = Messages.objects.exclude(source = request.GET.get('s'))

    if 'since' in request.GET.keys() and float(request.GET['since']) > 0:
        msg = queryset.filter(created__gte=datetime.datetime.fromtimestamp(float(request.GET['since']))).order_by("created")[:20]
    else:
        msg = queryset.order_by("created")[:20]
    return HttpResponse(json.dumps([{"t" : x.msgtype, "d" : x.content, "c" : int(time.mktime(x.created.timetuple()))} for x in msg]), content_type="application/json")


