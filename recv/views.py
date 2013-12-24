# Create your views here.
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from recv.models import UF
from django.utils import timezone

@require_POST
@csrf_exempt
def uf(request):
    try:
        ufc = request.POST.get('ufc')
        if ufc is None:
            raise Exception("ufc is null")
        ua = request.META.get('HTTP_USER_AGENT')
        if ua is None:
            raise Exception("ua is null")

	rip = request.META.get('REMOTE_ADDR')

        UF.objects.create(content = ufc, useragent = ua, created = timezone.now(), remoteIP = rip )
    
        return HttpResponse('OK', content_type='text/plain')

    except Exception as e:
        return HttpResponse('FAIL '+str(e), content_type='text/plain')
    
#    uf = UF.objects.create()
