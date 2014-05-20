# -*- coding: latin-1 -*-


from base import Group, NULL_TEXEL, Glyph
from copy import copy as shallowcopy
import listtools
import texel


class Empty(Glyph):
    # Steuerzeichen, das für "leere" Positionen verwendet wird. Wird
    # nur im Zusammenhang mit Container benutzt.
    new_line = False
    def __repr__(self):
        return 'Empty()'

    def get_linelengths(self):
        if self.new_line:
            return [1]
        return []

EMPTY = Empty()
EMPTY_NL = Empty()
EMPTY_NL.new_line = True


class Container:
    # Container ist eine Basisklasse für Texel mit Kindelementen. Dazu
    # wird in abgeleiteten Klassen get_childs und replace
    # implementiert. Die Kinder müssen im Indexraum dicht
    # liegen. Statt Löchern kann kann ein Steuerzeichen (Empty)
    # verwendet werden.
    #
    # Methodenanfragen werden an die Kinder weitergeleitet. Dieses
    # Verhalten kann durch Ableiten neuer Klassen geändert werden.

    def from_childs(self, childs):
        # Erzeuge Clone ausgehend von Childs
        raise NotImplemented()

    def replace(self, i, new):
        # Ersetzt das Kind an Position i mit new
        l = []
        found = False
        for j1, j2, child in self.iter():
            if j1 == i:
                l.append(new)
                found = True
            else:
                l.append(child)
        assert found
        return self.from_childs(l)

    def __len__(self): 
        n = 0
        for texel in self.get_childs():
            n += len(texel)
        return n

    def get_content(self):
        return Group(self.get_childs())

    def iter(self):
        j1 = 0
        for child in self.get_childs():
            j2 = j1+len(child)
            yield j1, j2, child
            j1 = j2
        
    def get_text(self):
        return self.get_content().get_text()
        
    def get_style(self, i):
        return self.get_content().get_style(i)

    def get_linelengths(self):
        return self.get_content().get_linelengths()

    def get_styles(self, i1, i2):
        return self.get_content().get_styles(i1, i2)

    def set_styles(self, i, styles):
        data = []
        childs = list(self.get_childs())
        while childs:
            # XXX kann optimiert werden!
            data.append(child.set_styles(i, styles))
            i -= len(child)
        return self.from_childs(data)

    def set_properties(self, i1, i2, properties):
        l = []
        for child in self.get_childs():
            n = len(child)
            if i1<=n and i2>=0:
                child = child.set_properties(i1, i2, properties)
                l.append(child)
                i1 -= n
                i2 -= n            
        return checked(group(l))
        
    def split(self, i):
        if i == 0:
            return NULL_TEXEL, Group([self]) 
        elif i == len(self):
            return Group([self]), NULL_TEXEL
        return self.get_content().split(i)
        
    def takeout(self, i1, i2):
        if i1 <= 0 and i2 >= len(self):
            return NULL_TEXEL, self
        k1, k2, items = listtools.get_items(self.get_childs(), i1, i2)
        items = [x for x in items if len(x)] # leere Items ausfiltern!
        if len(items) == 0:
            return self, NULL_TEXEL
        if len(items)>1:
            raise IndexError, (i1, i2)
        item = items[0]
        rest, part = item.takeout(i1-k1, i2-k1)
        return self.replace(k1, rest), part

    def insert(self, i, texel):
        for j1, j2, elem in self.iter():
            if isinstance(elem, Empty):
                continue
            if j1 <= i <= j2:
                new = elem.insert(i-j1, texel)
                return self.replace(j1, new)

        if i == 0: # muss ein Empty auf der ersten Position haben!
            return Group([texel, self])

        # muss ein empty auf der letzten Position haben
        assert i == len(self)
        return Group([self, texel])

    def simplify(self, i):
        return self

    def dump(self, i=0):
        name = self.__class__.__name__
        print (" "*i)+name+"(["
        for texel in self.get_childs():
            texel.dump(i+4)
        print (" "*i)+"])"



def test_00():
    "container"
    c = Container()
    assert texel.check(c)

def test_01():
    "empty"
    e = Empty()
    assert texel.check(e)


if __name__ == '__main__':
    import alltests
    alltests.dotests()
