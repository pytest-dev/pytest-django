from django.db import models


# Routed to database "main".
class Item(models.Model):
    name = models.CharField(max_length=100)  # type: str


# Routed to database "second".
class SecondItem(models.Model):
    name = models.CharField(max_length=100)  # type: str
