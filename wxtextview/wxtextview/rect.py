from math import sqrt


class Rect:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
        
    def __repr__(self):
        return 'Rect%s' % repr((self.x1, self.y1, self.x2, self.y2))

    def dist(self, x, y):
        dx = max(self.x1 - x, 0, x - self.x2);
        dy = max(self.y1 - y, 0, y - self.y2)
        return sqrt(dx*dx + dy*dy)

    def adist(self, x, y):
        # alternative dist: puts stronger weight on y-deviations
        dx = max(self.x1 - x, 0, x - self.x2);
        dy = max(self.y1 - y, 0, y - self.y2)
        #print "adist:", self, x, y, dx, dy
        return dy*dy, dx*dx

    def items(self):
        return self.x1, self.y1, self.x2, self.y2

    def __eq__(self, other):
        return self.items() == other.items()


def combine_rects(r1, r2):
    if r1 is None:
        return r2
    elif r2 is None:
        return r1
    r = Rect(0, 0, 0, 0)
    r.x1 = min(r1.x1, r2.x1)
    r.x2 = max(r1.x2, r2.x2)
    r.y1 = min(r1.y1, r2.y1)
    r.y2 = max(r1.y2, r2.y2)
    return r
