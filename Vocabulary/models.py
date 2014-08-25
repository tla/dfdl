import json
from neo4django.db import models
from neo4django.db.models.query import NodeQuerySet
from neo4django.db.models.properties import BoundProperty


# Every word is an inflection.
class Inflection(models.NodeModel):
    form = models.StringProperty()
    pos = models.StringProperty()
    morphology = models.StringProperty()  # Values like 'genitive', 'past participle', etc.
    lemma_form = models.Relationship('Lemma', rel_type='has_inflection', single=True, related_name='inflections')

    def __unicode__(self):
        return self.form

    def update_values(self, formdata, use_lemma=None):
        """Takes the cleaned values from a LexiconEntry form and does the appropriate updates on
         the referenced word and its lemma."""
        # If we have a particular lemma object that goes with this form, keep it.
        thelemma = self.lemma_form
        if use_lemma is not None:
            thelemma = use_lemma
            self.lemma_form = thelemma

        # Now make sure we are operating on the right type of object (Inflection or Lemma).
        if formdata.get('is_lemma', False):  # despite appearances this runs if is_lemma is True!
            if use_lemma is not None:
                raise VocabularyError("Makes no sense to pass use_lemma for a lemma word")
            if isinstance(self, Lemma):
                thelemma = self
            else:
                # Call this again on the same word, as a Lemma instead of an Inflection.
                return thelemma.update_values(formdata)
        del formdata['is_lemma']

        # If we don't have a lemma yet, set it up.
        # At this point we should already have checked that there is really no lemma.
        if thelemma is None:
            thelemma = Lemma.objects.create(form=formdata['lemma_form'], morphology=formdata['lemma_morphology'],
                                            pos=formdata['lemma_pos'], translation=formdata['translation'])
            # Set this as the word's lemma form.
            self.lemma_form = thelemma
        elif thelemma != self:  # The lemma exists and is not the word.
            # See if we are updating the lemma's properties.
            thelemma.pos = formdata['lemma_pos']
            thelemma.morphology = formdata['lemma_morphology']
            thelemma.translation = formdata['translation']
            thelemma.save()

        # Delete the lemma keys
        if thelemma != self:
            for k in ['lemma_form', 'lemma_pos', 'lemma_morphology', 'translation']:
                del formdata[k]
        # Otherwise the lemma_* keys don't exist and the translation key is needed.

        # Finally, make changes to the object itself with the appropriate keys.
        for k in formdata.keys():
            if getattr(self, k) != formdata[k]:
                setattr(self, k, formdata[k])
        self.save()

    @classmethod
    def wordformsearch(cls, formdata):
        """Wrapper around .objects.filter() to find potentially-matching database entries,
        based on LexiconEntry form data, whose values have not all necessarily been defined."""
        found_object = None
        prefix = ''
        if cls == Lemma and not formdata['is_lemma']:
            prefix = 'lemma_'
        for w in cls.objects.filter(form=formdata[prefix+'form']):
            if w.pos is not None and w.pos != formdata[prefix+'pos']:
                continue
            if w.morphology is not None and w.morphology != formdata[prefix+'morphology']:
                continue
            if found_object is not None:
                raise cls.MultipleObjectsReturned()
            found_object = w
        if found_object is None:
            # This is going to be a new word; create it.
            found_object = cls.objects.create(form=formdata['form'])
        return found_object


# But an inflection can also be a lemma. Here is where we record the translations.
# TODO See if an inflection can be upgraded to a lemma.
class Lemma(Inflection):
    translation = models.StringProperty()

    def __init__(self, **kwargs):
        Inflection.__init__(self, **kwargs)
        self.lemma_form = self

    def __unicode__(self):
        return self.form

    # In case the object is cast to an int (e.g. for a Cypher query)
    def __int__(self):
        return self.id


# A custom JSON encoder for our word objects. Somewhat hackish, should see if there
# is a more formal way of getting our named properties.
class Encoder(json.JSONEncoder):
    def default(self, o):
        # Serialize all the fields; recurse, guardedly, on the lemma.
        if isinstance(o, models.NodeModel):
            result = {}
            for f in o._meta.fields:
                datum = getattr(o, f.name, None)
                if f.name == 'lemma_form' and isinstance(datum, Lemma):
                    if datum.id == o.id and isinstance(o, Lemma): # avoid infinite recursion on adding the lemma form
                        pass
                    else:
                        result[f.name] = self.default(datum)
                elif isinstance(f, BoundProperty) or f.name == 'id':
                    result[f.name] = datum
            return result
        elif isinstance(o, NodeQuerySet):
            result = []
            for item in o:
                result.append(self.default(item))
            return result
        else:
            return json.JSONEncoder.default(self, o)


class VocabularyError(Exception):
    def __init__(self, msg):
        self.msg = msg