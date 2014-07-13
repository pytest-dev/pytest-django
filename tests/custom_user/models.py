from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class MyCustomUserManager(BaseUserManager):
    def _create_user(self, username, email, password, is_staff, is_superuser,
                     **extra_fields):
        email = self.normalize_email(email)
        user = self.model(identifier=username, email=email, is_staff=is_staff,
                          is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, False, False,
        **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True, True,
                                 **extra_fields)


class MyCustomUser(AbstractBaseUser):
    identifier = models.CharField(unique=True, max_length=100)
    email = models.EmailField(blank=True)
    is_staff = models.BooleanField()
    is_superuser = models.BooleanField()

    USERNAME_FIELD = 'identifier'

    objects = MyCustomUserManager()
