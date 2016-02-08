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

    def colorize(self, texel):
        """Colorizes $texel$ to make it more readable. """
        return texel



class ClientPool:
    def __init__(self):
        self._clients = {}

    def register(self, client):
        self._clients[client.name] = client

    def get_matching(self, texel):
        return self._clients[texel.client_name]
