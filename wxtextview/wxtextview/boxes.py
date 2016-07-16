# -*- coding: latin-1 -*-

from ..textmodel.texeltree import EMPTYSTYLE
from .testdevice import TESTDEVICE
from .rect import Rect
from math import ceil


# Coordinates:
#
#    (0,0)______________
#     |                |
#     |                |
# --(0, height)-------------
#     |                |
#     |                |
#     |__________(width, height+depth)


nmax = 15

def calc_length(l):
    """Calculates the total length of all elements in list *l*."""
    return sum([len(x) for x in l])


def groups(l):
    """Transform the list of boxes *l* into a list of groups.
    """
    r = []
    N = len(l)
    if N == 0:
        return r
    create_group = l[0].create_group

    n = N // nmax
    if n*nmax < N:
        n = n+1
    rest = n*nmax-N

    a = nmax-float(rest)/n
    b = a
    while l:
        i = int(b+1e-10)
        r.append(create_group(l[:i]))
        l = l[i:]
        b = b-i+a
    return r


def grouped(boxes):
    """Creates a single group from the list of boxes *boxes*.

       If the number of boxes exceeds nmax, subgroups are formed.
    """
    if len(boxes) == 0:
        raise ValueError("Need at least on element to group.")
        
    while len(boxes) > nmax:
        boxes = groups(boxes)
    g = boxes[0].create_group(boxes)
    return strip(g)


def strip(box):
    """Removes unnecessary Group-boxes."""
    n = len(box)
    while box.is_group and len(box.childs) == 1:
        box = box.childs[0]
    assert n == len(box)
    return box


