from django.db import models

# Create your models here.

class Messages(models.Model):
    source  = models.CharField(max_length=32)
    msgtype = models.CharField(max_length=6)
    content = models.CharField(max_length=255)
    created = models.DateTimeField()
