# coding=utf-8
from django.core.exceptions import MultipleObjectsReturned
from django.test import SimpleTestCase
from django.test.client import Client
from neo4django.testcases import NodeModelTestCase
from Vocabulary.models import *
from Vocabulary.forms import LexiconEntry
import json
import re


# Create your tests here.
class VocabularyModelTests(NodeModelTestCase):

    gitemk_id = None

    def setUp(self):
        Lemma.objects.create(form=u'արդ', translation='now', pos='conj')
        gitem = Lemma.objects.create(form=u'գիտեմ', translation='to know', pos='verb', morphology='1spia')
        gitemk = Inflection.objects.create(form=u'գիտեմք', morphology='1ppia', pos='verb', lemma_form=gitem)
        self.gitemk_id = gitemk.id

    def test_lookup_id(self):
        byid = Inflection.objects.get(pk=self.gitemk_id)
        self.assertEqual(byid.pos, 'verb')
        self.assertEqual(byid.morphology, '1ppia')
        self.assertEqual(byid.lemma_form.translation, 'to know')

    def test_lookup_string(self):
        byname = Lemma.objects.get(form=u'արդ')
        self.assertEqual(byname.translation, 'now')

    def test_lemma_lookup(self):
        gitem = Lemma.objects.get(form=u'գիտեմ')
        self.assertEqual(gitem.lemma_form, gitem)
        gitemk = Inflection.objects.get(pk=self.gitemk_id)
        self.assertSetEqual(set(gitem.inflections.all()), {Inflection.objects.get(pk=gitem.id), gitemk})
        gitem.translation = 'I know'
        gitem.save()
        self.assertEqual(gitem.translation, gitemk.lemma_form.translation)

    def test_add_existing_lemma(self):
        Lemma.objects.get_or_create(form=u'ու', translation='or', pos='conj')
        current_num = Inflection.objects.count()
        Lemma.objects.get_or_create(form=u'արդ', translation='now', pos='conj')
        self.assertEqual(Inflection.objects.count(), current_num)
        Lemma.objects.get_or_create(form=u'արդ', translation='now')
        self.assertEqual(Inflection.objects.count(), 4)

    def test_add_existing_inflection(self):
        current_num = Inflection.objects.count()
        Inflection.objects.get_or_create(form=u'գիտեմ', pos='verb', morphology='1spia')
        self.assertEqual(Inflection.objects.count(), current_num)

    def test_new_inflection_lemma(self):
        current_num = Inflection.objects.count()
        newlem, isnew = Lemma.objects.get_or_create(form=u'հոգի', pos='noun', morphology='ns;as', translation='soul')
        self.assertTrue(isnew)
        Inflection.objects.get_or_create(form=u'հոգւոյն', pos='noun', morphology='gs;ds;bs+n', lemma_form=newlem)
        self.assertEqual(Inflection.objects.count(), current_num+2)
        nextlem, isnew = Lemma.objects.get_or_create(form=u'գիտեմ')
        self.assertFalse(isnew)
        Inflection.objects.get_or_create(form=u'գիտէ', pos='verb', morphology='3spia', lemma_form=nextlem)
        self.assertEqual(Inflection.objects.count(), current_num+3)

    def test_divergent_lemmas(self):
        # Make the preposition form / lemma, make sure the inflection then exists
        Lemma.objects.create(form=u'առի', pos='prep+lab', translation='up to')
        ari, isnew = Inflection.objects.get_or_create(form=u'առի')
        self.assertIsInstance(ari, Inflection)
        self.assertFalse(isnew)
        # Make the verb form / lemma, check that it is new
        vari, isnew = Inflection.objects.get_or_create(
            form=u'առի', pos='verb', morphology='1saia',
            lemma_form=Lemma.objects.create(form=u'առնում', pos='verb', morphology='1spia',
                                            translation='to receive, take'))
        self.assertIsInstance(vari, Inflection)
        self.assertTrue(isnew)
        with self.assertRaises(MultipleObjectsReturned):
            Inflection.objects.get_or_create(form=u'առի')

    def test_lemma_update(self):
        nlem = Lemma.objects.create(form=u'ասեմ')
        fv = LexiconEntry({
            'form': u'ասեմ',
            'morphology': '1spia',
            'pos': 'verb',
            'is_lemma': True,
            'lemma_form': u'ասեմ',
            'lemma_morphology': '1spia',
            'lemma_pos': 'verb',
            'translation': 'to say'
        })
        self.assertTrue(fv.is_valid())
        ninf = Inflection.objects.get(pk=nlem.id)
        ninf.update_values(fv.cleaned_data)
        self.assertEquals(ninf.lemma_form.translation, 'to say')