class Box:
    # Boxes are the basic building blocks of a layout.
    width = 0
    height = 0
    depth = 0
    device = TESTDEVICE
    is_group = False # we will use this as base class for groups and
                     # non groups
    @staticmethod
    def create_group(l):
        return SimpleGroupBox(l)

    def __len__(self):
        raise NotImplementedError()

    def dump_boxes(self, i, x, y, indent=0):
        """Print out a graphical representation of the tree."""
        print " "*indent, "[%i:%i]" % (i, i+len(self)), x, y, 
        print repr(self)[:100]
        for j1, j2, x1, y1, child in self.iter_boxes(i, x, y):
            child.dump_boxes(j1, x1, y1, indent+4)

    def iter_childs(self):
        # Convenience method. 
        for i1, i2, x, y, child in self.iter_boxes(0, 0, 0):
            yield i1, i2, child 

    def from_childs(self, childs):
        """Creates a copy of $self$ where the childs a replaced by $childs$.

        Setting childs will only be implemented for boxes which have
        child boxes. For other boxes (e.g. textboxes) we will raise
        the not-implemented exception.  Returns a list of boxes, where
        each box has the same depth as $self$.
        """
        try:
            assert len(childs) == 0
        except:
            print "box:"
            self.dump_boxes(0, 0, 0)
            print "childs=", childs
            raise
        return [self]

    def iter_boxes(self, i, x, y):
        """Iter boxes yields the tuple (i1, i2, x, y, child) for all child
        boxes. Overriding this method is the way of customizing
        special boxes
        """
        height = self.height
        if False:
            # This line contains a dummy yield statement which is
            # needed because it turns this method into a generator.
            yield j1, j2, x, y+height-child.height, child

    def riter_boxes(self, i, x, y):
        # Convience method.
        return reversed(tuple(self.iter_boxes(i, x, y)))
        
    def extend_range(self, i1, i2):
        """In some situations the user may not be allowed to select from $i1$
        to $i2$. We solve this by extending the selection to a
        possible interval.
        """
        
        # This is the default implementation. It lets the children
        # decide whether the seleciton should be extended. Must to be
        # overriden if a different behaviour is needed.
        for j1, j2, x1, y1, child in self.iter_boxes(0, 0, 0):
            if i1 < j2 and j1 < i2:
                k1, k2 = child.extend_range(i1-j1, i2-j1)
                i1 = min(i1, k1+j1)
                i2 = max(i2, k2+j1)
        return i1, i2

    def responding_child(self, i, x0, y0):
        """Finds the child which is responsible for index position i. Returns
        a tuple: child, j1, x1, y1. Child is either the responsible
        child or None, j1 is the childs indexposition relative to i,
        x1 and y1 are the absolute positions of the child box.
        """
        if i<0 or i>len(self):
            raise IndexError, i
        j1 = None # marker
        for j1, j2, x1, y1, child in self.riter_boxes(0, x0, y0):
            if j1 < i <= j2:
                return child, j1, x1, y1
            elif j1 == i and child.can_leftappend():
                return child, j1, x1, y1
        if i == 0:
            return None, i, x0, y0
        if j1 is None: # -> no childs
            return None, i, x0, y0
        if i == len(self): # empty last
            return None, i, x0, y0
        # Only single index positions between child elements can be
        # empty. If two or more consecutive postions were empty, this
        # would mean that then we would have at least one position
        # without a responsible element.
        print tuple(self.riter_boxes(0, x0, y0))
        print j1, j2, i, child, child.can_leftappend()
        raise Exception, (self, i, len(self))

    def draw(self, x, y, dc, styler):
        """Draws box and all child boxes at origin (x, y)."""
        device = self.device
        for j1, j2, x1, y1, child in self.iter_boxes(0, x, y):
            r = Rect(x1, y1, x1+child.width, y1+child.height)
            if device.intersects(dc, r):
                child.draw(x1, y1, dc, styler)

    def draw_selection(self, i1, i2, x, y, dc):
        """Draws box as selected, where the selection extends from $i1$ to
        $i2$.
        """
        device = self.device
        for j1, j2, x1, y1, child in self.iter_boxes(0, x, y):
            if i1 < j2 and j1< i2:
                r = Rect(x1, y1, x1+child.width, y1+child.height)
                if device.intersects(dc, r):
                    child.draw_selection(i1-j1, i2-j1, x1, y1, dc)

    def draw_cursor(self, i, x0, y0, dc, style):
        """Draws the cursor."""
        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is not None:
            child.draw_cursor(i-j, x1, y1, dc, style)
        else:
            r = self.get_cursorrect(i, x0, y0, style)
            self.device.invert_rect(r.x1, r.y1, r.x2-r.x1, r.y2-r.y1, dc)

    def get_rect(self, i, x0, y0):
        """Returns the rectangle occupied by the Glyph at position $i$.
        XXX should be renamed to get_glyphrect(...)"""
        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is None:
            if i == len(self):
                return Rect(x1+self.width, y1+self.height, x1+self.width, y1)
            return Rect(x1, y1+self.height, x1, y1)
        return child.get_rect(i-j, x1, y1)

    def get_cursorrect(self, i, x0, y0, style):
        """Returns the BBox around the cursor at index $i$. Is used by
        draw_cursor.
        """
        child, j, x, y = self.responding_child(i, x0, y0)
        if child is not None:
            return child.get_cursorrect(i-j, x, y, style)
        else:
            m = self.device.measure('M', style)[1]
            x1, y1, x2, y2 = self.get_rect(i, x0, y0).items()
            return Rect(x1, y2-m, x1+2, y2)

    def get_index(self, x, y):
        """Returns the index which is closest to point (x, y). A return value
        of None means: no matching index position found!
        """
        print self
        raise NotImplemented # XXX
        l = [0 ,len(self)]
        for j1, j2, x1, y1, child in self.riter_boxes(0, 0, 0):
            if x1 <= x <= x1+child.width and \
                    y1 <= y <= y1+child.height+child.depth:
                i = child.get_index(x-x1, y-y1)
                if i is not None:
                    l.append(i+j1)
        return self._select_index(l, x, y)

    def _select_index(self, l, x, y):# XXX as Function
        r = []
        for i in l:
            r.append((self.get_rect(i, 0, 0).adist(x, y), -i))
        r.sort() # NOTE: this favours higher index positions!
        assert -r[0][-1] <= len(self)
        return -r[0][-1]
        
    def get_info(self, i, x0, y0): # XXX TODO: should be a function not a method
        # Returns the box object which is responsible for position i,
        # the absolute index position and the position of the
        # surrounding rect. Only used for debugging. 
        if i<0 or i>len(self):
            raise IndexError(i)

        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is None:
            x, y = self.get_rect(i, x0, y0).items()[:2]
            return self, i, x, y
        return child.get_info(i-j, x1, y1)

    def can_leftappend(self):
        # If we are inserting at an edge between two texels, both
        # texels could in principle be the target of the
        # operation. To solve this ambiguity, we usually prefere the
        # right texels. For some texels, however this doesn't make
        # sense (e.g. the square root). By returning False, Boxes of
        # such texels can signal that insert should go into the
        # other (the left) texel.
        return True


    
