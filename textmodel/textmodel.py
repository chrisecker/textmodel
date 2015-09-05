# -*- coding: latin-1 -*-


# Wir müssen darauf achten, dass das unterste Texel immer eine Gruppe
# ist. Wenn es ein Element mit Leerstellen, beispielsweise eine Zelle
# ist, dann gibt es Probleme

from base import defaultstyle, create_style, group, check, get_interval, \
    Characters, Group, NewLine, Tabulator
from modelbase import Model
import re


_split = re.compile(r"([\t\n])", re.MULTILINE).split
class TextModel(Model):
    def __init__(self, text=u'', **properties):
        style = create_style(**properties)
        l = []
        text = text.replace('\r', '')
        for part in _split(text):
            if part == '\n':
                l.append(NewLine(style))
            elif part == '\t':
                l.append(Tabulator(style))
            else:
                l.append(Characters(part, style))
        self.texel = group(l)
        self.linelengths = self.texel.get_linelengths()

    def __len__(self):
        return len(self.texel)

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'linelengths' in state:
            del state['linelengths']
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        self.linelengths = self.texel.get_linelengths()

    def nlines(self):
        return len(self.linelengths)+1

    def get_text(self, i1=None, i2=None):
        if i1 is None and i2 is None:
            return self.texel.get_text()
        if i1 is None:
            i1 = 0
        if i2 is None:
            i2 = len(self.texel)
        b, c = self.texel.split(i2)
        a, b = b.split(i1)
        return b.get_text()

    def get_style(self, i):
        return self.texel.get_style(i)
        
    def position2index(self, row, col):
        linelengths = self.linelengths        
        return sum(linelengths[:row])+col
        
    def _lfromt(self, t):
        # zum Debuggen
        splitter = t.split('\n')
        l = [len(s)+1 for s in splitter[:-1]]
        return l

    def _check_linelengths(self):
        # zum Debuggen
        t = self.get_text()
        assert self.linelengths ==  self._lfromt(t)

    def index2position(self, i):
        if i > len(self.texel):
            raise IndexError, i
        if i < 0:
            raise IndexError, i

        s = 0
        row = 0
        l = self.linelengths
        while row < len(l):
            t = s+l[row]
            if t>i:
                break
            row += 1
            s = t
        col = i-s
        return row, col

    def linestart(self, row):
        if row == 0:
            return 0
        linelengths = self.linelengths
        if row < len(linelengths):
            return sum(linelengths[:row])
        return sum(linelengths)

    def linelength(self, row):
        linelengths = self.linelengths
        if row < len(linelengths):
            return linelengths[row]
        elif row == len(linelengths):
            return len(self.texel)-sum(linelengths)
        raise IndexError, row

    def set_properties(self, i1, i2, **properties):
        memo = self.texel.get_styles(i1, i2) 
        self.texel = self.texel.set_properties(i1, i2, properties).\
            simplify(i1).simplify(i2)
        assert check(self.texel)
        self.notify_views('properties_changed', i1, i2)
        return memo

    def set_styles(self, i, styles):
        n = sum([entry[0] for entry in styles])
        memo = self.texel.get_styles(i, i+n) 
        self.texel = self.texel.set_styles(i, styles)
        self.notify_views('properties_changed', i, i+n)
        return memo

    def insert(self, i, text):
        assert isinstance(text, TextModel)        

        row, col = self.index2position(i)
        self.texel = group([
                self.texel.insert(i, text.texel). \
                    simplify(i). \
                    simplify(i+len(text))]
                )
        assert check(self.texel)

        l1 = self.linelengths
        l2 = text.linelengths
        r2 = len(text)-sum(l2)

        l_ = l1[:row]+l2+l1[row:]
        if row < len(l_):
            l_[row] += col
        if row+len(l2) < len(l_):
            l_[row+len(l2)] += r2-col
        self.linelengths = l_
        self.notify_views('inserted', i, len(text))

    def insert_text(self, i, text):
        textmodel = TextModel(text)
        self.insert(i, textmodel)

    def copy(self, i1, i2):
        row1, col1 = self.index2position(i1)
        row2, col2 = self.index2position(i2)

        b, c = self.texel.split(i2)
        a, b = b.split(i1)

        model = TextModel()
        model.texel = b
        model.linelengths = self.linelengths[row1:row2]
        if len(model.linelengths):
            model.linelengths[0] -= col1
        return model
        
    def __getitem__(self, r):
        i1, i2 = get_interval(self, r)
        return self.copy(i1, i2)

    def remove(self, i1, i2):
        row1, col1 = self.index2position(i1)
        row2, col2 = self.index2position(i2)

        texel, old = self.texel.takeout(i1, i2)
        self.texel = group([texel.simplify(i1)])

        # update der linelengths
        l = self.linelengths
        l_ = l[:]
        del l_[row1:row2]
        if row1<len(l_):
            l_[row1] += col1-col2
        self.linelengths = l_

        model = TextModel()
        model.texel = old
        model.linelengths = l[row1:row2]
        if len(model.linelengths):
            model.linelengths[0] -= col1

        self.notify_views('removed', i1, old)
        assert check(self.texel)
        return model
    
    

