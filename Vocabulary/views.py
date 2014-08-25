# No idea why I don't need to import json
import logging
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import ListView, View
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
        """Convert the relevant object(s) into a JSON object."""
        toconvert = getattr(self, 'object', None)
        if toconvert is None:
            toconvert = getattr(self, 'object_list', None)
        return json.dumps(toconvert, cls=Encoder)


class LexiconView(View):
    form_class = LexiconEntry

    # A GET should simply return the wordlist.
    def get(self, request, *args, **kwargs):
        return redirect('/words/list/')

    # A POST should create a new word, or an existing word if it would otherwise
    # be a duplicate.
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            formdata = form.cleaned_data
            error_raised = None
            try:
                found_inflection, found_lemma = self._find_matching_words(formdata)
            except Inflection.MultipleObjectsReturned:
                error_raised = 'inflection'
            except Lemma.MultipleObjectsReturned:
                error_raised = 'lemma'
            if error_raised is not None:
                data = {'error': 'More than one possibly-matching %s found' % error_raised}
                return HttpResponse(json.dumps(data), content_type="application/json", status=400)

            # Now update the word from its form values.
            found_inflection.update_values(formdata, found_lemma)
            return redirect('/words/%d/' % found_inflection.id)
        else:
            data = json.dumps(form.errors)
            return HttpResponse(data, content_type="application/json", status=400)


    def _find_matching_words(self, formdata):
        found_inflection = None
        found_lemma = None

        if formdata['is_lemma']:
            found_inflection = Lemma.wordformsearch(formdata)
        else:
            found_inflection = Inflection.wordformsearch(formdata)
            if found_inflection.lemma_form is None:
                found_lemma = Lemma.wordformsearch(formdata)
        return found_inflection, found_lemma


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
            theword = self.get_object()
            # Look up the appropriate lemma form.
            try:
                posted_lemma = Lemma.wordformsearch(formdata)
            except Lemma.MultipleObjectsReturned:
                data = json.dumps({'error': 'More than one matching lemma found for this word'})
                return HttpResponse(data, content_type='application/json', status=400)
            if posted_lemma != theword.lemma_form:
                theword.update_values(formdata, posted_lemma)
            else:
                theword.update_values(formdata)
            return redirect('/words/%d/' % theword.id)
        else:
            data = json.dumps(form.errors)
            return HttpResponse(data, content_type="application/json", status=400)


class LookupView(JSONResponseMixin, ListView):
    def get_queryset(self):
        return Inflection.objects.filter(form=self.args[0])

    def render_to_response(self, context, **kwargs):
        return self.render_to_json_response(context, **kwargs)