class _TextBoxBase(Box):
    def __len__(self):
        return len(self.text)

    def __repr__(self):
        return "TB(%s)" % repr(self.text)

    def layout(self):
        self.width, h = self.measure(self.text)
        self.height = int(ceil(h))        

    def measure(self, text):
        return self.device.measure(text, self.style)

    def measure_parts(self, text):
        return self.device.measure_parts(text, self.style)

    def dump_boxes(self, i, x, y, indent=0):
        print " "*indent, "[%i:%i]" % (i, i+len(self)), x, y, 
        print self.__class__.__name__, repr(self.text)

    ### Box-Protokoll
    def get_info(self, i, x0, y0):
        if i<0 or i>len(self.text):
            raise IndexError(i)
        x1 = x0+self.measure(self.text[:i])[0]
        return self, i, x1, y0

    def draw(self, x, y, dc, styler):
        styler.set_style(self.style)
        self.device.draw_text(self.text, x, y, dc)

    def draw_selection(self, i1, i2, x, y, dc):
        measure = self.measure
        i1 = max(0, i1)
        i2 = min(len(self.text), i2)
        x1 = x+measure(self.text[:i1])[0]
        x2 = x+measure(self.text[:i2])[0]
        self.device.invert_rect(x1, y, x2-x1, self.height, dc)

    def get_rect(self, i, x0, y0):
        text = self.text
        i = max(0, i)
        i = min(len(text), i)
        x1 = self.measure(text[:i])[0]
        x2 = self.measure((text+'m')[:i+1])[0]
        return Rect(x0+x1, y0, x0+x2, y0+self.height)

    def get_index(self, x, y):
        if x<= 0:
            return 0
        measure = self.measure
        x1 = 0
        for i, char in enumerate(self.text):
            x2 = x1+measure(char)[0]
            if x1 <= x and x <= x2:
                if x-x1 < x2-x:
                    assert i <= len(self) # XXX
                    return i
                assert i+1 <= len(self)
                return i+1
            x1 = x2
        return len(self)



class TextBox(_TextBoxBase):
    def __init__(self, text, style=EMPTYSTYLE, device=None):
        self.text = text
        self.style = style
        if device is not None:
            self.device = device
        self.layout()


class NewlineBox(_TextBoxBase):
    text = '\n'
    width = 0
    weights = (0, 1)
    def __init__(self, style=EMPTYSTYLE, device=None):        
        self.style = style
        if device is not None:
            self.device = device
        self.layout()

    def layout(self):
        w, h = self.measure(self.text)
        self.height = int(ceil(h))

    def __repr__(self):
        return 'NL'

    def get_index(self, x, y):
        # The _TextBoxBase would return index 1 for x>0 which does not
        # make sense for newlines. The last position of a line is the
        # index of the NL-Glyph, i.e. o.
        return 0
    

class TabulatorBox(_TextBoxBase):
    text = ' ' # XXX for now we treat tabs like spaces
    weights = (0, 1) 
    def __init__(self, style=EMPTYSTYLE, device=None):        
        self.style = style
        if device is not None:
            self.device = device
        self.layout()

    def __repr__(self):
        return 'TAB'



class EndBox(_TextBoxBase):
    text = chr(27)
    width = 0
    weights = (0, 1)
    def __init__(self, style=EMPTYSTYLE, device=None):
        self.style = style
        if device is not None:
            self.device = device
        self.layout()

    def __repr__(self):
        return 'ENDBOX'

    def layout(self):
        w, h = self.measure(self.text)
        self.height = int(ceil(h))


class EmptyTextBox(_TextBoxBase):
    text = ""
    width = 0
    weights = (0, 0)
    def __init__(self, style=EMPTYSTYLE, device=None):
        self.style = style
        if device is not None:
            self.device = device
        self.layout()

    def layout(self):
        w, h = self.measure('M')
        self.height = int(ceil(h))

    def __repr__(self):
        return 'ETB'



def extend_range_seperated(box, i1, i2):
    # Restrict ranges to child boundaries, e.g. in the fraction it
    # should not be possible to select a part of the nominator and a
    # part of the denominator. 
    last = 0
    for j1, j2, x, y, child in box.iter_boxes(0, 0, 0):
        if not (i1<j2 and j1<i2):
            continue
        if i1 < j1 or i2>j2:
            return min(i1, 0), max(i2, len(box))
        k1, k2 = child.extend_range(i1-j1, i2-j1)
        return min(i1, k1+j1), max(i2, k2+j1)
    return i1, i2



