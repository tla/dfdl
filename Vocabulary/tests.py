# coding=utf-8
from django.core.exceptions import MultipleObjectsReturned
from django.test import TestCase
from django.test.client import Client
from neo4django.testcases import NodeModelTestCase
from Vocabulary.models import *
import json


# Create your tests here.
class VocabularyModelTests(NodeModelTestCase):

    gitemk_id = None

    def make_data(self):
        Lemma.objects.create(form=u'արդ', translation='now', pos='conj')
        gitem = Lemma.objects.create(form=u'գիտեմ', translation='to know', pos='verb', morphology='1spia')
        gitemk = Inflection.objects.create(form=u'գիտեմք', morphology='1ppia', pos='verb', lemma_form=gitem)
        self.gitemk_id = gitemk.id

    def test_lookup_id(self):
        self.make_data()
        byid = Inflection.objects.get(pk=self.gitemk_id)
        self.assertEqual(byid.pos, 'verb')
        self.assertEqual(byid.morphology, '1ppia')
        self.assertEqual(byid.lemma_form.translation, 'to know')

    def test_lookup_string(self):
        self.make_data()
        byname = Lemma.objects.get(form=u'արդ')
        self.assertEqual(byname.translation, 'now')

    def test_lemma_lookup(self):
        self.make_data()
        gitem = Lemma.objects.get(form=u'գիտեմ')
        self.assertEqual(gitem.lemma_form, gitem)
        gitemk = Inflection.objects.get(pk=self.gitemk_id)
        self.assertSetEqual(set(gitem.inflections.all()), {Inflection.objects.get(pk=gitem.id), gitemk})
        gitem.translation = 'I know'
        gitem.save()
        self.assertEqual(gitem.translation, gitemk.lemma_form.translation)

    def test_add_existing_lemma(self):
        self.make_data()
        newor = Lemma.objects.get_or_create(form=u'ու', translation='or', pos='conj')
        current_num = Inflection.objects.count()
        neward = Lemma.objects.get_or_create(form=u'արդ', translation='now', pos='conj')
        self.assertEqual(Inflection.objects.count(), current_num)
        nextard = Lemma.objects.get_or_create(form=u'արդ', translation='now')
        self.assertEqual(Inflection.objects.count(), 4)

    def test_add_existing_inflection(self):
        self.make_data()
        current_num = Inflection.objects.count()
        newgitem = Inflection.objects.get_or_create(form=u'գիտեմ', pos='verb', morphology='1spia')
        self.assertEqual(Inflection.objects.count(), current_num)

    def test_new_inflection_lemma(self):
        self.make_data()
        current_num = Inflection.objects.count()
        newlem, isnew = Lemma.objects.get_or_create(form=u'հոգի', pos='noun', morphology='ns;as', translation='soul')
        self.assertTrue(isnew)
        Inflection.objects.get_or_create(form=u'հոգւոյն', pos='noun', morphology='gs;ds;bs+n', lemma_form=newlem)
        self.assertEqual(Inflection.objects.count(), current_num+2)
        nextlem, isnew = Lemma.objects.get_or_create(form=u'գիտեմ')
        self.assertFalse(isnew)
        nextword = Inflection.objects.get_or_create(form=u'գիտէ', pos='verb', morphology='3spia', lemma_form=nextlem)
        self.assertEqual(Inflection.objects.count(), current_num+3)

    def test_divergent_lemmas(self):
        self.make_data()
        # Make the preposition form / lemma, make sure the inflection then exists
        Lemma.objects.create(form=u'առի', pos='prep+lab', translation='up to')
        ari, isnew = Inflection.objects.get_or_create(form=u'առի')
        self.assertIsInstance(ari, Inflection)
        self.assertFalse(isnew)
        # Make the verb form / lemma, check that it is new
        vari, isnew = Inflection.objects.get_or_create(form=u'առի', pos='verb', morphology='1saia',
                                         lemma_form=Lemma.objects.create(form=u'առնում', pos='verb', morphology='1spia',
                                                                         translation='to receive, take'))
        self.assertIsInstance(vari, Inflection)
        self.assertTrue(isnew)
        with self.assertRaises(MultipleObjectsReturned):
            result, isnew = Inflection.objects.get_or_create(form=u'առի')


