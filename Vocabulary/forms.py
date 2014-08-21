from django import forms


# Make a form class, purely at this point for validation.
class LexiconEntry(forms.Form):
    # All fields required by the time it gets to the server; auto-filling
    # and conditional-required magic should be handled on the client side.
    form = forms.CharField(label='Word form', max_length=50)
    # TODO CLIENT-SIDE Make POS and morphology into pick lists
    pos = forms.CharField(label='Part of speech', max_length=15)
    morphology = forms.CharField(label='Morphology', max_length=25)
    is_lemma = forms.BooleanField(label='This is a lemma form', required=False)
    lemma_id = forms.IntegerField(show_hidden_initial=True, required=False)
    lemma_form = forms.CharField(label='Lemma form', max_length=50)
    lemma_pos = forms.CharField(label='Lemma part of speech', max_length=15)
    lemma_morphology = forms.CharField(label='Lemma morphology', max_length=25)
    translation = forms.CharField(label='Lemma translation', max_length=200)

    # Validation specifics for our part of speech and morphology tags.
    accepted_pos = ['noun', 'verb', 'adj', 'adv', 'conj', 'prep', 'prel', 'numc', 'numo', 'pdem', 'pref', 'po3']
    accepted_morphology = {
        'substantive': [['n', 'a', 'g', 'd', 'l', 'b', 'i', 'v'], ['s', 'p']],
        'verb': [[1, 2, 3], ['s', 'p'], ['p', 'a'], ['i, s'], ['a', 'p']],
        'governs': ['a', 'g', 'd', 'l', 'b', 'i'],
        'verbtype': ['part', 'inf']
    }

    # Part-of-speech validation methods
    def pos_clean(self, field):
        value = self.cleaned_data.get(field + 'pos')
        if value not in self.accepted_pos:
            raise forms.ValidationError("Part-of-speech tag is not recognized")
        return value

    def clean_pos(self):
        return self.pos_clean('')

    def clean_lemma_pos(self):
        return self.pos_clean('lemma_')

    # Morphology validation methods
    def morphology_clean(self, field):
        value = self.cleaned_data.get(field + 'morphology')
        orig_value = value
        thepos = self.cleaned_data.get(field + 'pos')
        is_substantive = True
        # No morphology for uninflected words; different morphology for preposition/verb forms
        if thepos in ['adv', 'conj', 'prep', 'verb']:
            is_substantive = False
        # Optional morphology for numbers
        if not value and thepos in ['numc', 'numo']:
            is_substantive = False
        if thepos == 'prep':
            # Should be +a, +gdb, etc.
            if value[0] != '+':
                raise forms.ValidationError("Preposition morphology tag must begin with +")
            for l in value[1:]:
                if l not in self.accepted_morphology['governs']:
                    raise forms.ValidationError("Preposition morphology tag is not recognized")
        elif thepos == 'verb':
            args = value.split()
            if args[0] in self.accepted_morphology['verbtype']:
                is_substantive = True
                value = args[1]
            else:
                for vform in value.split(';'):
                    idx = 0
                    for l in vform:
                        if l not in self.accepted_morphology['verb'][idx]:
                            raise forms.ValidationError("Verb morphology tag %s is not recognized" % vform)
                        idx += 1
        # Got this far, now check substantives.
        if is_substantive:
            # We might have a +n, +s, z+ etc. on one end.
            for spart in value.split('+'):
                if len(spart) > 1 and spart[0] in ['z', 'y', 'c']:
                    value = spart[1]
                elif len(spart) > 1 and spart[1] in ['n', 's', 'd']:
                    value = spart[0]
            for sform in value.split(';'):
                idx = 0
                for l in sform:
                    if l not in self.accepted_morphology['substantive'][idx]:
                        raise forms.ValidationError("Substantive morphology tag %s is not recognized" % sform)
                    idx += 1
        # Got this far? We're done.
        return orig_value

    def clean_morphology(self):
        return self.morphology_clean('')

    def clean_lemma_morphology(self):
        return self.morphology_clean('lemma_')

    # Method for sanitizing form data for lemma words
    def clean(self):
        # If the inflection is a lemma, then lemma_* is not needed other than translation
        if self.cleaned_data['is_lemma']:
            del self.cleaned_data['lemma_id']
            del self.cleaned_data['lemma_form']
            del self.cleaned_data['lemma_pos']
            del self.cleaned_data['lemma_morphology']
        return self.cleaned_data