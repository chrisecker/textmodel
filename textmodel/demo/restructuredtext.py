import sys
sys.path.insert(0, '..')

from textmodel import TextModel
from textmodel.texeltree import Texel, T, TAB, NL, EndMark, Container, dump, get_text, NewLine
from textmodel.styles import create_style



class MyTextModel(TextModel):
    defaultstyle = create_style(bold=False, italics=False)



def print_rst(text):
    # A very simple printer for restructured text
    def get_pieces(obj):
        if obj.is_group:
            r = []
            for child in obj.childs:
                r.extend(get_pieces(child))
            return r
        return [obj]

    
    last = None
    r = []
    for texel in get_pieces(text.get_xtexel()):
        style = texel.style
        if not isinstance(texel, NewLine):
            if last:
                if last['bold'] != style['bold']:
                    r.append('**')
                if last['italics'] != style['italics']:
                    r.append('*')
        else:
            if last:
                if last['bold']:
                    r.append('**')
                if last['italics']:
                    r.append('*')
            listlevel = texel.parstyle.get('listlevel')
            if listlevel:
                # insert tabs and bullet
                i = len(r)-1
                while i>=0:
                    if r[i] == '\n':
                        break
                    i -= 1
                r.insert(i+1, ('  '*listlevel)+'- ')
        if not isinstance(texel, EndMark):
            r.append(texel.text)
        last = style
    print ''.join(r)


T = MyTextModel

bullet = T('\n')
bullet.texel.parstyle = create_style(listlevel=1)

text = T()
text += T("Wonderful world of textmodel:\n")
i1 = len(text)
text += T("We can do ")
text += T("italics", italics=True)
text += T('\n')
text.append_text("We can do ")
text += T("bold", bold=True)
text += T('\n')
text.set_parproperties(i1, len(text), listlevel=1)
i1 = len(text)
text += T('Here are two \nsub \nitems\n')
text.set_parproperties(i1, len(text), listlevel=1)
text.set_parproperties(i1+15, len(text), listlevel=2)


print_rst(text)
dump(text.texel)        