class VocabularyAPITests(TestCase):
    thetext = [u'Եւ',
               u'արդ',
               u'ծառայից',
               u'փոքր',
               u'ի',
               u'շատէ',
               u'արդարեւ',
               u'ճշմարիտ',
               u'սիրելւոյդ',
               u'Յիսուսի',
               u'եւ',
               u'բարեկամիդ',
               u'իմ',
               u'գիտեմք',
               u'զի',
               u'սէր',
               u'հոգւոյն',
               u'ստիպէ',
               u'զքեզ',
               u'յաղագս',
               u'եկելոցս',
               u'ի վերայ',
               u'իմ',
               u'ի',
               u'տարակուսանս',
               u'եղեալ',
               u'յանզրաւական',
               u'եւ',
               u'յանսպառ',
               u'պատժապարտութեան',
               u'անպարտական',
               u'գոլով',
               u'եւ',
               u'ի',
               u'բոլորեցունց',
               u'պարառեալ',
               u'անպայման',
               u'եւ',
               u'պղտորեալ',
               u'խորհրդով',
               u'եւ',
               u'խարդաւանս',
               u'ի վերայ',
               u'իմ',
               u'խոկալով',
               u'խազմ',
               u'յարուցեալ',
               u'խիզախողաց',
               u'յոմանց',
               u'եկելոց',
               u'եւ',
               u'յոմանց',
               u'յարուցելով',
               u'կեամք,',
               u'ակն',
               u'ունելով',
               u'Աստուծոյ',
               u'ասելով']

    def setUp(self):
        for word in self.thetext:
            try:
                Inflection.objects.get_or_create(form=word.lower())
            except Inflection.MultipleObjectsReturned:
                pass
        self.client = Client()

    def test_list(self):
        response = self.client.get('/words/list/')
        self.assertEqual(response.status_code, 200)
        # TODO check the contents, make a JSON return

    def test_fetch(self):
        myform = u'փոքր'
        response = self.client.get(u'/words/lookup/%s/' % myform)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['form'], myform)
        # Now see that we get a 200 and empty list for a form that doesn't yet exist.
        myotherform = u'ոնոմատոպոեիա'
        response = self.client.get(u'/words/lookup/%s' % myotherform, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(json.loads(response.content), [])

    def test_add_forminfo(self):
        myform = u'աստուծոյ'
        response = self.client.get(u'/words/lookup/%s' % myform, follow=True)
        # Check that we got a response
        self.assertEqual(response.status_code, 200)
        word = json.loads(response.content)[0]
        # Check that we got a sane response
        self.assertEqual(word['form'], myform)
        self.assertIsNone(word['morphology'])
        # Set some values for what this word should contain
        values = {
            'pos': 'noun',
            'translation': 'God',
            'lemma_morphology': 'ns;as',
            'lemma_pos': 'noun',
            'lemma_form': u'աստուած'
        }
        # We haven't got a complete set of values; this should fail.
        update = self.client.post(u'/words/%d/' % word['id'], data=values)
        self.assertEqual(update.status_code, 400)
        # Fill in the missing values
        values['morphology'] = 'gs;ds;ls'
        values['form'] = u'աստուծոյ'
        update = self.client.post(u'/words/%d/' % word['id'], data=values, follow=True)
        self.assertEqual(update.status_code, 200)
        newword = json.loads(update.content)
        self.assertEqual(newword['pos'], 'noun')
        self.assertEqual(newword['lemma_form']['morphology'], 'ns;as')
        self.assertEqual(newword['lemma_form']['pos'], 'noun')
        self.assertIsNotNone(newword['lemma_form'].get('id'))


class FormValidationTests(TestCase):
    # Test our form input validation routines with a bunch of data. Preferably from the
    # Lewond file.
    pass


# input some text, try identifying the words
# check JSON generation of inflection, lemma

#
