# -*- coding: latin-1 -*-

# Siehe Notizbuch um den 8. Mai 2016
#
# Wir brauchen genau 4 Elemente in dem Texelbaum:
# - Gruppen
# - Container
# - Glyphs
# - Text
#
# Text sind allgmein Sequenzen von Glyphs (Arrays). Container
# sind die Basis für Tabellen und Formeln. Die 4 Grundelemente lassen
# sich unterteilen in Child-Elemente (Gruppen, Container) und
# Blattelemente (Glyphs und Text).
#
# Anders als in biserigen Entwürfen gibt es keine leeren
# Indexpositionen. Das bedeutet für den Container, dass er ganz anders
# implementiert wird, als bisher. Beispielsweise der Bruch würde wie
# folgt realisiert:
#
# Bruch(Container):
#   - TAB
#   - Nenner
#   - TAB
#   - Zähler
#   - TAB
#
# 


debug = 1
nmax = 15

def set_nmax(n):
    """Sets $nmax$ to the value $i$.

       The value nmax determines the number of childs per group (which
       should be between nmax/2 and nmax for efficient trees).
    """
    global nmax
    nmax = n

EMPTYSTYLE = {}

class Texel:
    is_glyph = 0
    is_container = 0
    is_group = 0
    is_text = 0
    weights = (0, 0, 0) # depth, length, lineno


class Glyph(Texel):
    is_glyph = 1
    weights = (0, 1, 0)
    style = EMPTYSTYLE

    def set_style(self, style):
        clone = shallow_copy(self)
        clone.style = style
        return clone


class Text(Texel):
    is_text = 1
    def __init__(self, text, style=EMPTYSTYLE):
        self.text = text
        self.style = style
        self.weights = (0, len(text), 0)

    def __repr__(self):
        return "T(%s)" % repr(self.text)


class _TexelWithChilds(Texel):
    functions = (
        lambda l:max(l)+1, 
        sum,               
        sum,               
        )

    def compute_weights(self):
        if len(self.childs): # for empty groups, we use the default weights
            w_list = zip(*[child.weights for child in self.childs])
            self.weights = [f(l) for (l, f) in zip(w_list, self.functions)]



class Group(_TexelWithChilds):
    is_group = 1
    def __init__(self, childs):
        self.childs = childs
        self.compute_weights()

    def __repr__(self):
        return 'G(%s)' % repr(list(self.childs))



class Container(_TexelWithChilds):
    is_container = 1
        
    def set_childs(self, childs):
        clone = shallow_copy(self)
        clone.childs = childs
        clone.compute_weights()
        return clone

    def __repr__(self):
        return 'C(%s)' % repr(list(self.childs))

    def get_spans(self):
        is_separator = True
        r = []
        for i1, i2, child in iter_childs(self):
            if not is_separator:
                r.append(i1, i2)
            is_separator = not is_separator
        return r
        

class NewLine(Glyph):
    weights = (0, 1, 1)
    style = EMPTYSTYLE
    parstyle = EMPTYSTYLE
    text = u'\n'

    def __repr__(self):
        return 'NL'

    def set_parstyle(self, style):
        clone = shallow_copy(self)
        clone.parstyle = style
        return clone


class EndMark(NewLine):
    pass


class Tabulator(Glyph):
    text = u'\t'

    def __repr__(self):
        return 'TAB'


class Fraction(Container):
    def __init__(self, denominator, nominator):
        self.childs = (TAB, denominator, TAB, nominator, TAB)
        self.compute_weights()
    

# ---- functions -----
def depth(texel):
    """Returns the depth of an element.

       The depth can be definied as the number of generations of
       groups. By definition empty groups have depth 0.

       >>> depth(Text('abc'))
       0

       >>> depth(G(Text('abc')))
       1

       >>> depth(G()) # empty groups are ignored
       0
    """
    return texel.weights[0]


def length(texel):
    """Returns the length of $texel$ in index units."""
    return texel.weights[1]


