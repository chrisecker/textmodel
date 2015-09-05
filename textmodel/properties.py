# -*- coding: latin-1 -*-


class Properties(object):
    """
    This class implements the standard interface for initialising
    properties using keyword arguments.
    """

    def __init__(self, **kw):
        "Properties(name=value, ...) passes the given arguments to the set() method."
        self.set(**kw)

    def set(self, **kw):
        """set(name=value, ...) sets property values according to the given
        keyword arguments."""
        for name, value in kw.iteritems():
            try:
                getattr(self, 'set_' + name)(value)
            except AttributeError:
                # Der Setter existiert nicht. Gibt es vielleicht ein
                # passendes Propertyobjekt?
                try:
                    obj = getattr(self.__class__, name)
                except :
                    raise AttributeError, name
                obj.fset(self, value)




def overridable_property(name, doc = None):
    """Creates a property which calls methods get_xxx and set_xxx of
    the underlying object to get and set the property value, so that
    the property's behaviour may be easily overridden by subclasses."""

    getter_name = intern('get_' + name)
    setter_name = intern('set_' + name)
    return property(
        lambda self: getattr(self, getter_name)(),
        lambda self, value: getattr(self, setter_name)(value),
        None,
        doc)


