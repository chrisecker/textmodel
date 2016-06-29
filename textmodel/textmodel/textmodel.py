# -*- coding: latin-1 -*-


from .texeltree import Text, Group, NewLine, Tabulator, insert, takeout, \
    ENDMARK, is_homogeneous, provides_childs, grouped, length, iter_childs, depth, \
    is_list_efficient, is_root_efficient, strip2list
from .styles import updated_style, create_style, get_styles, set_styles, \
    get_style, set_properties, get_parstyles, set_parstyles, set_parproperties, \
    StyleIterator
from .weights import find_weight, get_weight, NotFound
from .modelbase import Model
import re



debug = 0



def _get_text(texel, i1, i2):
    r = []
    if provides_childs(texel):
        for j1, j2, child in iter_childs(texel):
            if i1 < j2 and j1 < i2: # intersection
                r.append(_get_text(child, i1-j1, i2-j1))
        return u''.join(r)
    text = texel.text
    return text[max(0, i1):min(i2, len(text))]


def dump_range(texel, i1, i2, i0=0, indent=0):
    s = texel.__class__.__name__
    if texel.is_text:
        s += " "+repr(texel.text)
    print " "*indent+"%i:%i %s" % (i0, i0+length(texel), s)
    if provides_childs(texel):
        skip = False
        for j1, j2, child in iter_childs(texel):
            if i1 < j2 and j1 < i2: # intersection
                dump_range(child, i1-j1, i2-j1, i0+j1, indent+4)
                skip = False
            elif not skip:
                print " "*indent+'...'
                skip = True # skip output of more '...'


