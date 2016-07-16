# -*- coding: latin-1 -*-


from ..textmodel.viewbase import ViewBase, overridable_property
from ..textmodel.modelbase import Model
from ..textmodel.textmodel import dump_range
from ..textmodel import TextModel


debug = 0
#debug = 1

def undo(info):
    if callable(info[0]):
        func = info[0]
        args = info[1:]    
        redo = apply(func, args)
    else:
        redo = []
        for child in reversed(info):
            redo.append(undo(child))
    return redo


class TextView(ViewBase, Model):
    index = overridable_property('index')
    _index = 0
    selection = overridable_property('selection') # NOTE: i2 can also
                                                  # be smaller than
                                                  # i1!
    _selection = None
    maxw = overridable_property('maxw')
    _maxw = 0
    _scrollrate = 10, 10
    _TextModel = TextModel
    def __init__(self):
        ViewBase.__init__(self)
        self._undoinfo = []
        self._redoinfo = []
        self.set_model(self._TextModel(''))
        assert self.layout is not None

    def create_builder(self):
        pass

    def set_model(self, model):
        ViewBase.set_model(self, model)
        self.builder = self.create_builder()
        self.rebuild()

    def rebuild(self):
        self.builder.rebuild()
        self.layout = self.builder.get_layout()
        assert self.layout is not None

    def join_undo(self, info2, info1):
        # we are joining similar undo entries
        if 0:
            print "join"
            print "info1=", info1
            print "info2=", info2
        if info1[0] == info2[0]:
            if info1[0] == self._remove:
                i1, i2 = info1[1:]
                j1, j2 = info2[1:]
                if i2 == j1 and j2-i1<10:
                    return [(self._remove, i1, j2)]
            elif info1[0] == self._undo_remove:
                s, i1, i2 = info1[1:]
                t, j1, j2 = info2[1:]
                #print "i1, i2:", i1, i2
                #print "j1, j2:", j1, j2
                if j2 == i1 and i2-j1<10:
                    t.insert(len(t), s)
                    return [(self._undo_remove, t, j1, i2)]
                if i1 == j1 and i2-j1<10:
                    t.insert(0, s)
                    #print "remove:", repr(t.get_text()), i1, i2+j2-j1
                    return [(self._undo_remove, t, i1, i2+j2-j1)]
                    
        return [info2, info1]

    def undo(self):
        if len(self._undoinfo) > 0:
            self.add_redo(undo(self._undoinfo[0]))
            del self._undoinfo[0]
                
    def add_undo(self, info, clear_redo = 1):
        if info is not None:
            if len(self._undoinfo):
                joined = self.join_undo(info, self._undoinfo[0])
                self._undoinfo = joined + self._undoinfo[1:]
            else:
                self._undoinfo.insert(0, info)
            if clear_redo:
                self._redoinfo = []
            self.notify_views('undo_changed')

    def redo(self):
        if len(self._redoinfo) > 0:
            self.add_undo(undo(self._redoinfo[0]), 0)
            del self._redoinfo[0]

    def add_redo(self, info):
        # Internal method: add a single redo info
        self._redoinfo.insert(0, info)
        self.notify_views('undo_changed')

    def insert(self, i, textmodel):
        self.model.insert(i, textmodel)
        self.index = i+len(textmodel)
        info = self._remove, i, i+len(textmodel)
        self.add_undo(info)

    def insert_text(self, i, text, **style):
        model = self.model.__class__(text, **style)  
        return self.insert(i, model)

    def remove(self, i1, i2):
        info = self._remove(i1, i2)
        self.add_undo(info)
        self.index = i1

    def _remove(self, i1, i2):
        old = self.model.remove(i1, i2)
        self.index = i1
        return self._undo_remove, old, i1, i2

    def _undo_remove(self, old, i1, i2):
        self.model.insert(i1, old)
        self.index = i2
        return self._remove, i1, i2

    def set_maxw(self, maxw):
        if maxw == self._maxw:
            return
        self._maxw = maxw
        self.builder.set_maxw(maxw)
        self.layout = self.builder.get_layout()
        self.Refresh()
        self.notify_views('maxw_changed')

    def compute_index(self, x, y):
        if y >= self.layout.height:
            return len(self.model)-1
        if y < 0:
            return 0
        return self.layout.get_index(x, y)

    def handle_action(self, action, shift=False):
        #print "action = ", action, shift
        model = self.model
        index = self.index
        layout = self.layout
        if index == len(model):
            if index == 0:
                style = {} 
            else:
                style = model.get_style(index-1)
        else:
            style = model.get_style(index)
        row, col = self.current_position()
        rect = layout.get_rect(index, 0, 0)
        x = rect.x1
        y = rect.y1

        def del_selection():
            if self.has_selection():
                s1, s2 = sorted(self.selection)
                s1, s2 = layout.extend_range(s1, s2)
                self.remove(s1, s2)

        if action == 'dump_info':
            s1, s2 = sorted(self.selection)
            s1, s2 = layout.extend_range(s1, s2)
            dump_range(model.texel, s1, s2)
            row, col = model.index2position(index)
            print "index=", index
            print "row=", row
            print "col=", col

        elif action == 'dump_boxes':
            layout.dump_boxes(0, 0, 0)
            
        elif action == 'move_word_end':
            i = index
            n = len(model)
            try:
                while not model.get_text(i, i+1).isalnum():
                    i = i+1
                while model.get_text(i, i+1).isalnum():
                    i = i+1
            except IndexError:
                i = n
            self.set_index(i, shift)
        elif action == 'move_right':
            self.set_index(index+1, shift)
        elif action == 'move_word_begin':
            i = index
            try:
                while not model.get_text(i-1, i).isalnum():
                    i = i-1
                while model.get_text(i-1, i).isalnum():
                    i = i-1
            except IndexError:
                i = 0
            self.set_index(i, shift)
        elif action == 'move_left':
            self.set_index(index-1, shift)
        elif action == 'move_paragraph_end':
            i = row
            try:
                while model.linelength(i) == 1:
                    i += 1
                while model.linelength(i) > 1:
                    i += 1
                self.move_cursor_to(i, 0, shift)
            except IndexError:
                self.set_index(len(model), shift)                    
        elif action == 'move_down':
            self.move_cursor_to(row+1, col, shift)
        elif action == 'move_paragraph_begin':
            i = row-1
            while i >= 0 and model.linelength(i) == 1:
                i -= 1
            while i >= 0 and model.linelength(i) > 1:
                i -= 1
            self.move_cursor_to(i+1, 0, shift)
        elif action == 'move_up':
            self.move_cursor_to(row-1, col, shift)
        elif action == 'move_line_start':
            self.set_index(model.linestart(row), shift)
        elif action == 'move_line_end':
            self.set_index(model.linestart(row)+model.linelength(row)-1, shift)
        elif action == 'move_page_down':
            width, height = self.GetClientSize()
            i = self.compute_index(x, y+height)
            self.set_index(i, shift)            
        elif action == 'move_page_up':
            width, height = self.GetClientSize()
            i = self.compute_index(x, y-height)
            self.set_index(i, shift)
        elif action == 'move_document_start':
            self.set_index(0, shift)
        elif action == 'move_document_end':
            self.set_index(len(model), shift)
        elif action == 'select_all':
            self.selection = (0, len(model))
        elif action == 'insert_newline':
            self.insert(index, self._TextModel('\n', **style))
        elif action == 'insert_newline_indented':
            i = model.linestart(row)
            s = model.get_text(i, index)
            l = s[:len(s)-len(s.lstrip())]
            self.insert(index, self._TextModel('\n'+l, **style))
        elif action == 'backspace':
            del_selection()
            i = self.index
            if i>0:
                j1, j2 = layout.extend_range(i-1, i)
                self.remove(j1, j2)
        elif action == 'copy':
            self.copy()
        elif action == 'paste':
            self.paste()
        elif action == 'cut':
            self.cut()
        elif action == 'delete':
            if self.has_selection():
                del_selection()
            else:
                i = self.index
                if i < len(self.model):
                    j1, j2 = layout.extend_range(i, i+1)
                    self.remove(j1, j2)
        elif action == 'undo':
            self.undo()
        elif action == 'redo':
            self.redo()
        elif action == 'del_word_left':
            # find the beginning of the word
            i = index
            try:
                while not model.get_text(i-1, i).isalnum():
                    i = i-1
                while model.get_text(i-1, i).isalnum():
                    i = i-1
            except IndexError:
                i = 0
            self.remove(i, index)
        else:                  
            #print keycode
            assert len(action) == 1 # single character
            del_selection()
            self.insert_text(self.index, action, **style)
        self.Refresh()

    def copy(self):
        raise NotImplemented()

    def paste(self):
        raise NotImplemented()

    def cut(self):
        raise NotImplemented()
         
    def select_word(self, x, y):
        i = self.layout.get_index(x, y)
        if i is None:
            return
        model = self.model
        n = len(model)
        try:
            while not model.get_text(i-1, i).isalnum():
                i = i-1
            while model.get_text(i-1, i).isalnum():
                i = i-1
        except IndexError:
            i = 0
        i1 = i
        i = i1
        try:
            while not model.get_text(i, i+1).isalnum():
                i = i+1
            while model.get_text(i, i+1).isalnum():
                i = i+1
        except IndexError:
            i = n
        i2 = i
        self.index = i2
        self.selection = (i1, i2)

    def refresh(self):
        raise NotImplemented()

    def check(self):
        from ..textmodel.treebase import is_root_efficient
        assert is_root_efficient(self.layout)

    ### Signals issued by model
    def properties_changed(self, model, i1, i2):
        self.builder.properties_changed(i1, i2)
        self.layout = self.builder.get_layout()
        self.refresh()

    def inserted(self, model, i, n):
        self.builder.inserted(i, n)
        self.layout = self.builder.get_layout()
        if debug:
            self.check()
        if i>= self.index:
            self.index += n
        if self._selection is not None:
            s1, s2 = self.selection
            if i >= s1:
                s1 += n
            if i >= s2:
                s2 += n
            self.selection = s1, s2
        self.refresh()

    def removed(self, model, i, text):
        self.builder.removed(i, len(text))
        self.layout = self.builder.get_layout()
        n = len(text)
        i1 = i
        i2 = i+n
        m = len(model)
        index = self.index
        if index >= i2:
            self.index = index-n
        elif index > i1:
            self.index = i1
        if self._selection is not None:
            s1, s2 = self.selection
            if s1 >= i2:
                s1 -= n
            elif s1 > i1:
                s1 = i1
            if s2 >= i2:
                s2 -= n
            elif s2 > i1:
                s2 = i1
            self.selection = min(s1, m), min(s2, m)
        self.refresh()

    def keep_cursor_on_screen(self):
        pass
        
    ### Index
    def set_index(self, index, extend=False, update=True):
        if index < 0:
            index = 0
        elif index > len(self.model):
            index = len(self.model)
        if index != self._index:
            self._index = index
            if extend:
                self.extend_selection()
            elif update:
                self.start_selection()
            self.adjust_viewport()
            self.refresh()
            self.notify_views('index_changed')

    def get_index(self):
        return self._index

    def current_position(self):
        # Returns the cursorposition as tuple (row, col)
        model = self.model
        i = self.index
        if model is None or i == 0:
            return 0, 0
        return model.index2position(i)

    def move_cursor_to(self, row, col, extend=False, update=True):
        # Moves cursor to (row, col). If this position is non existent
        # the next possible value is selected.

        # extend: extend selection
        # update: update selection 

        model = self.model
        row = max(0, min(row, model.nlines()-1))
        col = max(0, min(col, model.linelength(row)-1))
        self.set_index(model.position2index(row, col), extend, update)

    def get_selection(self):
        return self._selection

    def set_selection(self, selection):
        old = self._selection
        if selection == old:
            return
        if old is not None:
            i1, i2 = old
        self._selection = selection
        self.Refresh()
        self.notify_views('selection_changed')

    def has_selection(self):
        selection = self.selection
        if selection is None:
            return False
        return selection[0] != selection[1]

    def get_selected(self):
        # Returns a list of selected regions. So far only a
        # continguous region can be selected. In the futur this can
        # change (for example for tables). Box.extend_selection should
        # be renamed in Box.get_selection then.
        selection = self.selection
        if selection is None:
            return []
        s1, s2 = sorted(self.selection)
        return [self.layout.extend_range(s1, s2)]

    def start_selection(self):
        index = self.index
        self.selection = index, index
        
    def extend_selection(self):
        # Moves the selection endoint to index
        selection = self.selection
        index = self.index
        if selection is None:
            self.selection = index, index
        else:
            self.selection = selection[0], index
        
        
    
