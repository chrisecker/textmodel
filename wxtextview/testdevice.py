# -*- coding: latin-1 -*-

class TestDevice:
    # Device ist ein Interface-Layer zu den Plattformspezifischen
    # Grafik-Methoden. Zum Beispiel in Wx findet das zeichnen über das
    # dc-Objekt statt. Das Device Objekt für wx weiss wie das Wx-Dc
    # bedient wird.

    buffering = False
    def measure(self, text, style):
        return len(text), 1 # Dummy zum Testen

    def measure_parts(self, text, style):
        return tuple(range(1, len(text)+1)) # Dummy zum Testen

    def intersects(self, dc, rect):
        return True

    def invert_rect(self, x, y, w, h, dc):
        pass

    def draw_text(self, text, x, y, dc):
        pass


TESTDEVICE = TestDevice()
