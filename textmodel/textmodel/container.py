# -*- coding: latin-1 -*-

from . import treebase
from . import texeltree
from .texeltree import Texel, NULL_TEXEL, G, grouped, defaultstyle, \
      updated_style, _style_add, SPACE
from .treebase import join, simple_insert
from .listtools import calc_length, listjoin


class Container(Texel, treebase.Element):
    has_childs = True
    def __init__(self, style=defaultstyle):
        self.style = style
        w_list = zip(*[child.weights for i1, i2, child in self.iter_extended()])
        self.weights = [f(l) for (l, f) in zip(w_list, self.functions)]
        self.weights[0] = 0 # Containers have depth 0!

    def get_content(self):
        raise NotImplemented()

    def get_kwds(self):
        return {'style' : self.style}

    def is_emptypos(self, i):
        for j1, j2, child in self.iter_childs():
            if i == j1-1:
                return True
        if i == len(self):
            return True

    def iter_extended(self):
        empties = self.get_empties()
        yield 0, 1, empties[0]
        i1 = 1
        for child, empty in zip(self.get_content(), empties[1:]):
            i2 = i1+len(child)
            yield i1, i2, child
            yield i2, i2+1, empty
            i1 = i2+1

    ### default implementations
    def get_emptychars(self):
        # default: treat empty positions as spaces
        return u' ' * (len(self.get_content())+1)

    def get_empties(self):
        # Can be overridden
        return (SPACE,) * (len(self.get_content())+1)

    def get_child(self, i):
        for j1, j2, child in self.iter_childs():
            if j1 <= i <= j2:
                return j1, j2, child
        raise IndexError(i)

    ### texel interface
    def get_style(self, i):
        for j1, j2, child in self.iter_childs():
            if j1 <= i < j2:
                return child.get_style(i-j1)
        return self.style

    def get_text(self):
        emptychars = self.get_emptychars()
        content = self.get_content()
        assert len(emptychars) == len(content)+1
        t = emptychars[0]
        for i, child in enumerate(content):
            t += child.get_text()+emptychars[i+1]
        return t

    def get_styles(self, i1, i2):
        styles = []
        if i1 < 1 and i2 > 0:
            styles.append((1, self.style))
        i1 -= 1
        i2 -= 1
        for texel in self.get_content():
            n = len(texel)
            if i1 < n and i2 > 0:
                #print i1, i2, texel.get_styles(i1, i2)
                styles = listjoin(styles, texel.get_styles(i1, i2),
                                  _style_add)
                #styles.append(texel.get_styles(i1, i2))
            i1 -= n
            i2 -= n
            if i1 < 1 and i2 > 0:
                styles = listjoin(styles, [(1, self.style)],
                                  _style_add)
                #styles.append((1, self.style))
            i1 -= 1
            i2 -= 1
        return styles

    def set_styles(self, i, styles):
        content = list(self.get_content())
        j = -1
        for j1, j2, child in self.iter_childs():
            j += 1
            if  i<j2:
                content[j] = child.set_styles(i-j1, styles)
        empties = set([0]) # empty indices
        for j1, j2, child in self.iter_childs():
            empties.add(j1-1)
            empties.add(j2)
        empties = list(sorted(empties))
        j1 = i
        style = self.style
        for j, _style in styles:
            j2 = j1+j
            for e in empties:
                if j1 <= e <= j2:
                    style = _style
        kwds = self.get_kwds()
        kwds.update(style=style)
        return self.__class__(*content, **kwds)

    def set_properties(self, i1, i2, properties):
        content = list(self.get_content())
        style = self.style
        for j1, j2, child in self._iter_extended():
            if  i1 < j2 and j1 < i2: # test of overlap
                if child is None:
                    style = updated_style(style, properties)
                else:
                    new = grouped(child.set_properties(i1-j1, i2-j1,
                                                   properties))
                    i = content.index(child)
                    content[i] = new
        kwds = self.get_kwds()
        kwds['style'] = style
        return [self.__class__(*content, **kwds)]

    ### Element interface
    def __len__(self):
        childs = self.get_content()
        return len(childs)+1+calc_length(childs)

    def iter_childs(self):
        i1 = 1
        for child in self.get_content():
            i2 = i1+len(child)
            yield i1, i2, child
            i1 = i2+1

    def _iter_extended(self):
        # Helper
        yield 0, 1, None
        i1 = 1
        for child in self.get_content():
            i2 = i1+len(child)
            yield i1, i2, child
            yield i2, i2+1, None
            i1 = i2+1

    def replace_child(self, i1, i2, stuff):
        content = list(self.get_content())
        if i1 == i2: # insert
            if i1 == 0:
                 return join(stuff, [self])
            elif i1 == len(self):
                return join([self], stuff)
            j1, j2, child = self.get_child(i1)
            if i1 == j1:
                new = grouped(join(stuff, [child]))
            else:
                if not i1 == j2:
                    raise IndexError((i1, i2))
                new = grouped(join([child], stuff))
            i = content.index(child)
            content[i] = new
        else: #replace_child
           j1, j2, child = self.get_child(i1)
           if not (j1 == i1 and j2 == i2):
               # i1..i2 must be the interval occupied by one child.
               raise IndexError((i1, i2))
           i = content.index(child)
           content[i] = grouped(stuff)
        return [self.__class__(*content, **self.get_kwds())]

    def takeout(self, i1, i2):
        assert i1 >= 0
        assert i2 <= len(self)
        if i1 == i2:
            return [self], []
        if i1 <= 0 and i2 >= len(self):
            return [], [self]
        for k, (j1, j2, child) in enumerate(self.iter_childs()):
            if  i1 < j2 and j1 < i2: # test of overlap
                if not (j1 <= i1 and i2 <= j2):
                    raise IndexError((i1, i2))
                childs = list(self.get_content())
                tmp, kern = child.takeout(
                    max(0, i1-j1), min(len(self), i2-j1))
                childs[k] = grouped(tmp)
                return [self.__class__(*childs, **self.get_kwds())], \
                       kern
        raise IndexError((i1, i2))


