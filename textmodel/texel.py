# -*- coding: latin-1 -*-


class Texel:
    # Ein Texel ist ein TEXt-ELement. Texel müssen nicht von der
    # Basisklasse "Texel" abgeleitet werden. Sie müssen aber das
    # Texel-Protokoll vollständig implementieren.
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
        # jeweils eine Länge und s ein Style ist. Der Index i gibt
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
        # Die Zeilenlängen werden benutzt, um zwischen Indexposition
        # und Spalten- und Zeilennummern umzurechnen.  Ein Texel, das
        # aus zwei NewLines besteht sollte beispielsweise [1, 1]
        # zurückliefern.
        return []

    def dump(self, i=0):
        pass
    


def check(texel):
    # Führt diverse Tests durch. Insbesondere wird geprüft, ob das
    # Texel-Protokoll korrekt und vollständig implementiert ist.
    
    # 1. Sind alle nötigen Methoden implementiert?
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


