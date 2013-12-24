from django.db import models

# Create your models here.
class UF(models.Model):
	content = models.TextField()
	created = models.DateTimeField()
	remoteIP = models.GenericIPAddressField()
	useragent = models.CharField(max_length=32)
