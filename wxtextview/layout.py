# -*- coding: latin-1 -*-

# Der bisherige Ansatz lässt sich kaum testen. Hier wird versucht den
# Boxenbaum besser zugänglich zu gestalten.
#
# Wichtige Grundsätze:
# - Der Boxenbaum lässt sich auch ohne Modell erstellen
# - Es gibt eine Factory-Instanz, die alle einfachen Boxen erzeugt
# - Boxen sind Einweg-Artikel, sie werden nicht modifiziert sondern neu erzeugt
# - Backends überschreiben Factory-Moethoden um modifizierte Boxen zu erzeugen
# - Keine Empties
# - Ein Texel muss über alle Indizes (0 bis n) Auskunft geben können
# - Das übergeordnete Texel ist dafür verantwortlich, dass nur sinnvolle Anfragen 
#   gestellt werden. Beispielsweise sollte ein abgeschlossener Paragraf nicht 
#   über die Position n Auskunft geben
#
# Backends lassen sich auf 2 Arten implementieren: (a) durch Anpassen
# der Factory, sodass sie spezielle Boxen für das Backend erzeugt
# (b) durch definieren einer Device, die von den Boxen verwendet
# wird.
#
# Das Definieren einer Device ist besonders einfach aber nicht ganz so
# effizient. Es eigent sich daher besonders zum Testen.
#
# Damit löse ich das Enwicklerdilemma: es ist möglich einfache
# Backends in der Entwicklungsphase einzubauen, es ist aber trotzdem
# möglich später optimierte Varianten zu benutzen.


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '..')

from textmodel import listtools
from textmodel import TextModel, NewLine, Group, Characters, defaultstyle
from testdevice import TESTDEVICE
from rect import Rect
from math import ceil




class Box:
    width = 0
    height = 0
    depth = 0
    length = 0
    is_dummy = False # Dummy-Boxen werden teilweise antelle von Lücken
                     # verwendet, was praktisch sein kann. Sie werden
                     # bei dem Iterieren ausgeblendet.
    device = TESTDEVICE

    def dump(self, i, x, y, indent=0):
        print " "*indent, i, i+len(self), x, y, self
        
    def __len__(self):
        return self.length

    def extend_range(self, i1, i2):
        return i1, i2

    def responding_child(self, i, x0, y0):
        # Sucht das für die Cursorposition i verantwortliche
        # Kind. Gibt ein Tupel zurück: child, j1, x1, y1 Dabei ist
        # Child das Kind oder None (wenn es kein passendes Kind gibt),
        # j1 ist die Indexposition des Kindes relativ zu i, x1 und y1
        # ist die absolute Position der Kindbox.
        if i<0 or i>len(self):
            raise IndexError, i
        # Defaultverhalten: es gibt kein passendes Kind
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
        # Gibt das Rect des Glyphs an Position i in absoluten
        # Koordinaten.
        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is None:
            w, h = self.device.measure('M', defaultstyle)
            if i == len(self):
                x1 += self.width # rechts neben die Box
            return Rect(x1, y1+self.height, x1+w, y1+self.height-h)
        return child.get_rect(i-j, x1, y1)

    def get_cursorrect(self, i, x0, y0, style):
        # Gibt die BBox um den Cursor an der Stelle i. Wird von
        # draw_cursor verwendet, außerdem von TextView um den Scroll
        # anzupassen.
        child, j, x, y = self.responding_child(i, x0, y0)
        if child is not None:
            return child.get_cursorrect(i-j, x, y, style)
        else:
            x1, y1, x2, y2 = self.get_rect(i, x0, y0).items()
            return Rect(x1, y1, x1+2, y2)

    def get_index(self, x, y):
        # Gibt die Indexposition, die zur Position (x, y) am nächsten
        # ist.  None bedeutet: Keine passende Indexposition gefunden!
        return None

    def get_info(self, i, x0, y0):
        # Gibt das für die Position i verantwortliche BoxObjekt, die
        # absolute Position im Indexraum und die absolute Position des
        # zu i gehörigen Rechtecks in der Zeichenfläche zurück.
        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is None:
            x, y = self.get_rect(i, x0, y0).items()[:2]
            return self, i, x, y
        return child.get_info(i-j, x1, y1)

    def find_box(self, i, x0, y0):
        # Momentan nicht verwendet, könnte aber praktisch sein. Sucht
        # die Box, die i verwaltet. Gibt die Box, die Position von i
        # innerhalb der Box und den Ursprung der Box in der
        # Zeichenfläche zurück.
        child, j, x1, y1 = self.responding_child(i, x0, y0)
        if child is None:
            return self, i, x0, y0
        return child.find_box(i-j, x1, y1)
        

    def can_leftappend(self):
        # Wenn zwei benachbarte Texel für das Einfüen infrage kommen,
        # dann wird normalerweise das rechte Texel bevorzugt. Für
        # manche Texel macht das allerdings keinen Sinn
        # (beispielsweise das Wurzelzeichen). Boxen dieser Texeln
        # können daher False zurückgeben und damit signalisieren, dass
        # das linke Texel das Einfügen übernehmen sollte.
        return True


    
