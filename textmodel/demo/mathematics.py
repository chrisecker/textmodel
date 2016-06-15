# -*- coding: latin-1 -*-

"""This demo shows how to extend the texel tree by introducing new
container types. We create two types which can be used for
typesdetting math: fraction and root. We then create a text, simulate
some editing operations by the user and print out the resulting text.

"""

import sys
sys.path.insert(0, '..')

from textmodel import TextModel
from textmodel.texeltree import Texel, T, TAB, Container, dump, get_text



class Fraction(Container):
    def __init__(self, denominator, nominator):
        self.childs = [TAB, denominator, TAB, nominator, TAB]
        self.compute_weights()



class Root(Container):
    def __init__(self, content):
        self.childs = [TAB, content, TAB]
        self.compute_weights()



def _mk_textmodel(texel):
    model = TextModel()
    model.texel = texel
    return model


EMPTY = T('')

class MyTextModel(TextModel):
    def insert_fraction(self, i):
        return self.insert(i, _mk_textmodel(Fraction(EMPTY, EMPTY)))

    def insert_root(self, i):
        return self.insert(i, _mk_textmodel(Root(EMPTY)))

    def insert_sum(self, i):
        return self.insert(i, _mk_textmodel(Sum(EMPTY, EMPTY, EMPTY, EMPTY)))


def print_math(text):
    # A very simple math printer
    def tostring(obj):
        if isinstance(obj, list):
            return ''.join([tostring(child) for child in obj])
        elif isinstance(obj, Texel):
            if obj.is_group:
                return tostring(obj.childs)
            elif obj.is_text:
                return obj.text
            elif isinstance(obj, Root):
                return "sqrt[%s]" % tostring(obj.childs[1])
            elif isinstance(obj, Fraction):
                return "(%s)/(%s)" % (tostring(obj.childs[1]),
                                      tostring(obj.childs[3]))
            else:
                return obj.text
    print tostring(text.texel)



print __doc__

text = MyTextModel()

# We simulate some user input ...

text.append('A text which contains some math\n')
text.set_properties(27, 32, underline=True)
text.append('\t')
n = len(text)
text.insert_root(n)

text.insert(n+1, '2')
text.append('= 1.414214...\n')

text.append('\t')
text.append('tan[alpha] = ')
n = len(text)
text.insert_fraction(n)
text.insert(n+2, 'cos[alpha]')
text.insert(n+1, 'sin[alpha]')

# ... and output the text
print_math(text)

print
print 'Here is the internal representation of the text:'
dump(text.texel, 8)
