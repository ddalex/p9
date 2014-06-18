from django.contrib import admin
from django.contrib.admin.filters import RelatedFieldListFilter
from .models import ClientLog, Client, Feedback

def client_id(obj):
    return obj.client.externid

class AliveClientsRelatedFieldListFilter(RelatedFieldListFilter):
    def __init__(self, field, request, *args, **kwargs):
        field.rel.limit_choices_to = {'status': Client.STATUS_ALIVE }

        super(AliveClientsRelatedFieldListFilter, self).__init__(field, request, *args, **kwargs)

class ClientLogAdmin(admin.ModelAdmin):
    list_display = ('client', 'tag', 'log', 'updated')
    list_filter = ('client', )
    ordering = ('-updated',)
    search_fields = ("client__ip", "client__externid", "log", "tag",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "client":
            kwargs["queryset"] = Client.objects.filter(status = Client.STATUS_ALIVE)
        return super(ClientLogAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(ClientLog, ClientLogAdmin)

class ClientAdmin(admin.ModelAdmin):
    list_display = ("status", "externid", "ip", "updated", "created", "useragent")
    list_filter = ("status", "useragent", "failures", "complets")
    ordering = ("status", "-updated", "-created", )
    search_fields = ("ip", "useragent", "externid", )

admin.site.register(Client, ClientAdmin)

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "useremail", "ip", "created")
    ordering = ("-id",)

admin.site.register(Feedback, FeedbackAdmin)