def spans(texel):
    if not texel.is_container:
        return 0, length(texel)
    return texel.get_spans()


def iter_childs(texel):
    assert texel.is_group or texel.is_container
    i1 = 0
    for child in texel.childs:
        i2 = i1+length(child)
        yield i1, i2, child
        i1 = i2    


def replace_childs(texel, i1, i2, stuff):
    """Replace all child texels in $i1$...$i2$ by the elements in list
$stuff$."""
    assert texel.is_group or texel.is_container
    assert 0 <= i1 <= i2 <= length(texel)
    stuff = filter(length, stuff) 
    r1 = []
    r2 = []
    for j1, j2, item in iter_childs(texel):
        if j2 <= i1:
            r1.append(item)
        elif j1 >= i2:
            r2.append(item)
        elif i1 <= j1 <= j2 <= i2:
            # Item is beeing replaced
            pass
        else:
            # Item overlaps i1, i2. This is not allowed!
            raise IndexError((i1, i2))
        j1 = j2
    if texel.is_container:
        return texel.set_childs(r1+stuff+r2)        
    return groups(join(r1, stuff, r2))


def groups(l):
    """Transform the list of texels $l$ into a list of groups.

       If texels have depth d, groups will have depth d+1.

       pre:
           is_elementlist(l)
           is_homogeneous(l)

       post[l]:
           is_homogeneous(__return__)
           calc_length(l) == calc_length(__return__)
           #out("groups check: ok")
    """
    r = []
    N = len(l)
    if N == 0:
        return r

    n = N // nmax
    if n*nmax < N:
        n = n+1
    rest = n*nmax-N

    a = nmax-float(rest)/n
    b = a
    while l:
        i = int(b+1e-10)
        r.append(Group(l[:i]))
        l = l[i:]
        b = b-i+a
    return r


def _join(l1, l2):
    l1 = filter(length, l1) # strip off empty elements
    l2 = filter(length, l2) #
    if not l1:
        return l2
    if not l2:
        return l1
    t1 = l1[-1]
    t2 = l2[0]
    d1 = depth(t1)
    d2 = depth(t2)
    if d1 == d2:
        return l1+l2
    elif d1 > d2:
        return l1[:-1]+groups(_join(t1.childs, l2))
    # d1 < d2
    return groups(_join(l1, t2.childs))+l2[1:]


def join(*args):
    """Join several homogeneous lists of elements.

       The returned list is homogeneous.

       pre:
           forall(args, is_elementlist)
           forall(args, is_homogeneous)

       post[args]:
           is_homogeneous(__return__)
           sum([calc_length(x) for x in args]) == calc_length(__return__)
           #out("join check: ok")
    """
    return reduce(_join, args)


def insert(element, i, stuff):
    """Inserts the list $stuff$ at position $i$.

       Returns a list of elements. Unlike simple_insert, stuff can
       contain elements with depth>0.  Note that insert can increase
       the elements depth. The returned list is always homogeneous.

       pre:
           isinstance(element, Texel)
           is_elementlist(stuff)
           is_homogeneous(stuff)

       post[element, stuff]:
           calc_length(__return__) == length(element)+calc_length(stuff)
           is_homogeneous(__return__)
    """
    if not 0 <= i <= length(element):
        raise IndexError(i)
    if element.is_group or element.is_container:
        k = -1
        for i1, i2, child in iter_childs(element):
            k += 1
            if i1 <= i <= i2:
                new = insert(child, i-i1, stuff)
                # XXX this can change the number of childs and is
                # therefore not correct for containers!                  
                # XXX and this can change the depth!
                return replace_childs(element, i1, i2, new)
    return join(copy(element, 0, i), stuff, copy(element, i, length(element)))