def check_split(texel):
    for i in range(len(texel)+1):
        a, b = texel.split(i)
        assert len(texel) == len(a)+len(b)
    try:
        texel.split(-1)
        assert False
    except IndexError:
        pass
    try:
        texel.split(len(texel)+1)
        assert False
    except IndexError:
        pass
    return True



def pycolorize(rawtext, coding='latin-1'):
    # used by benchmark
    import cStringIO
    #rawtext = model.get_text()
    instream = cStringIO.StringIO(rawtext).readline

    import token, keyword
    KEYWORD = token.NT_OFFSET + 1
    TEXT = token.NT_OFFSET + 2
    def tokeneater(toktype, toktext, (srow,scol), (erow,ecol), line):
        i1 = model.position2index(srow-1, scol)
        i2 = model.position2index(erow-1, ecol)
        if toktype == token.STRING:
            color = 'grey'
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            color = 'red'
        elif toktype == TEXT:
            color = 'green'
        #elif toktype is token.NAME:
        #    color = 'red'
        #else:
        #    color = 'black'
        else:
            return
        model.set_properties(i1, i2, textcolor=color)

    text = rawtext.decode(coding)
    model = TextModel(text)
        
    from tokenize import tokenize
    tokenize(instream, tokeneater)
    return model



text1 = "0123456789"
text2 = "abcdefghijklmnopqrstuvwxyz"
text3 = "01\n345\n\n89012\n45678\n"


def test_00():
    "remove w. simplify"
    t2 = TextModel(text2)
    
    for i in range(len(text1)):
        t = TextModel(text1)
        t.remove(i, i+1)
        assert isinstance(t.texel, Characters)

    for i in range(len(text1)):
        t = TextModel(text1)
        t.texel = Group([t.texel])
        t.remove(i, i+1)
        assert isinstance(t.texel, Characters)

    # Die Gruppe wird immer aufgelöst, wenn nur ein Element enthalten
    # ist
    for i in range(len(text1)):
        t = TextModel(text1)
        t.texel = Group([t.texel])
        t.remove(i, i+1)
        assert isinstance(t.texel, Characters)

    # Characters it unterschiedlicher Formatierung können nicht
    # zusammengefasst werden
    for i in range(2*len(text1)):
        t = TextModel(text1)
        t1 = TextModel(text1, fontsize=20)
        t.insert(len(t), t1)
        t.remove(i, i+1)
        assert isinstance(t.texel, Group)
        assert len(t.texel.data) == 2
        assert isinstance(t.texel.data[0], Characters)
        assert isinstance(t.texel.data[1], Characters)    
        text = '01234567890123456789'
        text = text[:i]+text[i+1:]
        assert t.get_text() == text

# XXXX es fehlen weitere Tests zu Simplify 


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

        assert t.texel.get_linelengths() == ll_text
        assert t.linelengths == ll_text


        for i in range(len(text)):
            row, col = t.index2position(i)
            assert (row, col) == index2position(text, i)

        for i in range(len(text)):
            row, col = index2position(text, i)
            i_ = t.position2index(row, col)
            #print text.replace('\n', 'n')
            #print "pos=", (row, col)
            #print i, i_
            assert i == i_


def test_02():
    "update linelengths bei insert"
    for i in range(len(text3)):
        t0 = TextModel(text3)
        t1 = TextModel(text3)

        ll_text = t0._lfromt(text3)
        
        assert t0.linelengths == t0.texel.get_linelengths()
        assert t0.linelengths == t0.texel.get_linelengths()
        row, col = t0.index2position(i) 
        t0.insert(i, t1)
        assert t0.linelengths == t0.texel.get_linelengths()