class TextBox(Box):
    def __init__(self, text, style=defaultstyle, device=None):
        self.text = text
        self.style = style
        if device is not None:
            self.device = device
        self.update()

    def __repr__(self):
        return "TB(%s)" % repr(self.text)

    def update(self):
        self.width, h = self.measure(self.text)
        self.height = ceil(h)
        self.length = len(self.text)

    def measure(self, text):
        return self.device.measure(text, self.style)

    def measure_parts(self, text):
        return self.device.measure_parts(text, self.style)

    ### Box-Protokoll
    def get_info(self, i, x0, y0):
        i = max(0, i)
        i = min(len(self.text), i)
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

    ### Weitere Methoden
    def split(self, w):
        # Wird von Paragraph benutzt
        text = self.text
        parts = self.measure_parts(text)
        for i, part in enumerate(parts):
            if part > w:
                j = i
                b1 = self.__class__(text[:j], self.style)
                b2 = self.__class__(text[j:], self.style)
                if b1.width > w:
                    print "split:", repr(text[:j]), repr(text[j:])
                    print "parts =", parts
                    print b1.width
                    assert False
                assert b1.width <= w
                return b1, b2
        return self, self.__class__('', self.style)


class NewlineBox(TextBox):
    # Die NewlineBox ist eigentlich unnötig, die Position könnte
    # genausogut leer bleiben. Wir verwenden Sie trotzdem, da wir hier
    # sehr praktisch die Font-Information für das nachfolgende Zeichen
    # ablegen können.
    is_dummy = True
    def __init__(self, style, device=None):        
        TextBox.__init__(self, '\n', style, device)
        self.width = 0

    def __repr__(self):
        return 'NL'

    def get_index(self, x, y):
        # Die TextBox würde den Index 1 zurückgeben, wenn x>0 ist. Das
        # macht aber keinen Sinn, da nach einem NL eine neue Zeile
        # angefangen wird. Die letzte Position einer Zeile ist gerade
        # der Index des NL-Zeichens, also 0.
        return 0
    

class TabulatorBox(TextBox):
    def __init__(self, style, device=None):        
        TextBox.__init__(self, ' ', style, device)
        #self.width = 0

    def __repr__(self):
        return 'TAB'


