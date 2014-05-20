# -*- coding: latin-1 -*-


class Texel:
    # Ein Texel ist ein TEXt-ELement. Texel m�ssen nicht von der
    # Basisklasse "Texel" abgeleitet werden. Sie m�ssen aber das
    # Texel-Protokoll vollst�ndig implementieren.
    def __len__(self):
        pass

    def get_style(self, i):
        return {}

    def get_text(self):
        return ' '

    def simplify(self, i):
        return self

    def get_styles(self, i1, i2):
        return []

    def set_styles(self, i, styles):
        # Styles ist eine Liste [(n1, s1), (n2, s2), ... ], wobei n
        # jeweils eine L�nge und s ein Style ist. Der Index i gibt
        # die Position, ab der die Styles angewendet werden.
        pass

    def set_properties(self, i1, i2, properties):
        # Properties ist ein Dict, z.B. {'fontsize':16, 'bgcolor':'red'}
        pass

    def takeout(self, i1, i2):
        pass

    def insert(self, i, texel):
        pass

    def split(self, i):
        pass

    def get_linelengths(self):
        # Die Zeilenl�ngen werden benutzt, um zwischen Indexposition
        # und Spalten- und Zeilennummern umzurechnen.  Ein Texel, das
        # aus zwei NewLines besteht sollte beispielsweise [1, 1]
        # zur�ckliefern.
        return []

    def dump(self, i=0):
        pass
    


def check(texel):
    # F�hrt diverse Tests durch. Insbesondere wird gepr�ft, ob das
    # Texel-Protokoll korrekt und vollst�ndig implementiert ist.
    
    # 1. Sind alle n�tigen Methoden implementiert?
    for name in dir(Texel):
        if name.startswith('__') and name != '__len__':
            continue
        getattr(texel, name) # wenn eine Methode nicht implementiert
                             # ist, dann gibt s hier einen AttributError
    return True


def checked(texel):
    # Praktische Funktion. Man kann damit "return checked(texel)"
    # schreiben.
    assert check(texel)
    return texel


def check_split(texel):
    for i in range(len(texel)+1):
        a, b = texel.split(i)
        assert len(texel) == len(a)+len(b)
    try:
        texel.split(-1)
        assert False
    except IndexError:
        pass
    try:
        texel.split(len(texel)+1)
        assert False
    except IndexError:
        pass
    return True


