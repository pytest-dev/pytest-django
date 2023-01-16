from django.db import models


# Routed to database "main".
class Item(models.Model):
    name: str = models.CharField(max_length=100)


# Routed to database "second".
class SecondItem(models.Model):
    name: str = models.CharField(max_length=100)
