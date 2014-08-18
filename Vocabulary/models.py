import json
from neo4django.db import models
from neo4django.db.models.properties import BoundProperty

# The base model is a word.
class Word(models.NodeModel):
    form = models.StringProperty()


# A word can be a lemma...
class Lemma(Word):
    translation = models.StringProperty()
    pos = models.StringProperty() # Values like 'noun', 'verb', etc.
    # known_forms = models.Relationship(Word, rel_type='inflection_of')
    def __unicode__(self):
        return self.form


# ...or it can be an inflected form that has a lemma.
class Inflection(Word):
    morphology = models.StringProperty() # Values like 'genitive', 'past participle', etc.
    lemma_form = models.Relationship(Lemma, rel_type='has_inflection', single=True, related_name='inflections')
    def __unicode__(self):
        return self.form


# A custom JSON encoder for our word objects. Somewhat hackish, should see if there
# is a more formal way of getting our named properties.
class Encoder(json.JSONEncoder):
    def default(self, o):
        # Serialize all the fields; recurse on all the foreign keys.
        result = {}
        if isinstance(o, models.NodeModel):
            for f in o._meta.fields:
                datum = getattr(o, f.name, None)
                if f.name == 'lemma_form':
                    result[f.name] = self.default(datum)
                elif isinstance(f, BoundProperty) or f.name == 'id':
                    result[f.name] = datum
            return result
        else:
            return json.JSONEncoder.default(self, o)