class IterBox(Box):
    # Die Kinder brauchen nicht dicht in i zu liegen. Es können
    # einzelne Indizes frei bleiben.

    def dump(self, i, x, y, indent=0):
        print " "*indent, i, i+len(self), x, y, self
        for j1, j2, x1, y1, child in self.iter(i, x, y):
            child.dump(j1, x1, y1, indent+4)
        
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
        # Es darf maximal eine Indexposition zwischen zwei Kindern
        # frei bleiben. Damit ist sichergestellt, dass jede Position
        # verwaltet wird (zumindest wenn es Kinder gibt). Wenn wir an
        # diese Stelle kommen dann liegt also ein Fehler vor!
        print tuple(self.riter(0, x0, y0))
        print j1, j2, i, child, child.can_leftappend()
        raise Exception, (self, i, len(self))

    def get_index(self, x, y):
        # Sucht die zu (x,y) nächstgelegene Indexposition. Kann auch
        # None zurückgeben. 

        # 1. Durchlauf: nur Kindboxen die (x, y) enthalten
        l = []
        for j1, j2, x1, y1, child in self.riter(0, 0, 0):
            if x1 <= x <= x1+child.width and \
                    y1-child.depth <= y <= y1+child.height:
                i = child.get_index(x-x1, y-y1)
                if i is not None:
                    r = child.get_rect(i, x1, y1)
                    dist = r.dist(x, y)
                    l.append((dist, -j1-i))
        if l:
            l.sort() # Achtung: so werden große Indexposition bevorzugt!
            assert -l[0][-1] <= len(self)
            return -l[0][-1]
        
        # 2. Durchlauf: restlicher Kindboxen. ACHTUNG: die
        # vollständige Suche ist zwar allgemein, aber sehr
        # ineffizient! Die Methode get_index sollte daher wenn immer
        # möglich überschrieben werden.
        for j1, j2, x1, y1, child in self.riter(0, 0, 0):
            if x1 <= x <= x1+child.width and \
                    y1-child.depth <= y <= y1+child.height:
                pass
            else:
                if l: # Versuch einer Optimierung
                    if Rect(x1, y1, x1+child.width, y1+child.height)\
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

        # Keine Indexposition innerhalb eines Kinds gefunden!
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



class ChildBox(IterBox):
    def __init__(self, childs, device=None):
        self.childs = tuple(childs)
        if device is not None:
            self.device = device
        self.length = listtools.calc_length(self.childs)
        self.layout()

    def layout(self):
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
        # h0 und w0 beschreiben den Überstand nach links bzw. nach
        # oben. Die Werte können in abgeleiteten Klassen nützlich
        # sein, um den Ursprung festzulegen. Wir geben sie daher
        # zurück.
        return w0, h0

    def __repr__(self):
        return self.__class__.__name__+repr(list(self.childs))



class HBox(ChildBox):
    # Richtet seine Kinder in einer horizontalen Reihe aus. Childs ist
    # eine Liste mit Kindboxen. Boxen mit dem Flag is_dummy werden als
    # Lücken behandelt.

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
    # Stapelt die Kinderboxen übereinander. Childs ist eine Liste mit
    # Kindboxen. Boxen mit dem Flag is_dummy werden als Lücken
    # behandelt.

    def iter(self, i, x, y):
        j1 = i
        for child in self.childs:
            j2 = j1+child.length
            if not child.is_dummy:
                yield j1, j2, x, y, child
                y += child.height+child.depth
            j1 = j2

    def get_index(self, x, y):
        # Wir überschreiben die ineffiziente vollständige Suche. Das
        # ist wichtig, da VBox insbesondere als Basisklasse für
        # Paragraph dient und get_index gerade für längere Texte sehr
        # leicht ineffizient wird.
        l = []
        for j1, j2, x1, y1, child in self.riter(0, 0, 0):
            if y1-child.depth <= y <= y1+child.height:
                i = child.get_index(x-x1, y-y1)
                if i is not None:
                    return i+j1


class Row(HBox):
    pass


class Paragraph(VBox):
    # Ein Paragraph enthält eine Textzeile bis zu einem NewLine. Der
    # Paragraph wird in eine oder mehrere Zeilen (Rows) umgebrochen.
    #
    # Es wird zwischen abgeschlossenen und offenen
    # Paragraphenunterschieden. Ein Paragraph ist abgeschlossen, wenn
    # er mit einem NewLine endet.
    #
    # Ein Paragraph darf nur Kinder vom Typ Row enthalten. Bei einem
    # abgeschlossenen Paragraph muss das letzte Kind der letzten Reihe
    # eine NewLineBox sein.
    def __init__(self, rows, device=None):
        for row in rows:
            assert isinstance(row, Row)
        VBox.__init__(self, rows, device)

    def has_newline(self):
        return isinstance(self.childs[-1].childs[-1], NewlineBox) 

    def get_newlinebox(self):
        # Die Newlinebox wird von Paragraphstack verwenet, um die Höhe
        # des Cursorzeichens zu bestimmen.
        return self.childs[-1].childs[-1]



