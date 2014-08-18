import json
from django.core import serializers
from django.http import HttpResponse
from django.views import generic
from django.views.generic.detail import BaseDetailView
from Vocabulary.models import *

# Create your views here.
class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    Taken from https://docs.djangoproject.com/en/1.6/topics/class-based-views/mixins/
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return HttpResponse(
            self.convert_objects_to_json(),
            content_type='application/json',
            **response_kwargs
        )

    def convert_objects_to_json(self):
        "Convert the relevant object(s) into a JSON object"
        if hasattr(self, 'object'):
            return json.dumps(self.object, cls=Encoder)
        else:
            return serializers.serialize('json', self.object_list)


class WordlistView(generic.ListView):
    template_name = 'wordlist.html'

    def get_queryset(self):
        return Inflection.objects.order_by('form')


class DetailView(JSONResponseMixin, BaseDetailView):
    model = Word
    def render_to_response(self, context, **kwargs):
        return self.render_to_json_response(context, **kwargs)


class LookupView(JSONResponseMixin, generic.ListView):
    def get_queryset(self):
        return Word.objects.filter(form=self.args[0])
    def render_to_response(self, context, **kwargs):
        return self.render_to_json_response(context, **kwargs)


class LookupLemma(JSONResponseMixin, generic.ListView):
    def get_queryset(self):
        return Lemma.objects.filter(form=self.args[0])
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


# Take a JSON data structure and update or create an entry as requested.
def update_word(request):
    pass


