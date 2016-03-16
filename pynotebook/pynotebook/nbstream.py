# -*_ coding: latin-1 -*-

# The purpose of streams is to combine the stdout and stderr channels
# into a single channel, aka a "stream".


from .textmodel import TextModel
from .textmodel.texeltree import Texel


class StreamBase:
    # Stream protocol
    def output(self, obj, iserr=False):
        pass


class StreamRecorder(StreamBase):
    # A stream which stores all output calls into a list
    
    def __init__(self):
        self.messages = []

    def output(self, arg, iserr=False):
        self.messages.append((arg, iserr))



class Stream(StreamBase):
    # A stream which stores the output into a textmodel

    def __init__(self):
        self.model = TextModel()

    def output(self, obj, iserr=False):
        if isinstance(obj, Texel):
            new = TextModel()
            new.texel = obj
        else:
            if iserr:
                properties = {'textcolor':'red'}
            else:
                properties = {}
            if isinstance(obj, unicode):
                new = TextModel(obj, **properties)
            elif isinstance(obj, str):
                u = unicode(obj, 'utf-8')
                new = TextModel(u, **properties)
            else:
                new = TextModel(str(obj), **properties)
        self.model.append(new)
