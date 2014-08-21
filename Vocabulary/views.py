import json
import logging
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import ListView
from django.views.generic.detail import BaseDetailView
from Vocabulary.models import *
from Vocabulary.forms import LexiconEntry

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
        toconvert = getattr(self, 'object', None)
        if toconvert == None:
            toconvert = getattr(self, 'object_list', None)
        return json.dumps(toconvert, cls=Encoder)


class WordlistView(ListView):
    template_name = 'wordlist.html'

    def get_queryset(self):
        return Inflection.objects.order_by('form')

class WordView(JSONResponseMixin, BaseDetailView):
    form_class = LexiconEntry
    model = Inflection
    logger = logging.getLogger(__name__)

    # The 'get' method of DetailView calls render_to_response. Fine.
    def render_to_response(self, context, **kwargs):
        return self.render_to_json_response(context, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        self.logger.debug("Received POST request with the data: %s" % json.dumps(request.POST))
        if form.is_valid():
            formdata = form.cleaned_data
            # Get the object in question, either the lemma or the inflection.
            # TODO When we refactor this, it will be a get_or_create.
            theword = self.get_object()
            thelemma = theword.lemma_form
            if formdata['is_lemma']:
                # TODO Sanity-check that the lemma form matches the inflection form, if it exists.
                theword = thelemma
            # Now set up the lemma if it is not the same as the word.
            elif thelemma is None:
                thelemma, is_new = Lemma.objects.get_or_create(form=formdata['lemma_form'], pos=formdata['lemma_pos'],
                                                               morphology=formdata['lemma_morphology'])
                # See if thelemma.translation exists
                if thelemma.translation is None:
                    thelemma.translation = formdata['translation']
                    thelemma.save()
                # Set this as the word's lemma form.
                theword.lemma_form = thelemma
            else:  # The lemma exists and is not the word.
                if thelemma.translation != formdata['translation']:
                    # Assume we wanted to update the translation.
                    thelemma.translation = formdata['translation']
                    thelemma.save()
            # Finally, make changes to the inflection with the appropriate keys.
            for k in formdata.keys():
                if k.find('lemma') > -1:
                    continue
                if k == 'translation' and theword != thelemma:
                    continue
                if getattr(theword, k) != formdata[k]:
                    setattr(theword, k, formdata[k])
            theword.save()
            return redirect('/words/%d/' % theword.id)
        else:
            data = json.dumps(form.errors)
            return HttpResponse(data, content_type="application/json", status=400)

class LookupView(JSONResponseMixin, ListView):
    def get_queryset(self):
        return Inflection.objects.filter(form=self.args[0])
    def render_to_response(self, context, **kwargs):
        return self.render_to_json_response(context, **kwargs)




