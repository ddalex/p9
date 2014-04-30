from django.db import models

# Create your models here.

class Client(models.Model):
    STATUS_ALIVE = 0
    STATUS_DEAD = 1

    CLIENT_STATUS = (
        (STATUS_ALIVE, "alive"),    
        (STATUS_DEAD,  "dead"),
    )

    externid  = models.CharField(max_length=64, unique = True)
    status  = models.IntegerField(choices = CLIENT_STATUS, default = STATUS_ALIVE)
    ip      = models.GenericIPAddressField(blank = True)
    useragent = models.CharField(max_length=256, blank = True)
    created = models.DateTimeField(auto_now_add = True) 
    updated = models.DateTimeField(null=True)

    def __unicode__(self):
        return "Client " + self.externid + " " + self.ip

class Message(models.Model):
    client  = models.ForeignKey(Client)
    recipient = models.ForeignKey(Client, related_name = "recipient")
    msgtype = models.CharField(max_length=16)
    content = models.CharField(max_length=4096)
    created = models.DateTimeField()

class Channel(models.Model):
    STATUS_ALIVE = 0
    STATUS_DEAD = 1

    CHANNEL_STATUS = (
        (STATUS_ALIVE, "alive"),    
        (STATUS_DEAD,  "dead"),
    )
    name    = models.CharField(max_length=64, unique = True)
    master  = models.ForeignKey(Client)
    created = models.DateTimeField(null=True)
    status  = models.IntegerField(choices = CHANNEL_STATUS, default = STATUS_ALIVE)

class ChannelRelay(models.Model):
    STATUS_ALIVE = 0
    STATUS_DEAD = 1
    STATUS_PROSPECTIVE = 2

    RELAY_STATUS = (
        (STATUS_PROSPECTIVE, "prospective"),
        (STATUS_ALIVE, "alive"),    
        (STATUS_DEAD,  "dead"),
    )
    channel = models.ForeignKey(Channel)
    client = models.ForeignKey(Client)
    updated = models.DateTimeField(null=True)
    status = models.IntegerField(choices = RELAY_STATUS, default = STATUS_PROSPECTIVE)

class ClientLog(models.Model):
    client  = models.ForeignKey(Client)
    tag     = models.CharField(max_length=32)
    log     = models.TextField()
    updated = models.DateTimeField(auto_now_add=True)