_split = re.compile(r"([\t\n])", re.MULTILINE).split
class TextModel(Model):
    """A data type for storing and manipulating styled text. Changes to
    the data are notified to views by emitting the following signals:
    - "inserted" (arguments: i, length)
    - "removed" (arguments: i, removed data)
    - "properties changed" (arguments: i1, i2)

    """
    defaultstyle = create_style()

    def create_textmodel(self, text=u'', **properties):
        """Creates a new textmodel with text $text$ and uniform style."""
        return self.__class__(text, **properties)

    def __init__(self, text=u'', **properties):
        style = updated_style(self.defaultstyle, properties)
        self.ENDMARK = ENDMARK.set_style(style)
        l = []
        text = text.replace('\r', '')
        for part in _split(text):
            if part == '\n':
                l.append(NewLine(style))
            elif part == '\t':
                l.append(Tabulator(style))
            elif len(part):
                l.append(Text(part, style))
        self.texel = grouped(l)

    def __len__(self):
        return length(self.texel)

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__ = state

    def get_xtexel(self):
        """Returns the texel tree extended by an ENDMARK glyph."""
        texel = self.texel
        return Group([texel, self.ENDMARK])

    def nlines(self):
        """Returns the number of lines."""
        return self.texel.weights[2]+1

    def get_text(self, i1=None, i2=None):
        """Retuns the text between *i1* and *i2* as unicode string."""
        if i1 is None:
            i1 = 0
        if i2 is None:
            i2 = length(self.texel)
        if i1<0:
            raise IndexError, i1
        if i2>len(self):
            raise IndexError, i2
        return _get_text(self.texel, i1, i2)

    def get_style(self, i):
        """Returns the style at index *i*."""
        return get_style(self.texel, i)

    def position2index(self, row, col):
        """Returns the index corresponding to *row* and *col*."""
        i = find_weight(self.texel, row, 2)
        if i is None:
            raise IndexError(row)
        return i+col

    def _lfromt(self, t):
        # for debugging
        splitter = t.split('\n')
        l = [len(s)+1 for s in splitter[:-1]]
        return l

    def index2position(self, i):
        """Returns the (row, col)-tuple corresponding to index *i*."""
        texel = self.texel
        if i > length(texel):
            raise IndexError(i)
        if i < 0:
            raise IndexError(i)

        row = get_weight(texel, 2, i)
        assert type(row) is int
        j = find_weight(texel, row, 2)
        col = i-j
        return row, col

    def linestart(self, row):
        """Returns the index where line number *row* starts."""
        try:
            return find_weight(self.texel, row, 2)
        except NotFound:
            raise IndexError(row)

    def lineend(self, row):
        """Returns the index where line number *row* ends. The NewLine-marker
           ist not included.  

           >>> TextModel("").lineend(0) 
           0 

           >>> TextModel("x").lineend(0)
           1
        """
        try:
            return find_weight(self.get_xtexel(), row+1, 2)-1
        except NotFound:
            raise IndexError(row)

    def linelength(self, row):
        """Returns the length of line *row*."""
        try:
            i1 = find_weight(self.texel, row, 2)
        except NotFound:
            raise IndexError(row)
        try:
            i2 = find_weight(self.texel, row+1, 2)
        except NotFound:
            i2 = len(self)
        return i2-i1

    def set_properties(self, i1, i2, **properties):
        """Sets the text properties between *i1* and *i2*."""
        memo = get_styles(self.texel, i1, i2)
        self.texel = grouped(
            set_properties(self.texel, i1, i2, properties))
        #assert check(self.texel)
        self.notify_views('properties_changed', i1, i2)
        return memo

    def set_styles(self, i, styles):
        """Sets the styling of a span of text. Usually used by undo."""
        n = sum([entry[0] for entry in styles])
        memo = get_styles(self.texel, i, i+n)
        iterator = StyleIterator(iter(styles))
        self.texel = grouped(
            set_styles(self.texel, i, iterator))
        self.notify_views('properties_changed', i, i+n)
        return memo

    def set_parproperties(self, i1, i2, **properties):
        """Sets the paragraph properties between *i1* and *i2*."""
        memo = get_parstyles(self.texel, i1, i2)
        self.texel = grouped(
            set_parproperties(self.texel, i1, i2, properties))
        #assert check(self.texel)
        self.notify_views('properties_changed', i1, i2)
        return memo

    def set_parstyles(self, i, styles):
        """Sets the paragraph style of a span of text. Usually used by undo."""
        n = sum([entry[0] for entry in styles])
        memo = get_styles(self.texel, i, i+n)
        iterator = StyleIterator(iter(styles))
        self.texel = grouped(
            set_parstyles(self.texel, i, iterator))
        self.notify_views('properties_changed', i, i+n)
        return memo

    def insert(self, i, text):
        """Inserts *text* at position *i*."""
        row, col = self.index2position(i)
        n = length(self.texel) + length(text.texel)
        stuff = strip2list(text.texel)
        tmp = grouped(insert(self.texel, i, stuff))
        self.texel = tmp
        assert length(self.texel) == n
        self.notify_views('inserted', i, len(text))

    def append(self, text):
        """Appends textmodel *texel*."""
        return self.insert(len(self), text)

    def append_text(self, text, **properties):
        """Appends unicode text."""
        return self.insert_text(len(self), text, **properties)

    def insert_text(self, i, text, **properties):
        """Inserts a unicode text string *text* at index *i*.""" 
        textmodel = self.create_textmodel(text, **properties)
        self.insert(i, textmodel)

    def copy(self, i1, i2):
        """Returns a copy of all data between *i1* and *i2*."""
        row1, col1 = self.index2position(i1)
        row2, col2 = self.index2position(i2)

        rest, removed = takeout(self.texel, i1, i2)
        model = self.create_textmodel()
        model.texel = grouped(removed)
        return model

    def __add__(self, other):
        model = self.create_textmodel()
        model.texel = self.texel
        model.insert(len(self), other)
        return model

    def __getitem__(self, slice):
        if slice.start is None:
            i1 = 0
        else:
            i1 = slice.start
            if i1 < 0:
                i1 = len(self)+i1
                if i1 < 0:
                    raise IndexError(slice.start)

        if slice.stop is None:
            i2 = len(self)
        else:
            i2 = slice.stop
            if i2 < 0:
                i2 = len(self)+i2
                if i2 < 0:
                    raise IndexError(slice.stop)
        return self.copy(i1, i2)

    def remove(self, i1, i2):
        """Removes everything between *i1* and *i2*."""
        row1, col1 = self.index2position(i1)
        row2, col2 = self.index2position(i2)

        rest, kern = takeout(self.texel, i1, i2)
        self.texel = grouped(rest)

        model = self.create_textmodel()
        model.texel = grouped(kern)

        self.notify_views('removed', i1, model)
        #assert check(self.texel)
        return model



