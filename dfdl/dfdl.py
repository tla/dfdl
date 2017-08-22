from flask import Flask, jsonify, redirect, render_template, request, url_for
from py2neo import Graph
from py2neo.database.status import *
from model import Text, Paragraph, Word
import re

app = Flask(__name__)

db = Graph(password="bedrossian")


@app.route('/')
def start_page():
    saved = Text.select(db)
    return render_template("textselect.html", saved=saved)


@app.route('/loadtext', methods=['POST'])
def load_text():
    text = None
    if 'savedtext' in request.form:
        text = Text.select(db, int(request.form['savedtext'])).first()
    elif 'file' in request.files:
        lines = [l.decode('utf-8') for l in request.files['file'].readlines()]
        paragraphs = []
        pgsplit = request.form['parasplit']
        if pgsplit == 'indent':
            para = []
            for line in lines:
                if re.match(r'^\s+', line):
                    if len(para) > 0:
                        paragraphs.append(' '.join(para))
                    para = [line.rstrip()]
                else:
                    para.append(line.rstrip())
            if len(para) > 0:
                paragraphs.append(' '.join(para))
        elif pgsplit == 'spacesep':
            para = []
            for line in lines:
                if re.match(r'^\s*$', line):
                    if len(para) > 0:
                        paragraphs.append(' '.join(para))
                        para = []
                else:
                    para.append(line.rstrip())
            if len(para) > 0:
                paragraphs.append(' '.join(para))
        else:  # this is "nowrap"
            for line in lines:
                paragraphs.append(line.rstrip())

        # Make the new text node
        text = Text()
        text.title = request.form.get('newtitle', 'A new text')
        thisnode = text
        for p in paragraphs:
            para = Paragraph()
            para.text = p
            thisnode.next_paragraph.add(para)
            thisnode = para
        db.push(text)

    # Now we have our text node, we can load the textview template.
    if text is not None:
        return redirect(url_for('display_text', textid=text.id()))


@app.route('/text/<int:textid>', methods=['GET'])
def display_text(textid):
    text = Text.select(db, textid).first()
    return render_template("textview.html", textblocks=traverse_text(text), textid=textid)


@app.route('/translation/<int:textid>', methods=['POST'])
def save_text_translation(textid):
    """Walk through text paragraphs, getting the new translation value for each
    out of the form."""
    tnode = Text.select(db, textid).first()
    response = {'status': 'ok', 'code': '200'}
    for pgnode in traverse_text(tnode):
        formprop = 'paragraph_%d' % pgnode.id()
        if formprop in request.form:
            try:
                pgnode.translation = request.form[formprop]
                db.push(pgnode)
            except (ClientError, ConstraintError, DatabaseError, GraphError) as e:
                response = {'status': 'error', 'code': 500, 'message': e.message}
        else:
            response = {'status': 'error', 'code': 401,
                        'message': "Paragraph %d has no corresponding form value" % pgnode.id()}
    code = response.pop('code')
    return jsonify(response), code


@app.route('/lookup/<word>')
def lookup(word):
    """Strip the received word of any punctuation except for inline dash, and look it up.
    Return a list of all values found."""
    result = []
    stripped = re.sub(r'\W+', '', word.lower())
    wordobj = Word.select(db, stripped).first()
    if wordobj is not None:
        if wordobj.lemma:
            result.append(lookup_result(wordobj, wordobj))
        for otherlemma in wordobj.has_lemma:
            result.append(lookup_result(wordobj, otherlemma))
    return jsonify(result)


@app.route('/define/<word>', methods=['POST'])
def define(word):
    """Add a new word definition / morphology / etc. to the database."""
    pass


def traverse_text(tnode):
    thisnode = tnode
    pgraphs = []
    while thisnode is not None:
        if len(thisnode.next_paragraph) > 0:
            for np in thisnode.next_paragraph:
                pgraphs.append(np)
                thisnode = np
        else:
            thisnode = None
    return pgraphs


def lookup_result(form, lemma):
    result = {'form': form.form, 'lemma': lemma.form}
    if lemma.morphology is not None:
        result['morphology'] = lemma.morphology
    if lemma.definition is not None:
        result['definition'] = lemma.definition
    return result


if __name__ == '__main__':
    app.run()
