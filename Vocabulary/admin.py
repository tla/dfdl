from django.contrib import admin
from Vocabulary.models import Lemma, Word

# Register your models here.
class WordAdmin(admin.ModelAdmin):
    list_display = ('word', 'pos', 'lemma')
    search_fields = ['word']


admin.site.register(Word, WordAdmin)
admin.site.register(Lemma)