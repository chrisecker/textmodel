# -*- coding: latin-1 -*-

# cerealizerformat.py
#
# A simple file format based on cerealizer. This is basically a secure
# form of pickling. Is meant to be used during development.

from . import nbtexels
from .textmodel import textmodel
from .textmodel import texeltree
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

def loads(s):
  return cerealizer.Dumper(magic).undump(StringIO(s))


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
    #print repr(s)
    model2 = loads(s)
    assert str(model1.texel) == str(model2.texel)

    try:
        model2 = loads('*'+s)
        assert False
    except cerealizer.NotCerealizerFileError:
        pass
