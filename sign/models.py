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
    updated = models.DateTimeField(null=True)

class Message(models.Model):
    client  = models.ForeignKey(Client)
    recipient = models.ForeignKey(Client, related_name = "recipient")
    msgtype = models.CharField(max_length=16)
    content = models.CharField(max_length=4096)
    created = models.DateTimeField()

class Channel(models.Model):
    name = models.CharField(max_length=64, unique = True)
    master = models.ForeignKey(Client)

class ChannelRelays(models.Model):
    channel = models.ForeignKey(Channel)
    client = models.ForeignKey(Client)       
