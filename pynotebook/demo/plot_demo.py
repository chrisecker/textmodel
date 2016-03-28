# -*- coding: latin-1 -*-


import sys
sys.path.insert(0, '..')

from pynotebook.nbview import TextModel, WXTextView, Cell
from pynotebook.textformat import fromtext
import wx



examples = r"""[In 0]:
import matplotlib
matplotlib.use('Agg')
from pylab import *

if matplotlib.__version__ >= '1.4':
    matplotlib.style.use('ggplot')


[In 0]:
fig = plt.figure(facecolor='white')
r = np.arange(0, 3.0, 0.01)
theta = 2 * np.pi * r

ax = plt.subplot(111, polar=True)
ax.plot(theta, r, color='r', linewidth=3)
ax.set_rmax(2.0)
ax.grid(True)

ax.set_title("A line plot on a polar axis", va='bottom')
output(fig)

[In 0]:
fig # ... and again, this time without "output"!
[In 0]:
from numpy import cos
alpha = 0.7
phi_ext = 2 * pi * 0.5

def flux_qubit_potential(phi_m, phi_p):
    return 2 + alpha - 2 * cos(phi_p)*cos(phi_m) - alpha * cos(phi_ext - 2*phi_p)

phi_m = linspace(0, 2*pi, 100)
phi_p = linspace(0, 2*pi, 100)
X,Y = meshgrid(phi_p, phi_m)
Z = flux_qubit_potential(X, Y).T

fig, ax = plt.subplots()
fig.set_facecolor('white')

p = ax.pcolor(X/(2*pi), Y/(2*pi), Z, cmap=cm.RdBu, vmin=abs(Z).min(), vmax=abs(Z).max())
cb = fig.colorbar(p, ax=ax)
output(fig)
[In 0]:
fig, ax = plt.subplots(facecolor='white')
cnt = contour(Z, cmap=cm.RdBu, vmin=abs(Z).min(), vmax=abs(Z).max(), extent=[0, 1, 0, 1])
output(fig)
"""


def demo_00():
    app = wx.App(redirect=False)
    model = fromtext(examples, Cell=Cell)

    frame = wx.Frame(None)
    win = wx.Panel(frame, -1)
    view = WXTextView(win, -1, style=wx.SUNKEN_BORDER)
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)

    frame.Show()

    if 0:
        from pynotebook.wxtextview import testing
        testing.pyshell(locals())
    app.MainLoop()


if __name__ == '__main__':
    demo_00()