def simple_linewrap(textboxes, maxw, device=TESTDEVICE):
    # Einfacher Zeilenumbruch-Algorithmus
    rows = []
    l = []
    w = 0
    for box in textboxes:
        while w+box.width > maxw:
            # neue Reihe anfangen
            a, b = box.split(maxw-w)

            if a.length > 1:
                # Könnte gebrochen werden
                if not a.width <= maxw-w:
                    print "Wrong split:", repr(a.text)
                assert a.width <= maxw-w

            if a.length:
                l.append(a)
            box = b
            row = Row(l, device)
            if row.length>1:
                if row.width > maxw:
                    print "___"
                    for child in row.childs:
                        print child.width, child
                assert row.width <= maxw
            rows.append(row)
            l = []
            w = 0
        if box.length:
            l.append(box)
            w += box.width
            assert w <= maxw
    if l:
        row = Row(l, device)
        assert row.width <= maxw
        rows.append(row)
    return rows


class ParagraphStack(ChildBox):
    _maxw = 0
    def __init__(self, paragraphs, maxw=0, device=None):
        self._maxw = maxw
        ChildBox.__init__(self, paragraphs, device)

    def layout(self):
        # w, h, length bestimmen. Wir müssen hier evt. Platz für die
        # nächsten (noch leere) Zeile berücksichtigen. Das ist der
        # Fall, wenn der letzte Paragraphmit einem NL endet oder wenn
        # das Element Länge 0 hat.
        w = h = length = 0
        par = None
        for par in self.childs:
            length += par.length
            w = max(w, par.width)
            h = h+par.height+par.depth

        # Wenn der Text leer ist oder der letzte Paragraph mit einem
        # NL endet, dann brauchen wir zusätzlichen Platz für die
        # nächste Zeile.
        extra_h = 0
        if par is None:
            extra_h = defaultstyle['fontsize'] # XXX gibt es eine bessere Methode?
        elif par.has_newline():
            newlinebox = par.get_newlinebox()
            extra_h = newlinebox.height

        self.width = w
        self.height = h+extra_h
        self.length = length
        self.extra_height = extra_h
        
    def iter(self, i, x, y):
        j1 = i
        for child in self.childs:
            j2 = j1+child.length
            yield j1, j2, x, y, child
            y += child.height+child.depth
            j1 = j2

    def get_index(self, x, y):
        if y > self.height-self.extra_height:
            # Da die zusätzliche Zeile eigentlich nicht exisitiert,
            # wird sie von dem Algorithmus in ChildBox.get_index nicht
            # gefunden. Wir müssen das daher hier als Sonderfall
            # behandeln.
            return len(self)
        return ChildBox.get_index(self, x, y)

    def responding_child(self, i, x0, y0):
        # Die letzte Position verwalten wir direkt. 
        if i == len(self) and self.extra_height:
            return None, i, x0, y0
        return IterBox.responding_child(self, i, x0, y0)

    def get_rect(self, i, x0, y0):
        if i < self.length or not self.extra_height:
            return IterBox.get_rect(self, i, x0, y0)
        h = self.height
        return Rect(x0, y0+h-self.extra_height, x0+2, y0+h)

    def get_cursorrect(self, i, x0, y0, style):
        if i < self.length or not self.extra_height:
            return IterBox.get_cursorrect(self, i, x0, y0, style)
        return self.get_rect(i, x0, y0)

    ### Methoden für den Updater
    def replace(self, i1, i2, new_paragraphs):
        boxes = self.childs
        j1, j2 = self.get_envelope(i1, i2)
        assert i1 == j1 and i2 == j2 
        self.childs = listtools.replace(boxes, j1, j2, new_paragraphs)
        self.layout()

    def get_envelope(self, i1, i2):        
        j1, j2 = listtools.get_envelope(self.childs, i1, i2)
        if i1 == self.length and self.childs:
            j1 -= len(self.childs[-1])
        return max(0, j1), min(j2, self.length)



