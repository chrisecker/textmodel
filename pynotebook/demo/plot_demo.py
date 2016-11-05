# -*- coding: latin-1 -*-


import sys
sys.path.insert(0, '..')

from pynotebook.nbview import TextModel, NBView, ScriptingCell
from pynotebook.textformat import fromtext
import wx



examples = r"""[Text]:
Matplotlib Demo

The notebook consists of cells: scripting cells and text cells. The python code in scripting cells can be executed by moving the cursor in the cell and pressing shift + return. Scripting cells have an input field (marked by "In") and an output field ("Out"). Output usually consists of text printed to stdout or stderr by the python interpreter. Pynotbook can also display matplotlib graphics, other output types can be easily implemented. This demo shows how to output graphics created by matplotlib.

Try to execute the following cells.

Notes:
 - Use the tab-key to complete. 
 - To create a new cell, place the cursor below any output cell and start typing. 
 - You can copy, paste and delete cells.
 - There is undo (ctrl-z) and redo (ctrl-r).

Demo codes are taken from 
http://www.southampton.ac.uk/~fangohr/training/python/notebooks/Matplotlib.html


[In 0]:
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
fig # ... and again, this time without an explicit call to "output"!
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

[In]:
from mpl_toolkits.mplot3d import axes3d, Axes3D
fig = plt.figure()
ax = Axes3D(fig)
X, Y, Z = axes3d.get_test_data(0.05)
cset = ax.contour(X, Y, Z, 16, extend3d=True)
ax.clabel(cset, fontsize=9, inline=1)
output(fig)

"""


def demo_00():
    app = wx.App(redirect=False)
    model = fromtext(examples)
    # Apply some formating to make the demo look better
    model.set_properties(0, 16, fontsize=16, weight='bold', underline=True)
    model.set_properties(0, 876, family='swiss' )
    model.set_properties(558, 563, underline=True)
    frame = wx.Frame(None)
    win = wx.Panel(frame)
    view = NBView(win)
    view.model = model
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(view, 1, wx.ALL|wx.GROW, 1)
    win.SetSizer(box)
    win.SetAutoLayout(True)
    frame.Show()

    if 0:
        from pynotebook.wxtextview import testing
        testing.pyshell(locals())

    if 0:
        import celleinspector
        inspector = cellinspector.Inspector(frame)
        inspector.model = view
        inspector.Show()

    app.MainLoop()


if __name__ == '__main__':
    demo_00()
