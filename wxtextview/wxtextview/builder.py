# -*- coding: latin-1 -*-


from ..textmodel import texeltree
from ..textmodel.textmodel import TextModel
from ..textmodel.texeltree import NewLine, Group, Text, length
from .testdevice import TESTDEVICE
from .boxes import TextBox, NewlineBox, TabulatorBox, EmptyTextBox, \
    EndBox, check_box, Box, calc_length



class Factory:
    TextBox = TextBox
    NewlineBox = NewlineBox
    TabulatorBox = TabulatorBox
    EndBox = EndBox

    def __init__(self, device=TESTDEVICE):
        self.device = device

    def get_device(self):
        return self.device

    ### Factory methods
    def create_all(self, texel):
        # Convenience method
        return self.create_boxes(texel, 0, length(texel))

    def create_boxes(self, texel, i1, i2):
        assert i1>=0
        assert i2<=length(texel)
        assert i1<=i2
        if i1 == i2:
            return () # XXX Why is this needed?
        name = texel.__class__.__name__+'_handler'
        handler = getattr(self, name)
        #print "calling handler", name, i1, i2
        l = handler(texel, i1, i2)
        try:
            assert calc_length(l) == i2-i1
        except:
            print "handler=", handler
            raise
        return tuple(l)
        
    def Group_handler(self, texel, i1, i2):
        r = []
        for j1, j2, child in texeltree.iter_childs(texel):
            if i1 < j2 and j1 < i2: # overlapp
                r.extend(self.create_boxes(
                    child, max(0, i1-j1), min(i2, j2)-j1))
        return r

    def Text_handler(self, texel, i1, i2):
        return [self.TextBox(texel.text[i1:i2], texel.style, self.device)]

    def NewLine_handler(self, texel, i1, i2):
        if texel.is_endmark:
            return [self.EndBox(texel.style, self.device)]
        return [self.NewlineBox(texel.style, self.device)] # XXX: Hmmmm

    def Tabulator_handler(self, texel, i1, i2):
        return [self.TabulatorBox(texel.style, self.device)]





class BuilderBase:
    """The builder is responsible for creating and updating the layout. 

    The methods build, insert, remove and update return a tree of boxes (=
    "layout").

    The length of the box tree is always the length of the model +1,
    because we add a special box ("end mark").

    """

    _layout = None

    def rebuild(self):
        # sets self._layout
        pass

    def get_layout(self):
        assert self._layout is not None
        return self._layout

    ### Signal handlers
    def properties_changed(self, i1, i2):
        pass

    def inserted(self, i, n):
        pass

    def removed(self, i, n):
        pass



def test_01():
    factory = Factory()
    boxes = factory.create_all(TextModel("123").texel)
    assert calc_length(boxes) == 3
    boxes = factory.create_all(TextModel("123\n567").get_xtexel())
    assert calc_length(boxes) == 8

    