class VocabularyAPITests(NodeModelTestCase):

    def setUp(self):
        for word in [u'փոքր',
                     u'ճշմարտի',
                     u'գիտեմք',
                     u'սէր',
                     u'հոգւոյն',
                     u'ի վերայ',
                     u'խորհրդով',
                     u'Աստուծոյ',
                     u'ասելով']:
            Inflection.objects.create(form=word.lower())
        # Add a few pre-existing lemmas
        Lemma.objects.get_or_create(form=u'խորհուրդ', pos='noun', morphology='ns;as', translation='thought, intention')
        Lemma.objects.get_or_create(form=u'ասեմ')
        Lemma.objects.get_or_create(form=u'ճշմարիտ')
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

    def test_add_existing_lemma(self):
        # Test values with a small problem first
        values = {
            'form': u'ասել',
            'morphology': '1spia',
            'pos': 'verb',
            'is_lemma': True,
            'lemma_form': u'ասեմ',
            'lemma_morphology': '1spia',
            'lemma_pos': 'verb',
            'translation': 'to say'
        }
        response = self.client.get(u'/words/lookup/%s/' % values['lemma_form'])
        self.assertEqual(response.status_code, 200)
        thelemma = json.loads(response.content)[0]
        new = self.client.post('/words/%d/' % thelemma['id'], data=values, follow=True)
        self.assertEqual(new.status_code, 400)
        errordata = json.loads(new.content)
        self.assertEquals(len(errordata.keys()), 1)
        self.assertEquals(len(errordata['__all__']), 1)
        rexp = re.compile("Lemma form.*doesn't match main form")
        self.assertRegexpMatches(errordata['__all__'][0], rexp)

        # Fix the data and try again
        values['form'] = u'ասեմ'
        new = self.client.post('/words/%d/' % thelemma['id'], data=values, follow=True)
        self.assertEqual(new.status_code, 200)
        newlemma = json.loads(new.content)
        # This is a bit redundant, but /words/ID/ returns an Inflection and not a Lemma, so we
        # still have to look at the lemma_form to find the translation.
        self.assertEqual(newlemma['lemma_form']['translation'], 'to say')

        # Now test adding an existing lemma to the specified word.
        response = self.client.get(u'/words/lookup/խորհուրդ/')
        self.assertEqual(response.status_code, 200)
        mylemma = json.loads(response.content)[0]
        ivalues = {
            'form': u'խորհրդով',
            'morphology': 'ns;as;vs',
            'pos': 'noun',
            'lemma_form': mylemma['form'],
            'lemma_morphology': mylemma['morphology'],
            'lemma_pos': mylemma['pos'],
            'translation': mylemma['lemma_form']['translation']
        }
        # Get the existing word
        response = self.client.get(u'/words/lookup/%s/' % ivalues['form'])
        self.assertEqual(response.status_code, 200)
        word = json.loads(response.content)[0]
        # ...and the existing lemma
        response = self.client.get(u'/words/lookup/%s/' % ivalues['lemma_form'])
        self.assertEqual(response.status_code, 200)
        itslemma = json.loads(response.content)[0]

        update = self.client.post(u'/words/%d/' % word['id'], ivalues, follow=True)
        self.assertEqual(update.status_code, 200)
        newword = json.loads(update.content)
        self.assertEqual(newword['lemma_form']['id'], itslemma['id'])
        self.assertEqual(newword['pos'], 'noun')

    def test_add_new_words(self):
        # First test the GET behavior
        request = self.client.get('/words/')
        self.assertRedirects(request, '/words/list/')

        # Now create a new lemma form
        values = {
            'form': u'հոգի',
            'morphology': 'ns;as',
            'pos': 'noun',
            'is_lemma': True,
            'lemma_form': u'հոգի',
            'lemma_morphology': 'ns;as',
            'lemma_pos': 'noun',
            'translation': 'spirit, soul'
        }
        request = self.client.post('/words/', values, follow=True)
        self.assertEqual(request.status_code, 200)
        lem = json.loads(request.content)
        self.assertEqual(lem['form'], values['lemma_form'])
        self.assertGreater(lem['id'], 1)

        # Next, create a new inflection with an existing lemma
        values = {
            'form': u'հոգւով',
            'morphology': 'is',
            'pos': 'noun',
            'lemma_form': u'հոգի',
            'lemma_morphology': 'ns;as',
            'lemma_pos': 'noun',
            'translation': 'spirit, soul'
        }
        request = self.client.post('/words/', values, follow=True)
        self.assertEqual(request.status_code, 200)
        word = json.loads(request.content)
        self.assertEqual(word['form'], values['form'])
        self.assertEqual(word['lemma_form']['id'], lem['id'])

        # Next, create new data for an existing but blank inflection and lemma
        exform = u'ճշմարտի'
        exlemf = u'ճշմարիտ'
        request = self.client.get('/words/lookup/%s/' % exform)
        self.assertEqual(request.status_code, 200)
        exword = json.loads(request.content)[0]
        request = self.client.get('/words/lookup/%s/' % exlemf)
        self.assertEqual(request.status_code, 200)
        exlem = json.loads(request.content)[0]
        values = {
            'form': exform,
            'morphology': 'gs;ds;ls',
            'pos': 'adj',
            'lemma_form': exlemf,
            'lemma_morphology': 'ns;as',
            'lemma_pos': 'adj',
            'translation': 'true'
        }
        request = self.client.post('/words/', values, follow=True)
        self.assertEqual(request.status_code, 200)
        word = json.loads(request.content)
        self.assertEqual(word['id'], exword['id'])
        self.assertEqual(word['lemma_form']['id'], exlem['id'])
        self.assertEqual(word['pos'], 'adj')
        self.assertEqual(word['lemma_form']['translation'], 'true')

        # TODO Finally, create an existing inflection with a new lemma


class FormValidationTests(SimpleTestCase):
    # Test our form input validation routines with a bunch of data. Preferably from the
    # Lewond file.
    def test_strings(self):
        f = open('testdata/forms.txt')
        corevalues = {
            'form': 'mots',
            'lemma_form': 'mot',
            'lemma_pos': 'noun',
            'lemma_morphology': 'ns;as',
            'translation': 'word'
        }

        for line in f:
            line.rstrip()
            fields = line.split()
            corevalues['pos'] = fields[0]
            if len(fields) > 1:
                corevalues['morphology'] = ' '.join(fields[1:])
            else:
                try:
                    del corevalues['morphology']
                except KeyError:
                    pass
            form = LexiconEntry(corevalues)
            self.assertTrue(form.is_valid(), 'testing string %s' % line)
        f.close()


# input some text, try identifying the words
# check JSON generation of inflection, lemma

#
