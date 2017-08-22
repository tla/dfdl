from py2neo.ogm import GraphObject, Property, RelatedTo, Label
import re


class Text(GraphObject):
    title = Property()
    next_paragraph = RelatedTo("Paragraph")

    def id(self):
        return self.__primaryvalue__


class Paragraph(GraphObject):
    next_paragraph = RelatedTo("Paragraph")
    text = Property()
    translation = Property()

    def id(self):
        return self.__primaryvalue__

    def words(self):
        return re.split(r'\s+', str(self.text))


class Word(GraphObject):
    __primarykey__ = "form"
    form = Property()
    morphology = Property()
    definition = Property()
    has_lemma = RelatedTo("Word")
    lemma = Label("Lemma")

