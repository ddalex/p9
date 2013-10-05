# Create your views here.
from django.views.decorators.csrf import csrf_exempt                                          
from django.http import HttpResponse
import datetime
import json

from sign.models import Messages

@csrf_exempt
def messages(request):
    if request.method == "POST":
        ic = Messages.objects.get_or_create(address = request.POST['d']);
    ic = Messages.objects.all()
    return HttpResponse(json.dumps([x.content for x in ic]), content_type="application/json")
