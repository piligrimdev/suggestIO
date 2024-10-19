from django.db import models

# Create your models here.

class Entity(models.Model):
    Name = models.CharField(max_length=10, null=False)

