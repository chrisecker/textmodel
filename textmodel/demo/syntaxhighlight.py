"""This model colorizes python source code and prints it to the
stdout. If you terminal understands ANSI escape codes you will see the
source code in colors.

The code is ment as an example only. It is not the fastest way to
colorize text.

Note: If you use a pager, you should pass it the -R parameter:
$ python syntaxhighlight.py|less -R

"""

import sys
sys.path.insert(0, '..')

import textmodel
from textmodel.textmodel import TextModel


CSI = "\x1B["
RESET = CSI+"m"


def pycolorize(rawtext, coding='latin-1'):
    import cStringIO
    rawtext+='\n'
    instream = cStringIO.StringIO(rawtext).readline

    import token, tokenize, keyword
    _KEYWORD = token.NT_OFFSET + 1
    _TEXT    = token.NT_OFFSET + 2

    _colors = {
        token.NUMBER:       CSI+'32m',
        token.OP:           CSI+'31m',
        token.STRING:       CSI+'33m',
        tokenize.COMMENT:   CSI+'33m',
        token.NAME:         CSI+'37m',
        token.ERRORTOKEN:   CSI+'30m',
        _KEYWORD:           CSI+'34m',
    }
    def tokeneater(toktype, toktext, (srow,scol), (erow,ecol), line):
        i1 = model.position2index(srow-1, scol)
        i2 = model.position2index(erow-1, ecol)
        if token.LPAR <= toktype and toktype <= token.OP:
            toktype = token.OP
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            toktype = _KEYWORD
        try:
            color = _colors[toktype]
        except:
            return
        model.set_properties(i1, i2, color=color)

    text = rawtext.decode(coding)
    model = TextModel(text)

    tokenize.tokenize(instream, tokeneater)
    return model.copy(0, len(model)-1)



def ansi_print(text):

    def ansi_text(texel):
        if texel.is_group:
            return ''.join([ansi_text(child) for child in texel.childs])
        if texel.style:
            return texel.style.get('color', '')+texel.text+RESET
        return texel.text
        
    print ansi_text(text.texel)




from textmodel import texeltree
filename = texeltree.__file__
if filename.lower().endswith('.pyc'):
    filename = filename[:-1]


rawtext = open(filename).read()
model = pycolorize(rawtext)

ansi_print(model)
#texeltree.dump(model.texel)