class ChildBox(Box):
    # Baseclass many boxes which are used to layout their content in a
    # certain way (e.g. HBox, VBox, HGroup, ...). It is assumed, that
    # boxes are dense, i.e. there is no gap between child
    # boxes. Further it is necessary that childboxes can be grouped.
    
    def __init__(self, childs, device=None):
        if device is not None:
            self.device = device
        self.childs = childs
        self.layout()

    def __len__(self):
        return self.length

    def from_childs(self, childs):
        while len(childs) > nmax:
            childs = groups(childs)
        return [self.__class__(childs, self.device)]

    def __repr__(self):
        return self.__class__.__name__+repr(list(self.childs))

    def layout(self):
        # This is a very general and slow implementation. Should be
        # reimplemented in derived classes.
        w0 = w1 = h0 = h1 = h2 = 0
        for j1, j2, x, y, child in self.iter_boxes(0, 0, 0):
            w0 = min(w0, x)
            h0 = min(h0, y)
            w1 = max(w1, x+child.width)
            h1 = max(h1, y+child.height)
            h2 = max(h2, y+child.height+child.depth)
        self.width = w1
        self.height = h1
        self.depth = h2-h1
        self.length = calc_length(self.childs)

        # h0 and w0 describe the overlapp to the left and to the right
        # respectively. They might be useful in derived classes. We
        # therefore return them.
        return w0, h0



class HBox(ChildBox):
    # A box which aligns its child boxes horizontaly. 
    def iter_boxes(self, i, x, y):
        height = self.height
        j1 = i
        for child in self.childs:
            j2 = j1+len(child)
            yield j1, j2, x, y+height-child.height, child
            x += child.width
            j1 = j2

    def layout(self):
        w = h = d = 0
        for child in self.childs:
            w += child.width
            h = max(h, child.height)
            d = max(d, child.depth)
        self.width = w
        self.height = h
        self.depth = d
        self.length = calc_length(self.childs)

    def get_index(self, x, y):
        l = [0, len(self)]
        for j1, j2, x1, y1, child in self.riter_boxes(0, 0, 0):
            if x1 <= x <= x1+child.width:
                i = child.get_index(x-x1, y-y1)
                if i is not None:
                    l.append(i+j1)
                    if len(child):
                        l.append(j1+len(child))
                        l.append(j1+len(child)-1) # This is needed for rows
        return self._select_index(l, x, y)


class Row(HBox):
    pass


class VBox(ChildBox):
    # A box which aligns its child boxes vertically.
    def iter_boxes(self, i, x, y):
        j1 = i
        for child in self.childs:
            j2 = j1+len(child)
            yield j1, j2, x, y, child
            y += child.height+child.depth
            j1 = j2

    def get_index(self, x, y):
        l = [0, len(self)]
        for j1, j2, x1, y1, child in self.riter_boxes(0, 0, 0):
            if y1 <= y <= y1+child.height+child.depth:
                l.append(j1)
                i = child.get_index(x-x1, y-y1)
                if i is not None:
                    l.append(i+j1)
                if len(child):
                    l.append(j1+len(child))
                    l.append(j1+len(child)-1) # This is needed for rows
        return self._select_index(l, x, y)



class SimpleGroupBox(ChildBox):
    # This Box is used as a dummy group to be able to temporarily
    # combine boxes. This is needed because treebase requires that all
    # elements have a corresponding group class.
    is_group = 1
    def iter_boxes(self, i, x, y):
        height = self.height
        j1 = i
        for child in self.childs:
            j2 = j1+len(child)
            yield j1, j2, x, y, child
            j1 = j2

    def layout(self):
        # all dimensions are left to 0
        self.length = calc_length(self.childs)



class HGroup(HBox):
    # A group which aligns its child boxes horizontaly. 
    is_group = True
    def create_group(self, l):
        return HGroup(l, device=self.device)



class VGroup(VBox):
    # A group which aligns its child boxes vertically. 
    is_group = True
    def create_group(self, l):
        return VGroup(l, device=self.device)


def replace_boxes(box, i1, i2, stuff):
    # Recursively replace everything between $i1$ and $i2$ by
    # $stuff$. Insertion is done at the depth of the first box which
    # starts at $i1$.
    #print "replace_boxes: (i1, i2)=", (i1, i2), "box=", repr(box)[:20]
    if box.is_group:
        l = []
        for j1, j2, child in box.iter_childs():
            if i1 <= j2 and j1 <= i2: # overlapping or neighbouring
                tmp = replace_boxes(child, max(0, i1-j1), min(j2, i2)-j1, stuff)
                l.extend(tmp)
                stuff = []
            else:
                l.append(child)
        l.extend(stuff)
        return box.from_childs(l)
    if i1 == i2:
        if i1 == 0:
            return list(stuff)+[box]
        elif i1 == len(box):
            return [box]+list(stuff)
    if i1<=0 and i2>=len(box):
        return stuff

    l = []
    for j1, j2, child in box.iter_childs():
        if i1 <= j2 and j1 <= i2: # overlapping or neighbouring
            tmp = replace_boxes(child, max(0, i1-j1), min(j2, i2)-j1, stuff)
            l.extend(tmp)
            stuff = []
        else:
            l.append(child)
    l.extend(stuff)
    return box.from_childs(l)