def pycolorize(rawtext, coding='latin-1'):
    # used for benchmarking
    import cStringIO
    rawtext+='\n'
    instream = cStringIO.StringIO(rawtext).readline

    import token, tokenize, keyword
    _KEYWORD = token.NT_OFFSET + 1
    _TEXT    = token.NT_OFFSET + 2

    _colors = {
        token.NUMBER:       '#0080C0',
        token.OP:           '#0000C0',
        token.STRING:       '#004080',
        tokenize.COMMENT:   '#008000',
        token.NAME:         '#000000',
        token.ERRORTOKEN:   '#FF8080',
        _KEYWORD:           '#C00000',
        #_TEXT:              '#000000',
    }
    def tokeneater(toktype, toktext, (srow,scol), (erow,ecol), line):
        i1 = model.position2index(srow-1, scol)
        i2 = model.position2index(erow-1, ecol)
        if token.LPAR <= toktype and toktype <= token.OP:
            toktype = token.OP
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            toktype = _KEYWORD
        try:
            color = _colors[toktype]
        except:
            return
        model.set_properties(i1, i2, textcolor=color)

    text = rawtext.decode(coding)
    model = TextModel(text)

    tokenize.tokenize(instream, tokeneater)
    return model.copy(0, len(model)-1)



if debug: # enable contract checking
     import contract
     contract.checkmod(__name__)


text1 = "0123456789"
text2 = "abcdefghijklmnopqrstuvwxyz"
text3 = "01\n345\n\n89012\n45678\n"


def test_00():
    "remove w. simplify"
    t2 = TextModel(text2)

    for i in range(len(text1)):
        t = TextModel(text1)
        t.remove(i, i+1)
        if not isinstance(t.texel, Text):
            t.texel.dump()
        assert isinstance(t.texel, Text)

    for i in range(len(text1)):
        t = TextModel(text1)
        t.texel = Group([t.texel])
        t.remove(i, i+1)
        assert isinstance(t.texel, Text)

    # Groups of onyl one element should be opened
    for i in range(len(text1)):
        t = TextModel(text1)
        t.texel = Group([t.texel])
        t.remove(i, i+1)
        assert isinstance(t.texel, Text)

    # Text with different styling should not be merged
    for i in range(2*len(text1)):
        t = TextModel(text1)
        t1 = TextModel(text1, fontsize=20)
        t.insert(len(t), t1)
        t.remove(i, i+1)
        assert isinstance(t.texel, Group)
        assert len(t.texel.childs) == 2
        assert isinstance(t.texel.childs[0], Text)
        assert isinstance(t.texel.childs[1], Text)
        text = '01234567890123456789'
        text = text[:i]+text[i+1:]
        assert t.get_text() == text



def test_01():
    "row, col"

    def index2position(t, i):
        row = t[:i].count('\n')
        i0 = 0
        for j in range(row):
            i0 = t.index('\n', i0)+1
        col = i-i0
        return row, col

    texts = [text3]
    text = '0123456789'
    import random
    while text.count('\n')<len(text):
        i = random.randrange(len(text))
        if text[i] == '\n':
            continue
        text = text[:i]+'\n'+text[i+1:]
        texts.append(text)

    for text in texts:
        t = TextModel(text)
        ll_text = t._lfromt(text)


        for i in range(len(text)):
            row, col = t.index2position(i)
            assert (row, col) == index2position(text, i)

        for i in range(len(text)):
            row, col = index2position(text, i)
            i_ = t.position2index(row, col)
            assert i == i_