def test_03():
    "TextModel"
    t1 = TextModel(text1)
    assert t1.get_text() == text1
    t2 = TextModel(text2)    
    assert t2.get_text() == text2
    t3 = TextModel(text1+'\n'+text2)    
    assert t3.nlines() == 2
    assert t3.position2index(0, 5) == 5
    assert t3.position2index(1, 0) == 11
    assert t3.get_text()[10] == '\n'
    assert t3.get_text()[11] == 'a'
    assert t3.linelength(0) == len(text1)+1 # Das Return wird gezählt!
    assert t3.linelength(1) == len(text2)

    t1.insert(0, t2)
    assert  t1.get_text() == text2+text1
    t1.remove(0, len(text2))
    assert t1.get_text() == text1

    t1.insert(3, t3)
    assert t1.get_text() == text1[:3]+t3.get_text()+text1[3:]
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
    t1 = TextModel(text1)
    assert t1.get_text() == text1
    t2 = TextModel(text2)    
    assert t2.get_text() == text2
    t3 = TextModel(text1+'\n'+text2)
    
    # Styles werden immer über ihre id verglichen. Sie sind genau dann
    # gleich, wenn sie die gleiche id haben. Dafür sorgt die style
    # factory (new_style)

    assert id(t3.get_style(0)) == id(defaultstyle)

    t3.set_properties(5, 10, textcolor='red')
    t3.set_properties(3, 8, fontsize=8)

    for i in range(len(t3)):
        style = t3.get_style(i)
        if i<5:
            assert style['textcolor'] == 'black'
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

    #assert len(style_pool) == 4 # gc-abhängig

    t3.set_properties(0, len(t3), **defaultstyle)
    for i in range(len(t3)):
        style = t3.get_style(i)
        assert id(style) == id(defaultstyle)

    t3.set_properties(0, len(t3), fontsize = 6)
    s0 = t3.get_style(0)
    for i in range(len(t3)):
        style = t3.get_style(i)
        assert id(style) == id(s0)
    assert s0['fontsize'] == 6


def test_06():
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


def test_07():
    t = TextModel('\n')
    #assert is_sequence(t.data)


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
    "simplify"
    text = text1+'\n'+text2
    t = TextModel(text)    
    n = len(t)
    m = len(t.texel.data)
    assert m == 3
    # Wir haben zwei Strings und ein Newlin , daher 3. Diese Zahl
    # sollte konstant bleiben.
    for i in range(len(text)):
        x = TextModel('x')
        t.insert(i, x)  
        assert len(t.texel.data) == m
        assert len(t) == n+1
        t.remove(i, i+1)
        assert len(t) == n
        assert len(t.texel.data) == m
        assert str(t.texel) == "G([C('0123456789'), NL, C('abcdefghijklmnopqrstuvwxyz')])"


def test_10():
    "split"            
    t = TextModel(text1+'\n'+text2)
    n = len(t)
    for i in range(len(t)+1):
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
    'pycolorize'
    filename = 'textmodel.py'
    rawtext = open(filename).read() 
    pycolorize(rawtext)

    
def benchmark():
    import cProfile
    cProfile.run(test_13.__code__)


def test_14():
    "random insert/remove"
    defaultstyle.clear()
    defaultstyle['s'] = 10

    model = TextModel(u'0123')
    from random import randrange, choice


    n = len(model)
    for j in range(10000):
        i1 = randrange(n)
        i2 = randrange(n)
        i1, i2 = sorted([i1, i2])

        model.remove(i1, i2)

        m = i2-i1
        text = u'abcdefghijkl'[:m]
        i1 = randrange(len(model))

        size = choice([6, 8, 10, 14])
        
        model.insert(i1, TextModel(text, s=size))

        assert not "C(u'')" in str(model.texel)
    #model.texel.dump()


def test_15():
    "get/set styles"

    s0 = defaultstyle
    s1 = create_style(bgcolor='red')

    t = Characters(text1)
    assert t.get_styles(0, len(t)) == [(len(t), s0)]

    t = t.set_properties(3, 5, {'bgcolor':'red'})
    styles = t.get_styles(0, len(t))
    assert styles == [
        (3, s0),
        (2, s1),
        (5, s0),
        ]

    # Styling überschreiben 
    t = t.set_styles(0, [(len(t), s0)])
    assert t.get_styles(0, len(t)) == [(len(t), s0)]

    # Und wieder herstellen
    t = t.set_styles(0, styles)
    styles = t.get_styles(0, len(t))
    assert styles == [
        (3, s0),
        (2, s1),
        (5, s0),
        ]

    # Zusammenfassen von Styles:
    styles = Group([Characters(text1), Characters(text1)]).get_styles(0, 2*len(text1))
    assert len(styles) == 1
    assert styles[0][0] == 2*len(text1)


def test_16():
    "undo properties"
    s0 = defaultstyle
    s1 = create_style(fontsize=3)

    model = TextModel(text1)
    old = model.set_properties(2, 5, fontsize=3)
    styles = model.texel.get_styles(0, len(model))
    assert styles == [
        (2, s0), 
        (3, s1), 
        (5, s0),
        ]
    model.set_styles(2, old)
    styles = model.texel.get_styles(0, len(model))
    assert styles == [
        (10, s0)
        ] 

def test_17():
    "Tabulator"
    text = "line 1\nline 2\tcol 1\tcol2\n\n"
    model = TextModel(text)
    model.texel.dump()

if __name__=='__main__':
    import alltests
    alltests.dotests()
    
