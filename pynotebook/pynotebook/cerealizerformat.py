# -*- coding: latin-1 -*-

# cerealizerformat.py
#
# A simple file format based on cerealizer. This is basically a secure
# form of pickling. Is meant to be used during development.

from . import nbtexels
from .textmodel import textmodel
from .textmodel import texeltree, styles
from .nbtexels import mk_textmodel

from . import cerealizer
from StringIO import StringIO


magic = 'pynotebook0'

def register(Class, handler=None, classname = None):
    # By default we want to register a class by its short name,
    # however in cerealizer the default is the full name (module +
    # name). I prefer the short name, because classes may be moved to
    # other modules during development.
    if classname is None:
        classname = Class.__name__
    cerealizer.register(Class, handler, classname)



def dumps(obj):
    s = StringIO()
    cerealizer.Dumper(magic).dump(obj, s)
    return s.getvalue()


def _replace_styles(texel, table):
    if texel.is_group or texel.is_container:
        for child in texel.childs:
            _replace_styles(child, table)
    else:
        if 'style' in texel.__dict__:
            sid = id(texel.style)
            if not sid in table:
                table[sid] = styles.create_style(**texel.style)
            texel.style = table[sid]
        if isinstance(texel, texeltree.NewLine) and 'parstyle' in texel.__dict__:
            sid = id(texel.parstyle)
            if not sid in table:
                table[sid] = texel.parstyle = styles.create_style(**texel.parstyle)
            texel.parstyle = table[sid]

def loads(s):
    model =  cerealizer.Dumper(magic).undump(StringIO(s))
    _replace_styles(model.texel, {})
    return model


register(texeltree.Group)
register(texeltree.Text)
register(texeltree.Container)
register(texeltree.NewLine)
register(texeltree.Tabulator)

register(textmodel.TextModel)

register(nbtexels.TextCell)
register(nbtexels.ScriptingCell)
register(nbtexels.BitmapRGB)
register(nbtexels.BitmapRGBA)


def test_00():
    model1 = textmodel.TextModel()
    tmp = textmodel.TextModel(u'for a in range(5):\n    print a')
    cell = nbtexels.ScriptingCell(tmp.texel, texeltree.NULL_TEXEL)
    model1.insert(len(model1), mk_textmodel(cell))

    s = dumps(model1)
    model2 = loads(s)
    assert str(model1.texel) == str(model2.texel)
    assert model1.get_style(5) is model2.get_style(5)
    assert model1.get_parstyle(5) is model2.get_parstyle(5)
    try:
        model2 = loads('*'+s)
        assert False
    except cerealizer.NotCerealizerFileError:
        pass
