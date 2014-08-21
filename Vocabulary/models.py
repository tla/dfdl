import json
from neo4django.db import models
from neo4django.db.models.query import NodeQuerySet
from neo4django.db.models.properties import BoundProperty


# Every word is an inflection.
class Inflection(models.NodeModel):
    form = models.StringProperty()
    pos = models.StringProperty()
    morphology = models.StringProperty() # Values like 'genitive', 'past participle', etc.
    lemma_form = models.Relationship('Lemma', rel_type='has_inflection', single=True, related_name='inflections')
    def __unicode__(self):
        return self.form


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
                    if datum.id == o.id: # avoid infinite recursion on adding the lemma form
                        result[f.name] = 'SELF'
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