def test_03():
    "TextModel"
    t1 = TextModel(text1)
    assert t1.get_text() == text1
    t2 = TextModel(text2)
    assert t2.get_text() == text2
    t3 = TextModel(text1+'\n'+text2)
    assert t3.get_text() == text1+'\n'+text2
    assert t3.nlines() == 2
    assert t3.position2index(0, 5) == 5
    assert t3.position2index(1, 0) == 11
    assert t3.get_text()[10] == '\n'
    assert t3.get_text()[11] == 'a'
    assert t3.linelength(0) == len(text1)+1 # the newline counts!
    assert t3.linelength(1) == len(text2)

    t1.insert(0, t2)
    assert  t1.get_text() == text2+text1
    t1.remove(0, len(text2))
    assert t1.get_text() == text1

    t1.insert(3, t3)
    tmp = text1[:3]+text1+'\n'+text2+text1[3:]
    assert t1.get_text() == tmp
    n = len(t1)
    old = t1.remove(3, 3+len(t3))
    assert len(old) + len(t1) == n
    assert t1.get_text() == text1


def test_04():
    "indices"
    t = TextModel(text1+'\n'+text2)
    row = col = 0

    for i in range(len(t)):

        assert t.index2position(i) == (row, col)
        if t.get_text(i, i+1) == '\n':
            row += 1
            col = 0
        else:
            col += 1


def test_05():
    "style"
    class TestModel(TextModel):
        defaultstyle = create_style(textcolor='black', fontsize=10)

    t1 = TestModel(text1)
    assert t1.get_text() == text1
    t2 = TestModel(text2)
    assert t2.get_text() == text2
    t3 = TestModel(text1+'\n'+text2)

    # Styles are compared by their id. Same styles always have the
    # same id. This is assured by the factory function "new_style()"
    assert t3.get_style(0) == TestModel.defaultstyle
    assert t3.get_style(0) is TestModel.defaultstyle

    t3.set_properties(5, 10, textcolor='red')
    t3.set_properties(3, 8, fontsize=8)

    for i in range(len(t3)):
        style = t3.get_style(i)
        if i<5:
            assert style.get('textcolor') == 'black'
        elif i<10:
            assert style['textcolor'] == 'red'
        else:
            assert style['textcolor'] == 'black'

        if i<3:
            assert style['fontsize'] == 10
        elif i<8:
            assert style['fontsize'] == 8
        else:
            assert style['fontsize'] == 10

    #assert len(style_pool) == 4 # depends on gc

    t3.set_properties(0, len(t3), **TestModel.defaultstyle)
    for i in range(len(t3)):
        style = t3.get_style(i)
        assert style == TestModel.defaultstyle
        assert id(style) == id(TestModel.defaultstyle)

    t3.set_properties(0, len(t3), fontsize = 6)
    s0 = t3.get_style(0)
    for i in range(len(t3)):
        style = t3.get_style(i)
        assert id(style) == id(s0)
    assert s0['fontsize'] == 6


def test_06():
    "get_style"
    t = TextModel(text1)
    assert t.get_text() == text1

    t.set_properties(3, 5, fontsize=8)
    s = t.get_style(4)
    n = len(t)
    t.insert(4, TextModel('x', **s))
    assert len(t) == n+1
    assert t.get_style(3) is s
    assert t.get_style(4) is s
    assert t.get_style(5) is s


def test_08():
    "insert/remove"
    text = text1+'\n'+text2
    for i in range(len(text)):
        t = TextModel(text)
        n = len(t)
        x = TextModel('x')
        t.insert(i, x)
        assert len(t) == n+1
        t.remove(i, i+1)
        assert len(t) == n