def takeout(texel, i1, i2):
    """Takes out all content between $i1$ and $i2$.

    Returns the rest and the cut out piece, i.e.
    G([a, b, c]).takeout(i1, i2) will return G([a, c]), b.

    pre:
        is_root_efficient(texel)

    post:
        is_elementlist(__return__[0])
        is_elementlist(__return__[1])
        is_homogeneous(__return__[0])
        is_homogeneous(__return__[1])
        calc_length(__return__[0])+i2-i1 == length(texel)
        calc_length(__return__[1]) == i2-i1
        #out("takeout", texel, i1, i2)
        #out(__return__[0])
        #out(__return__[1])
        is_list_efficient(__return__[0])
        is_list_efficient(__return__[1])
    """
    if not (0 <= i1 <= i2 <= length(texel)):
        raise IndexError([i1, i2])
    if not length(texel):
        return [], []
    if i1 == i2:
        return [texel], []
    if i1 <= 0 and i2 >= length(texel):
        return [], [texel]

    if texel.is_group:
        r1 = []; r2 = []; r3 = []; r4 = []
        k1 = []; k2 = []; k3 = []
        for j1, j2, child in iter_childs(texel):
            if j2 <= i1:
                r1.append(child)
            elif i1 <= j1 <= j2 <= i2:
                k2.append(child)
            elif j1 <= i1 <= j2:
                r, k = takeout(child, max(i1-j1, 0), min(i2-j1, length(child)))
                r2.extend(r)
                k1.extend(k)
            elif j1 <= i2 <= j2:
                r, k = takeout(child, max(i1-j1, 0), min(i2-j1, length(child)))
                r3.extend(r)
                k3.extend(k)
            elif i2 <= j1:
                r4.append(child)
        # Note that we are returning a list of elements which have
        # been in the content before. Therefore, we are decreasing the
        # depth by 1 (or more). This is the reason why the returned
        # lists are list_efficient. The correctness of the approach
        # can be seen from full induction.
        return join(r1, r2, r3, r4), join(k1, k2, k3)
        
    elif texel.is_container:
        for k, (j1, j2, child) in enumerate(iter_childs(texel)):
            if  i1 < j2 and j1 < i2: # test of overlap
                if not (j1 <= i1 and i2 <= j2):
                    raise IndexError((i1, i2))
                childs = list(texel.childs) # list erzeugt immer eine Kopie!
                tmp, kern = takeout(
                    child, max(0, i1-j1), min(len(self), i2-j1))
                childs[k] = grouped(tmp)
                return [texel.set_childs(childs)], kern
        raise IndexError((i1, i2))

    elif texel.is_text:
        r1 = self.text[:i1]
        r2 = self.text[i2:]
        r3 = self.text[i1:i2]
        s = self.style
        return [Text(r1+r2, s)], [Text(r3, s)]

    assert False


def copy(root, i1, i2):
    """Copy all content of $root$ between $i1$ and $i2$.

       pre:
           isinstance(root, Texel)

       post[i1, i2]:
           calc_length(__return__) == (i2-i1)
    """
    return takeout(root, i1, i2)[1]


def grouped(stuff):
    """Creates a single group from the list of texels $stuff$.

       If the number of texels exceeds nmax, subgroups are formed.
       Therefore, the depth can increase. Note that stuff is not
       allowed to be empty.

       pre:
           is_elementlist(stuff)
           is_homogeneous(stuff)
           
       post[stuff]:
           length(__return__) == calc_length(stuff)
    """
    while len(stuff) > nmax:
        stuff = groups(stuff)
    g = Group(stuff)
    return strip(g)


def strip(element):
    """Removes unnecessary Group-elements from the root.
    """
    n = length(element)
    while element.is_group and len(element.childs) == 1:
        element = element.childs[0]
    assert n == length(element)
    return element


def provides_childs(texel):
    """Returns True if $texel$ provides the childs_interface."""
    return texel.is_group or texel.is_container


def get_rightmost(element):
    if provides_childs(element):
        return get_rightmost(element.childs[-1])
    return element


def get_leftmost(element):
    if provides_childs(element):
        return get_leftmost(element.childs[0])
    return element


def exchange_rightmost(element, new):
    """Replace the rightmost subelement of $element$ by $new$.

       pre:
           depth(new) == 0
       post[element]:
           depth(__return__) == depth(element)
    """
    if provides_childs(element):
        l = exchange_rightmost(element.childs[-1], new)
        return Group(element.childs[:-1]+[l])
    return new


