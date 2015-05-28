# -*- coding: latin-1 -*-

class TestDevice:
    # Device is a interface layer to capsule platform dependent
    # graphics methods.

    buffering = False
    def measure(self, text, style):
        return len(text), 1 # Dummy for testing

    def measure_parts(self, text, style):
        return tuple(range(1, len(text)+1)) # Dummy for testing

    def intersects(self, dc, rect):
        return True

    def invert_rect(self, x, y, w, h, dc):
        pass

    def draw_text(self, text, x, y, dc):
        pass


TESTDEVICE = TestDevice()
