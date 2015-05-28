#
#		Python GUI - View Base - Generic
#

from .properties import overridable_property

class ViewBase(object):
    """ViewBase is an abstract base class for user-defined views.
    It provides facilities for handling mouse and keyboard events
    and associating the view with one or more models, and default
    behaviour for responding to changes in the models."""

    models = overridable_property('models',
        "List of Models being observed. Do not modify directly.")

    model = overridable_property('model',
        "Convenience property for views which observe only one Model.")


    def __init__(self):
        self._models = []

    def destroy(self):
        #print "ViewBase.destroy:", self ###
        for m in self._models[:]:
            #print "ViewBase.destroy: removing model", m ###
            self.remove_model(m)

    #
    #		Getting properties
    #

    def get_model(self):
        models = self._models
        if models:
            return self._models[0]
        else:
            return None

    def get_models(self):
        return self._models

    #
    #		Setting properties
    #

    def set_model(self, new_model):
        models = self._models
        if not (len(models) == 1 and models[0] == new_model):
            for old_model in models[:]:
                self.remove_model(old_model)
            if new_model is not None: # XXX CHRIS. Vorher gabs Probleme mit __len__
                self.add_model(new_model)

    #
    #   Model association
    #

    def add_model(self, model):
        """Add the given Model to the set of models being observed."""
        if model not in self._models:
            self._models.append(model)
            model.add_view(self)

    def remove_model(self, model):
        """Remove the given Model from the set of models being observed."""
        if model in self._models:
            self._models.remove(model)
            model.remove_view(self)

    #
    #		Callbacks
    #

    def model_changed(self, model, *args, **kwds):
        """Default method called by the attached Model's notify_views
        method. Default is to date the whole view."""
        pass #self.invalidate()

    def model_destroyed(self, model):
        """Called when an attached model is destroyed."""
        pass