def create_paragraphs(textboxes, maxw=0, Paragraph=Paragraph, device=TESTDEVICE):
    # Erzeugt eine Liste von Paragraphen
    r = []
    l = []
    for box in textboxes:
        l.append(box)
        if isinstance(box, NewlineBox):
            if maxw>0:
                rows = simple_linewrap(l, maxw, device)
            else:
                rows = [Row(l, device)]
            r.append(Paragraph(rows, device))
            l = []
    if l:
        if maxw>0:
            rows = simple_linewrap(l, maxw, device)
        else:
            rows = [Row(l, device)]
        r.append(Paragraph(rows, device))
    assert listtools.calc_length(r) == listtools.calc_length(textboxes)
    return r


class Updater:
    # Der updater ist absichtlich kein View von Model. Vielmehr soll
    # der TextView diese Rolle haben. KOnserquenterweise muss der View
    # die inserted, removed und changed-Signale an den Updater
    # weitergeben.
    def __init__(self, model, factory, maxw=0):
        self.model = model
        self._maxw = maxw
        assert factory is not None
        self.factory = factory
        self.rebuild()

    def create_paragraphs(self, i1, i2):
        factory = self.factory
        boxes = factory.create_boxes(self.model.texel, i1, i2)
        return create_paragraphs(
            boxes, self._maxw, 
            Paragraph = factory.Paragraph,
            device = factory.device)

    def rebuild(self):
        factory = self.factory
        l = self.create_paragraphs(0, len(self.model))
        self.layout = factory.ParagraphStack(l, device=factory.device)

    def set_maxw(self, maxw):
        if maxw != self._maxw:
            self._maxw = maxw
            self.rebuild()

    def properties_changed(self, i1, i2):
        j1, j2 = self.layout.get_envelope(i1, i2)
        new = self.create_paragraphs(j1, j2)
        self.layout.replace(j1, j2, new)
        assert len(self.layout) == len(self.model)

    def inserted(self, i, n):
        j1, j2 = self.layout.get_envelope(i, i)
        new = self.create_paragraphs(j1, j2+n)
        self.layout.replace(j1, j2, new)
        assert len(self.layout) == len(self.model)

    def removed(self, i, n):
        j1, j2 = self.layout.get_envelope(i, i+n+1) # +1 wg Newline
        new = self.create_paragraphs(j1, j2-n)
        self.layout.replace(j1, j2, new)
        assert len(self.layout) == len(self.model)



class Factory:
    TextBox = TextBox
    NewlineBox = NewlineBox
    TabulatorBox = TabulatorBox
    Paragraph = Paragraph
    ParagraphStack = ParagraphStack
    def __init__(self, device=TESTDEVICE):
        self.device = device
    
    def create_boxes(self, texel, i1=None, i2=None):
        if i1 is None:
            assert i2 is None
            i1 = 0 
            i2 = len(texel)
        else:
            assert i1 <= i2
            i1 = max(0, i1)
            i2 = min(len(texel), i2)
        if i1 == i2:
            return ()
        name = texel.__class__.__name__+'_handler'
        handler = getattr(self, name)
        boxes = handler(texel, i1, i2)
        if not i2-i1 == listtools.calc_length(boxes):
            print i1, i2, texel
            print boxes
        assert i2-i1 == listtools.calc_length(boxes)
        return tuple(boxes)

    def Group_handler(self, texel, i1, i2):
        r = []
        j1 = 0
        for child in texel.data:
            j2 = j1+len(child)
            if i1 < j2 and j1 < i2: # Test auf Überlapp -> Alle Texel,
                                    # die im Intervall [i1, i2] liegen
                                    # oder es schneiden
                r.extend(self.create_boxes(child, i1-j1, i2-j1))
            j1 = j2
        return r

    def Characters_handler(self, texel, i1, i2):
        return [self.TextBox(texel.data[i1:i2], texel.style, self.device)]

    def NewLine_handler(self, texel, i1, i2):
        return [self.NewlineBox(texel.style, self.device)] # XXX: Hmmmm

    def Tabulator_handler(self, texel, i1, i2):
        return [self.TabulatorBox(texel.style, self.device)]


        
