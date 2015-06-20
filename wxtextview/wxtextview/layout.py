# -*- coding: latin-1 -*-


from textmodel import listtools
from textmodel.textmodel import TextModel
from textmodel.texeltree import NewLine, Group, Characters, defaultstyle
from textmodel import treebase
from .testdevice import TESTDEVICE
from rect import Rect
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


class Box:
    # Box protocol. Boxes are boxes when they implement the box
    # protocol. They do not have to be derived from Box.
    width = 0
    height = 0
    depth = 0
    length = 0
    device = TESTDEVICE                     
    def dump_boxes(self, i, x, y, indent=0):
        print " "*indent, "[%i:%i]" % (i, i+len(self)), x, y, 
        print repr(self)[:100]
        
    def __len__(self):
        return self.length

    def extend_range(self, i1, i2):
        return i1, i2

    def responding_child(self, i, x0, y0):
        # Finds the child which is responsible for index position
        # i. Returns a tuple: child, j1, x1, y1. Child is either the
        # responsible child or None, j1 is the childs indexposition
        # relative to i, x1 and y1 are the absolute positions of the
        # child box.
        if i<0 or i>len(self):
            raise IndexError, i
        # Default: signal that there is no responding child
        return None, i, x0, y0

    def draw(self, x, y, dc, styler):
        raise NotImplementedError()

    def draw_selection(self, i1, i2, x, y, dc):
        raise NotImplementedError()

    def draw_cursor(self, i, x0, y0, dc, style):
        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is not None:
            child.draw_cursor(i-j, x1, y1, dc, style)
        else:
            r = self.get_cursorrect(i, x0, y0, style)
            self.device.invert_rect(r.x1, r.y1, r.x2-r.x1, r.y2-r.y1, dc)

    def get_rect(self, i, x0, y0):
        # Returns the rectangle occupied by the Glyph at position i in
        # absolute coordinates.
        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is None:
            w, h = self.device.measure('M', defaultstyle)
            if i == len(self):
                x1 += self.width # rechts neben die Box
            return Rect(x1, y1+self.height, x1+w, y1+self.height-h)
        return child.get_rect(i-j, x1, y1)

    def get_cursorrect(self, i, x0, y0, style):
        # Returns the BBox around the cursor at index position i. Is
        # used by draw_cursor.
        child, j, x, y = self.responding_child(i, x0, y0)
        if child is not None:
            return child.get_cursorrect(i-j, x, y, style)
        else:
            x1, y1, x2, y2 = self.get_rect(i, x0, y0).items()
            return Rect(x1, y1, x1+2, y2)

    def get_index(self, x, y):
        # Returns the index which is closest to point (x, y). A return
        # value of None means: no matching index position found!
        return None

    def get_info(self, i, x0, y0):
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
    def __repr__(self):
        return "TB(%s)" % repr(self.text)

    def update(self):
        self.width, h = self.measure(self.text)
        self.height = int(ceil(h))
        self.length = len(self.text)

    def measure(self, text):
        return self.device.measure(text, self.style)

    def measure_parts(self, text):
        return self.device.measure_parts(text, self.style)

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
        return self.length



class TextBox(_TextBoxBase):
    def __init__(self, text, style=defaultstyle, device=None):
        self.text = text
        self.style = style
        if device is not None:
            self.device = device
        self.update()


class NewlineBox(_TextBoxBase):
    # Die NewlineBox ist eigentlich unnötig, die Position könnte
    # genausogut leer bleiben. Wir verwenden Sie trotzdem, da wir hier
    # sehr praktisch die Font-Information für das nachfolgende Zeichen
    # ablegen können.
    text = '\n'
    width = 0
    length = 1
    def __init__(self, style=defaultstyle, device=None):        
        self.style = style
        if device is not None:
            self.device = device
        self.update()

    def update(self):
        w, h = self.measure(self.text)
        self.height = int(ceil(h))

    def __repr__(self):
        return 'NL'

    def get_index(self, x, y):
        # Die TextBox würde den Index 1 zurückgeben, wenn x>0 ist. Das
        # macht aber keinen Sinn, da nach einem NL eine neue Zeile
        # angefangen wird. Die letzte Position einer Zeile ist gerade
        # der Index des NL-Zeichens, also 0.
        return 0
    

class TabulatorBox(_TextBoxBase):
    text = ' ' # XXX for now we treat tabs like spaces
    length = 1
    def __init__(self, style=defaultstyle, device=None):        
        self.style = style
        if device is not None:
            self.device = device
        self.update()

    def __repr__(self):
        return 'TAB'



