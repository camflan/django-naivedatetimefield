from django.db import models

from naivedatetimefield import NaiveDateTimeField


class NaiveDateTimeTestModel(models.Model):
    aware = models.DateTimeField()
    naive = NaiveDateTimeField()


class NaiveDateTimeAutoNowAddModel(models.Model):
    aware = models.DateTimeField(auto_now_add=True,)
    naive = NaiveDateTimeField(auto_now_add=True,)


class NaiveDateTimeAutoNowModel(models.Model):
    aware = models.DateTimeField(auto_now=True,)
    naive = NaiveDateTimeField(auto_now=True,)