def check_box(box, texel=None):
    # - muss für alle Indizes infos liefern
    for i in range(len(box)+1):
        assert len(box.get_info(i, 0, 0)) == 4

    if texel is None:
        return True

    # - alle Indizes, die einzeln selektierbar sind müssen auch
    #   kopierbar sein
    for i in range(len(box)):
        j1, j2 = box.extend_range(i, i+1)
        a, b = texel.split(j1)
        assert len(a)+len(b) == len(texel)
        c, d = texel.split(j2)
        assert len(c)+len(d) == len(texel)
        rest, part = texel.takeout(j1, j2)
        assert len(part) == j2-j1
        assert len(rest)+len(part) == len(texel)

    for i in range(len(box)):
        if i+2>len(box):
            continue
        j1, j2 = box.extend_range(i, i+2)        
        a, b = texel.split(j1)
        assert len(a)+len(b) == len(texel)        
        c, d = texel.split(j2)
        assert len(c)+len(d) == len(texel)
        rest, part = texel.takeout(j1, j2)
        assert len(part) == j2-j1
        assert len(rest)+len(part) == len(texel)

    return True        
    


def test_00():
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
    assert str(t1.split(5)) == "(TB('01234'), TB('56789'))"


def test_01():
    factory = Factory()
    boxes = factory.create_boxes(TextModel("123").texel)
    assert listtools.calc_length(boxes) == 3
    boxes = factory.create_boxes(TextModel("123\n567").texel)
    assert listtools.calc_length(boxes) == 7
    paragraphs = create_paragraphs(boxes)
    assert len(paragraphs) == 2
    assert len(paragraphs[0]) == 4
    assert len(paragraphs[1]) == 3
    assert listtools.calc_length(paragraphs) == 7

def test_02():
    "ParagraphStack"
    factory = Factory()
    texel = TextModel("123\n567").texel
    boxes = factory.create_boxes(texel)
    assert listtools.calc_length(boxes) == 7
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert check_box(stack, texel)

    texel = TextModel("123\n\n5\n67").texel
    boxes = factory.create_boxes(texel)
    assert listtools.calc_length(boxes) == 9
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert check_box(stack, texel)
    assert stack.extra_height == 0

    texel = TextModel("123\n").texel
    boxes = factory.create_boxes(texel)
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert stack.childs[-1].has_newline()
    assert stack.extra_height == 1.0
    par = stack.childs[-1]
    assert len(par) == 4
    assert len(stack) == 4

    assert stack.get_info(3, 0, 0)[-2:] == (3, 0)
    assert stack.get_info(4, 0, 0)[-2:] == (0, 1)

    texel = TextModel("").texel
    boxes = factory.create_boxes(texel)
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert stack.extra_height > 0
    

def test_03():
    "Factory"
    factory = Factory()
    texel = TextModel("123\n\n567890 2 4 6 8 0").texel
    boxes = factory.create_boxes(texel)
    assert str(boxes) == "(TB('123'), NL, NL, TB('567890 2 4 6 8 0'))"
    paragraphs = create_paragraphs(boxes)
    stack = ParagraphStack(paragraphs)
    assert str(stack.childs) == "(Paragraph[Row[TB('123'), NL]], " \
        "Paragraph[Row[NL]], Paragraph[Row[TB('567890 2 4 6 8 0')]])"

    paragraphs = create_paragraphs(boxes, 5)
    assert repr(paragraphs) == "[Paragraph[Row[TB('123'), NL]], " \
        "Paragraph[Row[NL]], Paragraph[Row[TB('56789')], " \
        "Row[TB('0 2 4')], Row[TB(' 6 8 ')], Row[TB('0')]]]"

    texel = TextModel("123\t\t567890 2 4 6 8 0").texel
    boxes = factory.create_boxes(texel)


