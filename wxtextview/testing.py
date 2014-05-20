# -*- coding: latin-1 -*-



def pyshell(namespace=None):
    import wx.py
    style = wx.DEFAULT_FRAME_STYLE 
    f = wx.Frame(None,
                 pos=wx.DefaultPosition,
                 style=style
                 )
    f.Bind(wx.EVT_CLOSE, lambda e: f.Hide())
    box = wx.BoxSizer(wx.HORIZONTAL)
    if namespace is None:
        namespace = {}
    shell = wx.py.shell.Shell(
        f, -1, locals=namespace,                  
        size=(1000, 200),
        )
    f.shell = shell
    box.Add(shell, 1, wx.EXPAND)
    f.SetSizer(box)
    box.Fit(f)
    f.Fit()
    f.Show()


def logwindow():
    # Öffnet ein Logfenster und leitet die Stdout und Stderr darauf
    # um.
    import wx
    frame = wx.Frame(
                None,
                pos=wx.DefaultPosition,
                size=(300, 400),
                style = wx.DEFAULT_FRAME_STYLE \
                   #|wx.FRAME_FLOAT_ON_PARENT \
                   #|wx.FRAME_NO_TASKBAR \
                   #|wx.FRAME_TOOL_WINDOW,
                #title='Logfenster'                   
                )

    from logwindow import LogWindow
    LogWindow(frame, -1, size=wx.Size(400, 250))
    frame.Show()
    import log
    log.redirect_stdio()
    return frame


def demo_00():
    import wx
    app = wx.App(redirect=False)
    frame = logwindow()
    pyshell(locals())
    app.MainLoop()

if __name__=='__main__':
    import alltests
    alltests.dotests()


    
