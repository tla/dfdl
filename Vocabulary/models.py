import json
from django.db import models

# Create your models here.
class Lemma(models.Model):
    entry = models.CharField(max_length=30)
    translation = models.CharField(max_length=300)
    def __str__(self):
        return self.entry


class Word(models.Model):
    word = models.CharField(max_length=30)
    pos = models.CharField(max_length=50)
    lemma = models.ForeignKey(Lemma)
    def __str__(self):
        return self.word


class Encoder(json.JSONEncoder):
    def default(self, o):
        # Serialize all the fields; recurse on all the foreign keys.
        result = {}
        if isinstance(o, models.Model):
            for f in o._meta.fields:
                result[f.name] = getattr(o, f.name)
            return result
        else:
            return json.JSONEncoder.default(self, o)