def test_04():
    "insert/remove"
    factory = Factory()
    model = TextModel("123\n\n567890 2 4 6 8 0")
    boxes = factory.create_boxes(model.texel)
    paragraphs = create_paragraphs(boxes)
    updater = Updater(model, factory, maxw=0)
    layout = updater.layout
    assert repr(layout) == "ParagraphStack[Paragraph[Row[TB('123'), " \
        "NL]], Paragraph[Row[NL]], Paragraph[Row[TB('567890 2 4 6 8 0')]]]"
    assert len(layout) == len(model)
    assert layout.height == 3

    ins = TextModel("xyz\n")
    model.insert(2, ins)
    updater.inserted(2, len(ins))
    assert len(layout) == len(model)
    assert repr(layout) == "ParagraphStack[Paragraph[Row[TB('12xyz'),"\
        " NL]], Paragraph[Row[TB('3'), NL]], Paragraph[Row[NL]], "\
        "Paragraph[Row[TB('567890 2 4 6 8 0')]]]"
    assert layout.height == 4
    model.remove(2, 2+len(ins))
    updater.removed(2, len(ins))
    assert len(layout) == len(model)
    assert repr(layout) == "ParagraphStack[Paragraph[Row[TB('123'), " \
        "NL]], Paragraph[Row[NL]], Paragraph[Row[TB('567890 2 4 6 8 0')]]]"
    assert layout.height == 3

    factory = Factory()
    model = TextModel("123")
    updater = Updater(model, factory, maxw=0)
    layout = updater.layout

    ins = TextModel("xyz\n")    
    i = len(model)
    model.insert(i, ins)
    updater.inserted(i, len(ins))
    
    for c in "abc":
        ins = TextModel(c)    
        i = len(model)
        model.insert(i, ins)
        updater.inserted(i, len(ins))
    assert str(layout) == "ParagraphStack[Paragraph[Row[TB('123xyz'), NL]], " \
        "Paragraph[Row[TB('abc')]]]"


def test_05():
    device = TESTDEVICE
    factory = Factory(device)
    model = TextModel("123\n\n567890 2 4 6 8 0")
    updater = Updater(model, factory, maxw=0)
    layout = updater.layout
    
    def check(box):
        if not box.device is device:
            print box
        assert box.device is device
        if hasattr(box, 'iter'):
            for j1, j2, x1, y1, child in box.riter(0, 0, 0):
                check(child)
    check(layout)

def test_06():
    factory = Factory()
    model = TextModel("123\n")
    updater = Updater(model, factory, maxw=0)
    layout = updater.layout
    assert layout.get_info(4, 0, 0)
    assert str(layout.get_info(3, 0, 0)) == "(NL, 0, 3, 0.0)"
    assert layout.get_info(3, 0, 0)[-2:] == (3, 0)
    assert layout.get_info(4, 0, 0)[-2:] == (0, 1)

def test_07():
    # Problem: Wenn man recht neben eine Zeile klickt springt der
    # Cursor nicht an die letzte, sondern an die vorletzte Position.
    factory = Factory()
    model = TextModel("123\n567")
    updater = Updater(model, factory, maxw=0)
    layout = updater.layout
    assert layout.get_index(100, 0.5) == 3

def test_08():
    # Problem: get_rect gibt immer 0, 0
    t1 = TextBox("0123456789")
    t2 = TextBox("0123456789")
    p1 = Paragraph([Row([t1, t2, NewlineBox(defaultstyle)])])

    assert p1.get_rect(0, 0, 0) == Rect(0, 0.0, 1, 1.0)
    assert p1.get_rect(10, 0, 0) == Rect(10, 0.0, 11, 1.0)




if __name__ == '__main__':
    from textmodel import alltests
    alltests.dotests()