class EndBox(_TextBoxBase):
    text = chr(27)
    width = 0
    length = 1
    def __init__(self, style=defaultstyle, device=None):
        self.style = style
        if device is not None:
            self.device = device
        self.update()

    def __repr__(self):
        return 'ENDMARK'

    def update(self):
        w, h = self.measure(self.text)
        self.height = int(ceil(h))


class EmptyTextBox(_TextBoxBase):
    text = ""
    width = 0
    length = 0
    def __init__(self, style=defaultstyle, device=None):
        self.style = style
        if device is not None:
            self.device = device
        self.update()

    def update(self):
        w, h = self.measure('M')
        self.height = int(ceil(h))

    def __repr__(self):
        return 'ETB'




class IterBox(Box):
    # IterBox provides default implementations for many box
    # methods. Derived classes need to define an "iter"-method. Note
    # that childs do not have to ly densely packed in the index
    # space. Single gaps between childs are allowed.

    def dump_boxes(self, i, x, y, indent=0):
        Box.dump_boxes(self, i, x, y, indent)
        for j1, j2, x1, y1, child in self.iter(i, x, y):
            child.dump_boxes(j1, x1, y1, indent+4)
        
    def iter(self, i, x, y):
        raise NotImplementedError()

    def riter(self, i, x, y):
        return reversed(tuple(self.iter(i, x, y)))

    def extend_range(self, i1, i2):
        for j1, j2, x1, y1, child in self.iter(0, 0, 0):
            if i1 < j2 and j1 < i2:
                k1, k2 = child.extend_range(i1-j1, i2-j1)
                i1 = min(i1, k1+j1)
                i2 = max(i2, k2+j1)
        return i1, i2

    def responding_child(self, i, x0, y0):
        if i<0 or i>len(self):
            raise IndexError, i
        j1 = None # Markierung
        for j1, j2, x1, y1, child in self.riter(0, x0, y0):
            if j1 < i <= j2:
                return child, j1, x1, y1
            elif j1 == i and child.can_leftappend():
                return child, j1, x1, y1
        if i == 0:
            return None, i, x0, y0
        if j1 is None: # keine Kinder
            return None, i, x0, y0
        if i == len(self): # empty last
            return None, i, x0, y0
        # Only single index positions between child elements can be
        # empty. If two or more consecutive postions were empty, this
        # would mean that then we would have at least one position
        # without a responsible element.
        print tuple(self.riter(0, x0, y0))
        print j1, j2, i, child, child.can_leftappend()
        raise Exception, (self, i, len(self))

    def get_index(self, x, y):

        # First run: only boxes which directly contain (x, y)
        l = []
        for j1, j2, x1, y1, child in self.riter(0, 0, 0):
            if x1 <= x <= x1+child.width and \
                    y1 <= y <= y1+child.height+child.height:
                i = child.get_index(x-x1, y-y1)
                if i is not None:
                    r = child.get_rect(i, x1, y1)
                    dist = r.dist(x, y)
                    l.append((dist, -j1-i))
        if l:
            l.sort() # NOTE: this favors higher index positions!
            assert -l[0][-1] <= len(self)
            return -l[0][-1]
        
        # Second run: other boxes. NOTE: the full search is general
        # but is very inefficient! Derived Boxes there should
        # implement faster version if possible.
        for j1, j2, x1, y1, child in self.riter(0, 0, 0):
            if x1 <= x <= x1+child.width and \
                    y1 <= y <= y1+child.height+child.depth:
                pass
            else:
                if l: # Versuch einer Optimierung
                    if Rect(x1, y1, x1+child.width, 
                            y1+child.height+child.depth)\
                            .adist(x, y) > min(l)[0]:
                        continue
                i = child.get_index(x-x1, y-y1)
                if i is not None:
                    dist = child.get_rect(i, x1, y1).adist(x, y)
                    l.append((dist, -j1-i))
        if l:
            l.sort()
            assert -l[0][-1] <= len(self) # XXXX
            return -l[0][-1]

        # No index position found
        return None

    def draw(self, x, y, dc, styler):
        device = self.device
        for j1, j2, x1, y1, child in self.iter(0, x, y):
            r = Rect(x1, y1, x1+child.width, y1+child.height)
            if device.intersects(dc, r):
                child.draw(x1, y1, dc, styler)

    def draw_selection(self, i1, i2, x, y, dc):
        device = self.device
        for j1, j2, x1, y1, child in self.iter(0, x, y):
            if i1 < j2 and j1< i2:
                r = Rect(x1, y1, x1+child.width, y1+child.height)
                if device.intersects(dc, r):
                    child.draw_selection(i1-j1, i2-j1, x1, y1, dc)

    def layout(self):
        # This is a very general and slow implementation. Should be
        # reimplemented in derived classes.
        w0 = w1 = h0 = h1 = h2 = 0
        for j1, j2, x, y, child in self.iter(0, 0, 0):
            w0 = min(w0, x)
            h0 = min(h0, y)
            w1 = max(w1, x+child.width)
            h1 = max(h1, y+child.height)
            h2 = max(h2, y+child.height+child.depth)
        self.width = w1
        self.height = h1
        self.depth = h2-h1
        # h0 and w0 describe the overlapp to the left and to the right
        # respectively. They might be useful in derived classes. We
        # therefore return them.
        return w0, h0


