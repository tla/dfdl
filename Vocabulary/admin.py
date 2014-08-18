from django.contrib import admin
from Vocabulary.models import Lemma, Inflection

# Register your models here.
admin.site.register(Lemma)
admin.site.register(Inflection)
