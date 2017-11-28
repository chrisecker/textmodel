# -*- coding: latin-1 -*-




class Aborted(Exception):
    pass


class Client:
    name = 'unnamed' # each client should have a unique name 
    counter = 0
    can_abort = False # not all clients can abort

    def abort(self):
        pass

    def execute(self, texel):
        """Returns a tuple of completions. """
        pass

    def complete(self, word, nmax=None):
        """Returns a tuple of completions. """
        pass

    def colorize(self, texel, styles=None, bgcolor='white'):
        """Colorizes $texel$ to make it more readable. """
        return texel



class ClientPool:
    def __init__(self):
        self.clients = {}

    def add(self, client, name):
        self.clients[name] = client
        
    def register(self, client):
        self.add(client, client.name)

    def get(self, name):
        return self.clients[name]
    
    def get_matching(self, texel):
        return self.get(texel.client_name)