def extend_range_seperated(iterbox, i1, i2):
    # Restrict ranges to child boundaries, e.g. in the fraction it
    # should not be possible to select a part of the nominator and a
    # part of the denominator. 
    last = 0
    for j1, j2, x, y, child in iterbox.iter(0, 0, 0):
        if not (i1<j2 and j1<i2):
            continue
        if i1 < j1 or i2>j2:
            return min(i1, 0), max(i2, len(iterbox))
        k1, k2 = child.extend_range(i1-j1, i2-j1)
        return min(i1, k1+j1), max(i2, k2+j1)
    return i1, i2




class ChildBox(IterBox):
    def __init__(self, childs, device=None):
        self.childs = tuple(childs)
        if device is not None:
            self.device = device
        self.length = listtools.calc_length(self.childs)
        self.layout()

    def __repr__(self):
        return self.__class__.__name__+repr(list(self.childs))



class HBox(ChildBox):
    # A box which aligns its child boxes horizontaly. 

    def iter(self, i, x, y):
        height = self.height
        j1 = i
        for child in self.childs:
            j2 = j1+child.length
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




class VBox(ChildBox):
    # A box which aligns its child boxes vertically. 

    def iter(self, i, x, y):
        j1 = i
        for child in self.childs:
            j2 = j1+child.length
            yield j1, j2, x, y, child
            y += child.height+child.depth
            j1 = j2



class Row(HBox):
    pass


class _ParagraphBox(IterBox):
    # The number of paragraphs can be very long. Therefore we store
    # all paragraphs in a tree structure. This makes the GUI
    # considerably faster.

    def __init__(self, device):
        if device is not None:
            self.device = device
        self.layout()

    @property
    def length(self):
        return self.weights[1]

    def create_group(self, l):
        return ParagraphStack(l, device=self.device)

    def iter(self, i, x, y):
        j1 = i
        for child in self.childs:
            j2 = j1+child.length
            yield j1, j2, x, y, child
            y += child.height+child.depth
            j1 = j2

    def __repr__(self):
        return self.__class__.__name__+repr(list(self.childs))


class Paragraph(_ParagraphBox, treebase.Element):
    # A paragraph holds one line of text which is ended by a
    # newline. The paragraph is broken into one or several rows.

    def __init__(self, rows, device=None):
        length = listtools.calc_length(rows)
        self.weights = (0, length)
        self.childs = rows
        _ParagraphBox.__init__(self, device)

    def get_envelope(self, i1, i2):
        return 0, self.length

    def takeout(self, i1, i2):
        if i1 == i2:
            return [self], []
        assert i1 == 0
        assert i2 == self.length
        return [], [self]