def tree_depth(box):
    # For debugging
    if not box.is_group:
        return 0
    l = [tree_depth(child) for child in box.childs]
    if not l:
        return 1
    return max(l)+1
    

def get_text(box): 
    # Extract text from boxes (for debugging).
    if isinstance(box, _TextBoxBase):
        return box.text
    l = []
    last = 0
    for i1, i2, child in box.iter_childs():
        if i1>last:
            l.append('.'*(i1-last))
        l.append(get_text(child))
        last = i2
    i1 = len(box)
    if i1>last:
        l.append('.'*(i1-last))
    return u''.join(l)


def check_box(box, texel=None):

    # Box must return infos for all index postions
    for i in range(len(box)+1):
        assert len(box.get_info(i, 0, 0)) == 4

    try:
        box.get_info(-1, 0, 0)
        assert False
    except IndexError:
        pass

    try:
        box.get_info(len(box)+1, 0, 0)
        assert False
    except IndexError:
        pass

    if texel is None:
        return True

    if 0:
        # All index positions which can be selected must be copyable
        for i in range(len(box)):
            j1, j2 = box.extend_range(i, i+1)
            rest, part = texel.takeout(j1, j2)
            assert calc_length(part) == j2-j1
            assert calc_length(rest)+calc_length(part) == len(texel)

        for i in range(len(box)):
            if i+2>len(box):
                continue
            j1, j2 = box.extend_range(i, i+2)        
            rest, part = texel.takeout(j1, j2)
            assert calc_length(part) == j2-j1
            assert calc_length(rest)+calc_length(part) == len(texel)

    return True        
    

def _create_testobjects(s):
    from ..textmodel.textmodel import TextModel
    texel = TextModel(s).texel    
    box = TextBox(s)
    return box, texel

def test_00():
    "TextBox"
    box, texel = _create_testobjects("0123456789")
    assert check_box(box, texel)

def test_01():
    "HBox"
    box1, tmp = _create_testobjects("01234")
    box2, tmp = _create_testobjects("56789")
    tmp, texel = _create_testobjects("0123456789")
    box = HBox([box1, box2])
    assert check_box(box, texel)

def test_02():
    "VBox"
    box1, tmp = _create_testobjects("01234")
    box2, tmp = _create_testobjects("56789")
    tmp, texel = _create_testobjects("0123456789")
    box = VBox([box1, box2])
    assert check_box(box, texel)

def test_03():
    "grouped"
    box, tmp = _create_testobjects("01234")
    b = grouped([box]*20)
    #b.dump_boxes(0, 0, 0)
    assert tree_depth(b) == 2
    assert len(b) == 20*len(box)
    b = grouped([box]*10)
    assert tree_depth(b) == 1
    b = grouped([box])
    assert tree_depth(b) == 0

def test_04():
    "replace_boxes"

    def get_alltext(l):
        return ''.join(get_text(box) for box in l)

    t1 = TextBox('0123456789')
    t2 = TextBox('abcdefghij')
    t3 = TextBox('xyz')
    assert str(replace_boxes(t1, 0, 10, [t2])) == "[TB('abcdefghij')]"
    l = replace_boxes(t1, 0, 0, [t2])
    assert get_alltext(l) == 'abcdefghij0123456789'

    l = replace_boxes(t1, 10, 10, [t2])
    assert get_alltext(l) == '0123456789abcdefghij'

    g = VGroup([t1, t2])
    assert get_text(g) == '0123456789abcdefghij'

    l = replace_boxes(g, 0, 20, [t3])
    assert get_alltext(l) == 'xyz'
    
    l = replace_boxes(g, 0, 10, [t3])
    assert get_alltext(l) == 'xyzabcdefghij'

    l = replace_boxes(g, 10, 20, [t3])
    assert get_alltext(l) == '0123456789xyz'

    l = replace_boxes(g, 10, 10, [t3])
    assert get_alltext(l) == '0123456789xyzabcdefghij'

    l = replace_boxes(g, 20, 20, [t3])
    assert get_alltext(l) == '0123456789abcdefghijxyz'

    l = replace_boxes(g, 0, 0, [t3])
    assert get_alltext(l) == 'xyz0123456789abcdefghij'

    g2 = VGroup([])
    assert get_text(g2) == ''
    l = replace_boxes(g2, 0, 0, [t3])
    assert get_alltext(l) == 'xyz'



