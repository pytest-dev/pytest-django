from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=100)


class Unmanaged(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        managed = False
