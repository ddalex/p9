from django.db import models

# Create your models here.


class Client(models.Model):
    STATUS_ALIVE = 0
    STATUS_DEAD = 1

    CLIENT_STATUS = (
        (STATUS_ALIVE, "alive"),    
        (STATUS_DEAD,  "dead"),
    )

    externid  = models.CharField(max_length=32, unique = True)
    status  = models.IntegerField(choices = CLIENT_STATUS, default = STATUS_ALIVE)
    updated = models.DateTimeField(null=True)

class Message(models.Model):
    client  = models.ForeignKey(Client)
    recipient = models.ForeignKey(Client, related_name = "recipient", null=True)
    msgtype = models.CharField(max_length=6)
    content = models.CharField(max_length=255)
    created = models.DateTimeField()

   
