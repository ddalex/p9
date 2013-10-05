from django.db import models

# Create your models here.

class Messages(models.Model):
    content = models.CharField(max_length=255)