def remove_leftmost(element):
    """Removes the leftmost subelement of $element$.

       Note that this function can return an empty group.
       Also note, that this function can change the depth. 
    """
    if element.is_group:
        l = remove_leftmost(element.childs[0])
        return Group([l]+element.childs[1:])
    return Group([])


def can_merge(texel1, texel2):
    return texel1.is_text and texel2.is_text and \
           texel1.style is texel2.style


def merge(texel1, texel2):
    """Merge the rightmost child of $texel1$ with the leftmost child of
$texel2$.

       pre:
           isinstance(texel1, Texel)
           isinstance(texel2, Texel)
           can_merge(texel1, texel2)

       post[texel1, texel2]:
           length(__return__) == length(texel1)+length(texel2)
    """
    return Text(texel1.text+texel2.text, texel1.style)


def _heal(element, i):
    n = length(element)
    if not provides_childs(element):
        return [element]
    last_child = None
    l1 = None # indices of last texel
    l2 = None # 
    for i1, i2, child in iter_childs(element):
        if i1 == i and last_child is not None and i1 == l2:
            left = get_rightmost(last_child)
            right = get_leftmost(child)
            if can_merge(left, right):
                new = merge(left, right)
                # XXX UNFIXED BUG: remove_can change the depth!
                l = [exchange_rightmost(last_child, new),
                     remove_leftmost(child)]
                return replace_childs(element, l1, i2, l)

        elif i1 < i < i2:
            return replace_childs(element, i1, i2, _heal(child, i-i1))
        last_child = child
        l1 = i1
        l2 = i2
    return [element]


def heal(element, *indices):
    """Do a heal operation at positions $indices$ of element.

       post[element]:
           length(__return__) == length(element)
    """
    n = length(element)
    for i in indices:
        element = grouped(_heal(element, i))
    return element


def get_text(texel):
    if texel.is_glyph or texel.is_text:
        return texel.text
    assert texel.is_group or texel.is_container
    return u''.join([get_text(x) for x in texel.childs])


# ---- Debug Tools ---
def extract_text(element): # XXX REMOVE?
    # for testing
    if type(element) in (list, tuple):
        return u''.join([extract_text(x) for x in element])
    elif element.is_text or element.is_glyph:
        return element.text
    return u''.join([extract_text(x) for x in element.childs])


def calc_length(l):
    """Calculates the total length of all elements in list $l$."""
    return sum([length(x) for x in l])


def is_homogeneous(l):
    """Returns True if the elements in list *l* are homogeneous.

       Elements are homogeneous if they have alle the same depth.
    """
    return maxdepth(l) == mindepth(l)


def is_element_efficient(element):
    """Returns True if $element$ is efficient.

       An element is efficient, if it is not a group or otherwise if
       all of the following criteria are fulfilled:

       1. if each descendant group has between nmax/2 and nmax childs
       2. the depth of all childs is homogeneous

       In an efficient tree all groups (with the exception of the root
       node) must be element_efficient.

       Note: this function is very slow and should only be used for
       debugging.
    """
    if not is_group(element):
        return True
    if not is_homogeneous(element.childs):
        return False
    if len(element.childs) < nmax/2 or len(element.childs) > nmax:
        return False
    if not is_list_efficient(element.childs):
        return False
    return True


def is_list_efficient(l):
    """Returns True if the list of $l$ of elements is efficient.
    """
    if not is_homogeneous(l):
        return False
    for element in l:
        if not is_element_efficient(element):
            return False
    return True


def is_root_efficient(root):
    """Returns True if $root$ is efficient.

       The tree spawned by $root$ is efficient if it is either not a
       group or otherwise if it fulfills all of the following
       conditions:

       1. all childs are efficient
       2. the number of childs is <= nmax

       Note: this function is very slow and should only be used for
       debugging.
    """
    if not is_group(root):
        return True
    if len(root.childs) > nmax:
        return False
    return is_list_efficient(root.childs)