def iter_extended(texel):
    if isinstance(texel, Container):
        for i1, i2, child in texel.iter_extended():
            yield i1, i2, child
    else:
        for i1, i2, child in texel.iter_childs():
            yield i1, i2, child


class Fraction(Container):
    # a simple demo
    def __init__(self, denom, nom, style=defaultstyle):
        self.denom = denom
        self.nom = nom
        Container.__init__(self, style)

    def get_content(self):
        return self.denom, self.nom

    def get_emptychars(self):
        return '(;)'


def test_00():
    "get_styles/set_styles"

    from .texeltree import Characters
    frac = Fraction(Characters("denominator"), Characters("nominator"))
    n = len(frac)
    assert frac.get_styles(0, n) == [(n, defaultstyle)]
    assert frac.get_styles(1, n) == [(n-1, defaultstyle)]
    assert frac.get_styles(2, n) == [(n-2, defaultstyle)]
    assert frac.get_styles(2, n-1) == [(n-3, defaultstyle)]
    assert frac.get_styles(0, 1) == [(1, defaultstyle)]

    tmp = frac.set_styles(0, [(1, None)])
    assert tmp.get_styles(0, 1) == [(1, None)]
    assert tmp.get_styles(0, 2) == [(1, None), (1, defaultstyle)]

def test_01():
    "get_text"
    from .texeltree import Characters
    frac = Fraction(Characters("denominator"), Characters("nominator"))
    assert frac.get_text() == '(denominator;nominator)'

def test_02():
    "insert"
    from .texeltree import Characters
    from .treebase import insert
    frac = Fraction(Characters("denominator"), Characters("nominator"))
    elem = frac
    text = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"
    for i in range(len(text)):
        #print i
        tmp = insert(elem, 17, [Characters(text[i])])
        assert calc_length(tmp) == len(elem)+1
        elem = grouped(tmp)

    from .treebase import dump
    #dump(elem)

def test_010():
    from .texeltree import Characters, check
    frac = Fraction(Characters("denominator"), Characters("nominator"))
    assert check(frac)
    assert frac.get_text() == '(denominator;nominator)'
    tmp = frac.replace_child(1, 12, [Characters('x')])[0]
    assert tmp.get_text() == '(x;nominator)'
    try:
        frac.replace_child(1, 13, [Characters('x')])
        assert False
    except IndexError:
        pass

    rest, kern = frac.takeout(5, 11)
    assert G(rest).get_text() == '(denor;nominator)'
    assert G(kern).get_text() == 'minato'

    rest, kern = frac.takeout(13, 14)
    assert isinstance(rest[0], Fraction)
    assert G(rest).get_text() == '(denominator;ominator)'
    assert G(kern).get_text() == 'n'
    assert len(G(rest)) == len(frac)-1
    assert len(G(kern)) == 1

    for i in range(len(frac)+1):
        if frac.is_emptypos(i):
            continue
        simple_insert(frac, i, [Characters('x')])

def test_011():
    "heal"
    from .texeltree import Group, Characters, TAB, heal
    frac = Fraction(Characters("denominator"), Characters("nominator"))
    assert frac.get_text()[13:14] == 'n'
    #(denominator;nominator)
    tree = G(simple_insert(frac, 13, [TAB]))
    tree.dump()
    heal(tree, 13, 14).dump()
    
    tree = G(simple_insert(frac, 13, [Characters('X')]))
    tree.dump()
    t = heal(tree, 13) # no merge possible
    assert isinstance(t.nom, Group)
    t = heal(tree, 14) # merge possible
    assert isinstance(t.nom, Characters)