def test_09():
    "slice"
    text = "Text A"
    model = TextModel(text)

    assert model.get_text() == text
    assert model[5:6].get_text() == text[5:6]
    assert model[-1:].get_text() == text[-1:]
    for i in range(len(text)):
        for n in range(1, len(text)-i):
            j = i+n
            assert model[i:j].get_text() == text[i:j]
            assert model[i:-n].get_text() == text[i:-n]
            assert model[-i:].get_text() == text[-i:]


def test_10():
    "split"
    t = TextModel(text1+'\n'+text2)
    n = len(t)
    for i in range(len(t)+1):
        #print i
        item1 = t[:i]
        item2 = t[i:]
        assert len(item1)+len(item2) == n


def test_11():
    "properties"
    t = TextModel(text1+'\n'+text2)
    t.set_properties(5, 15, selected=True)
    t.set_properties(5, 15, selected=False)
    #print t.texel
    t.get_style(5) == {
        'bgcolor': 'white', 'textcolor': 'black', 'fontsize': 10,
        'selected': False}


def test_12():
    "remove all"
    t = TextModel(text1+'\n'+text2)
    t.remove(0, len(t))

def test_13():
    'ENDMARK'
    t = TextModel(text1+'\n'+text2)
    assert length(t.get_xtexel()) == length(t.texel)+1
    #t.extended_texel().dump()

def heavy_test():
    'pycolorize'
    filename = 'textmodel/textmodel.py'
    rawtext = open(filename).read()
    pycolorize(rawtext)


def test_14():
    "random insert/remove"
    class TestModel(TextModel):
        defaultstyle = create_style(s=10)

    model = TestModel(u'0123')
    from random import randrange, choice


    n = len(model)
    for j in range(1000):
        i1 = randrange(n)
        i2 = randrange(n)
        i1, i2 = sorted([i1, i2])

        model.remove(i1, i2)

        m = i2-i1
        text = u'abcdefghijkl'[:m]
        i1 = randrange(len(model))

        size = choice([6, 8, 10, 14])

        model.insert(i1, TestModel(text, s=size))

        assert not "C(u'')" in str(model.texel)


def test_15():
    "get/set styles"

    s0 = TextModel.defaultstyle
    s1 = create_style(bgcolor='red')

    t = Text(text1)
    assert get_styles(t, 0, length(t)) == [(length(t), s0)]

    t = grouped(set_properties(t, 3, 5, {'bgcolor':'red'}))
    styles = get_styles(t, 0, length(t))
    assert styles == [
        (3, s0),
        (2, s1),
        (5, s0),
        ]

    # Override styling
    n = length(t)
    t = grouped(set_styles(t, 0, StyleIterator(iter([(n, s0)]))))
    assert get_styles(t, 0, length(t)) == [(n, s0)]

    # And revert
    t = grouped(set_styles(t, 0, StyleIterator(iter(styles))))
    styles = get_styles(t, 0, length(t))
    assert styles == [
        (3, s0),
        (2, s1),
        (5, s0),
        ]

    # Merge styles:
    styles = get_styles(Group([Text(text1), Text(text1)]),
             0, 2*len(text1))
    assert len(styles) == 1
    assert styles[0][0] == 2*len(text1)


def test_16():
    "undo properties"
    s0 = TextModel.defaultstyle
    s1 = create_style(fontsize=3)

    model = TextModel(text1)
    old = model.set_properties(2, 5, fontsize=3)
    styles = get_styles(model.texel, 0, len(model))
    assert styles == [
        (2, s0),
        (3, s1),
        (5, s0),
        ]
    model.set_styles(2, old)
    styles = get_styles(model.texel, 0, len(model))
    assert styles == [
        (10, s0)
        ]

def test_17():
    "Tabulator"
    text = "line 1\nline 2\tcol 1\tcol2\n\n"
    model = TextModel(text)
    #model.texel.dump()
    assert model.get_text() == text


def test_18():
    "dump_range"
    t = TextModel(text1+'\n'+text2)
    dump_range(t.texel, 1, 10)


__all__ = ['TextModel']