def is_group(element):
    return element.is_group


def is_elementlist(l):
    """Returns True if $l$ is a list of Elements.
    """
    if not type(l) in (tuple, list):
        print "not a list or tuple", type(l), l.__class__ # XXX remove this
        return False
    return not False in [isinstance(x, Texel) for x in l]


def maxdepth(l):
    """Computes the maximal depth of all elements in list $l$.
    """
    m = [depth(x) for x in l if length(x)]
    if not m:
        return 0
    return max(m)


def mindepth(l):
    """Computes the minimal depth of all elements in list $l$.
    """
    m = [depth(x) for x in l if length(x)]
    if not m:
        return 0
    return min(m)


def out(*args):
    print repr(args)[1:-1]
    return True


def dump(texel, i=0):
    print (" "*i)+str(texel.__class__.__name__), texel.weights,
    if texel.is_text:
        print repr(texel.text), texel.style
    else:
        print
    if texel.is_group or texel.is_container:
        for i1, i2, child in iter_childs(texel):
            dump(child, i+2)



def dump_list(l):
    print "Dumping list (efficient: %s)" % is_list_efficient(l)
    for i, element in enumerate(l):
        print "Dumping element no. %i" % i,
        print "(efficient: %s)" % is_element_efficient(element)
        dump(element)
    return True

# --- Singeltons ---
TAB = Tabulator()
NL = NewLine()
ENDMARK = EndMark()






# --- Tests ---
G = Group
T = Text


if debug:
     #enable contract checking
     import contract
     contract.checkmod(__name__)


def test_04():
    "insert"
    set_nmax(4)
    s = G([T('1'), T('2'), T('3')])
    element = G([s, s, s])

    tmp = insert(element, 3, [T('X'), T('Y')])
    assert depth(grouped(tmp)) == depth(element)
    assert extract_text(tmp) == '123XY123123'

    tmp = insert(element, 3, [G([T('X'), T('Y')])])
    assert depth(grouped(tmp)) == depth(element)
    assert extract_text(tmp) == '123XY123123'

    tmp = insert(grouped(tmp), 3, [G([T('Z'), T('#')])])
    assert extract_text(tmp) == '123Z#XY123123'


def test_05():
    "growth in insert"
    set_nmax(3)
    g = Group([T("a"), T("b"), T("c")])
    assert depth(g) == 1
    assert repr(insert(g, 0, [T("d")])) == \
        "[G([C('d'), C('a')]), G([C('b'), C('c')])]"


def test_06():
    "efficient insert / takeout"
    set_nmax(3)
    texel = Group([])
    import random
    for i in range(100):
        x = random.choice("abcdefghijklmnopqrstuvwxyz")
        tmp = insert(texel, i, [Text(x)])
        assert is_list_efficient(tmp)
        texel = grouped(tmp)
    assert is_root_efficient(texel)
    #dump(texel)

    while length(texel):
        i1 = random.randrange(length(texel)+1)
        i2 = random.randrange(length(texel)+1)
        i1, i2 = sorted([i1, i2])
        r, k = takeout(texel, i1, i2)
        assert is_list_efficient(r)
        texel = grouped(r)
    assert is_root_efficient(texel)


def test_07():
    "depth"
    assert depth(Text('abc')) == 0
    assert depth(G([Text('abc')])) == 1
    assert depth(G([])) == 0
    element = G([G([G([T('1'), T('2')]), G([T('3')])])])
    assert depth(element) == 3


def test_08():
    "heal"
    t = G([T("01234"), T("56789")])
    assert str(heal(t, 5)) == "T('0123456789')"

    t = G([G([T("01234")]), G([T("56789")])])
    assert str(heal(t, 5)) == "T('0123456789')"

    t = G([G([T("01234")]), T("56789")])
    assert str(heal(t, 5)) == "T('0123456789')"


if __name__ == '__main__':
    import alltests
    alltests.dotests()
    