class ParagraphStack(_ParagraphBox, treebase.Group):

    def __init__(self, paragraphs, device=None):
        treebase.Group.__init__(self, paragraphs)
        _ParagraphBox.__init__(self, device)

    def get_interval(self, i, i0=0):
        # Returns the interval of the paragraph which is adressed by
        # index $i$
        for j1, j2, child in self.iter_childs():
            if j1 < i <= j2:
                if isinstance(child, ParagraphStack):
                    return child.get_interval(i-j1, i0+j1)
                return j1+i0, j2+i0
        return i+i0, i+i0

    def get_index(self, x, y):
        # This replaces the inefficient default method from IterBox.   
        l = []
        for j1, j2, x1, y1, child in self.riter(0, 0, 0):
            if y1 <= y <= y1+child.height+child.depth:
                i = child.get_index(x-x1, y-y1)
                if i is not None:
                    return i+j1

    ### Methods needed by the updater
    def get_envelope(self, i1, i2):  
        # Returns the interval in which paragraph boxes have to be
        # updated if content between $i1$ and $i2$ is changed.
        j1 = self.get_interval(i1)[0]
        tmp = self.get_interval(i2)[1]
        if tmp == len(self):
            j2 = len(self)
        else:
            assert tmp < len(self)
            j2 = self.get_interval(tmp+1)[1]
        return j1, j2




        
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

    # All index positions which can be selected must be copyable
    calc_length = listtools.calc_length
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
    from textmodel.textmodel import TextModel
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
    "Paragraph"
    box1, tmp = _create_testobjects("0123")
    box2, tmp = _create_testobjects("5678")
    tmp, texel = _create_testobjects("0123\n5678\n")
    box = Paragraph([
        Row([box1, NewlineBox()]), 
        Row([box2, NewlineBox()]),
        Row([EmptyTextBox()])
    ])
    assert check_box(box, texel)
    #box.dump_boxes(0, 0, 0)
    assert (box.height, box.width, box.depth) == (3, 4, 0)

    assert str(box.get_info(0, 0, 0)) == "(TB('0123'), 0, 0, 0)"
    assert str(box.get_info(1, 0, 0)) == "(TB('0123'), 1, 1, 0)"
    assert str(box.get_info(2, 0, 0)) == "(TB('0123'), 2, 2, 0)"
    assert str(box.get_info(3, 0, 0)) == "(TB('0123'), 3, 3, 0)"
    assert str(box.get_info(4, 0, 0)) == "(NL, 0, 4, 0)"
    assert str(box.get_info(5, 0, 0)) == "(TB('5678'), 0, 0, 1)"
    assert str(box.get_info(6, 0, 0)) == "(TB('5678'), 1, 1, 1)"
    assert str(box.get_info(7, 0, 0)) == "(TB('5678'), 2, 2, 1)"
    assert str(box.get_info(8, 0, 0)) == "(TB('5678'), 3, 3, 1)"
    assert str(box.get_info(9, 0, 0)) == "(NL, 0, 4, 1)"
    assert str(box.get_info(10, 0, 0)) == "(ETB, 0, 0, 2)"


def test_04():
    "ParagraphStack"
    box1, tmp = _create_testobjects("0123")
    box2, tmp = _create_testobjects("5678")
    tmp, texel1 = _create_testobjects("0123\n")
    tmp, texel2 = _create_testobjects("5678\n")
    tmp, texel = _create_testobjects("0123\n5678\n")
    p1 = Paragraph([
        Row([box1, NewlineBox()]), 
    ])
    p2 = Paragraph([
        Row([box2, NewlineBox()]), 
        Row([EmptyTextBox()])
    ])
    assert check_box(p1, texel1)
    assert check_box(p2, texel2)
    box = ParagraphStack([p1, p2])
    assert check_box(box, texel)

    assert str(box.get_info(0, 0, 0)) == "(TB('0123'), 0, 0, 0)"
    assert str(box.get_info(1, 0, 0)) == "(TB('0123'), 1, 1, 0)"
    assert str(box.get_info(2, 0, 0)) == "(TB('0123'), 2, 2, 0)"
    assert str(box.get_info(3, 0, 0)) == "(TB('0123'), 3, 3, 0)"
    assert str(box.get_info(4, 0, 0)) == "(NL, 0, 4, 0)"
    assert str(box.get_info(5, 0, 0)) == "(TB('5678'), 0, 0, 1)"
    assert str(box.get_info(6, 0, 0)) == "(TB('5678'), 1, 1, 1)"
    assert str(box.get_info(7, 0, 0)) == "(TB('5678'), 2, 2, 1)"
    assert str(box.get_info(8, 0, 0)) == "(TB('5678'), 3, 3, 1)"
    assert str(box.get_info(9, 0, 0)) == "(NL, 0, 4, 1)"
    assert str(box.get_info(10, 0, 0)) == "(ETB, 0, 0, 2)"


def test_05():
    t1 = TextBox("0123456789")
    t2 = TextBox("0123456789")
    p1 = Paragraph([Row([t1, NewlineBox(defaultstyle)])])
    row = p1.childs[0]
    assert p1.height == 1
    assert p1.width == 10
    assert p1.length == 11
    p2 = Paragraph([Row([t2])])
    assert p2.height == 1
    s = ParagraphStack([p1, p2])
    assert s.height == 2    


def test_06():
    # Problem: get_rect always returns 0, 0
    t1 = TextBox("0123456789")
    t2 = TextBox("0123456789")
    p1 = Paragraph([Row([t1, t2, NewlineBox(defaultstyle)])])

    assert p1.get_rect(0, 0, 0) == Rect(0, 0.0, 1, 1.0)
    assert p1.get_rect(10, 0, 0) == Rect(10, 0.0, 11, 1.0)



if __name__ == '__main__':
    from textmodel import alltests
    alltests.dotests()
