from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=100)
