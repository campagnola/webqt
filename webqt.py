import json
import PyQt5
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

# Most key codes are identical between JS and Qt; only need to specify a few:
key_map = {'Key'+k:getattr(QtCore.Qt, 'Key_'+k) for k in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}
key_map.update({'Digit%d'%i:getattr(QtCore.Qt, 'Key_%d'%i) for i in range(10)})
key_map.update({
    'ArrowLeft': QtCore.Qt.Key_Left,
    'ArrowUp': QtCore.Qt.Key_Up,
    'ArrowRight': QtCore.Qt.Key_Right,
    'ArrowDown': QtCore.Qt.Key_Down,
    'Quote': QtCore.Qt.Key_Apostrophe,
    'ShiftLeft': QtCore.Qt.Key_Shift,
    'AltLeft': QtCore.Qt.Key_Alt,
    'ControlLeft': QtCore.Qt.Key_Control,
    'MetaLeft': QtCore.Qt.Key_Meta,
    'ShiftRight': QtCore.Qt.Key_Shift,
    'AltRight': QtCore.Qt.Key_Alt,
    'ControlRight': QtCore.Qt.Key_Control,
    'MetaRight': QtCore.Qt.Key_Meta,
    'ContextMenu': QtCore.Qt.Key_Menu,
})


modifier_map = {
    'altKey': QtCore.Qt.AltModifier,
    'ctrlKey': QtCore.Qt.ControlModifier,
    'shiftKey': QtCore.Qt.ShiftModifier,
    'metaKey': QtCore.Qt.MetaModifier
}

def modifiers(ev):
    mods = QtCore.Qt.NoModifier
    for k,v in modifier_map.items():
        if ev.get(k, False):
            mods = mods | v
    return mods


class BrowserMouseEvent(object):
    def __init__(self, root_widget, event):
        self.root_widget = root_widget
        self.event = event

    def type(self):
        ev_type = self.event['event_type']
        typ = {
            'mousePress': QtCore.QEvent.MouseButtonPress,
            'mouseRelease': QtCore.QEvent.MouseButtonRelease,
            'mouseMove': QtCore.QEvent.MouseMove,
        }[ev_type]
        return typ
        
    def pos(self):
        ev = self.event
        root_pos = QtCore.QPoint(ev['x'], ev['y'])
        return root_pos
    
    def globalPos(self):
        return self.root_widget.mapToGlobal(self.pos())
    
    def widgetPos(self, widget):
        return widget.mapFromGlobal(self.globalPos())
        
    def widget(self):
        return self.root_widget.childAt(self.pos()) or self.root_widget
        
    def button(self):
        if self.event['event_type'] == 'mouseMove':
            return QtCore.Qt.NoButton
        
        # JS button coding is weird:
        all_btns = [QtCore.Qt.LeftButton, QtCore.Qt.MiddleButton, QtCore.Qt.RightButton]
        btn = all_btns[self.event['button']]
        return btn
        
    def buttons(self):
        ev = self.event
        all_btns = [QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton]
        btns = QtCore.Qt.NoButton
        for i in range(3):
            if ev['buttons'] & 2**i > 0:
                btns = btns | all_btns[i]
        return btns
    
    def modifiers(self):
        return modifiers(self.event)

    def mouseEvent(self, widget):
        global_pos = self.root_widget.mapToGlobal(self.pos())
        pos = widget.mapFromGlobal(global_pos)
        return QtGui.QMouseEvent(self.type(), pos, global_pos, self.button(), self.buttons(), self.modifiers())
    
    def wheelEvent(self, widget):
        global_pos = self.root_widget.mapToGlobal(self.pos())
        pos = widget.mapFromGlobal(global_pos)
        if pg.Qt.lib in ['PyQt4', 'PySide']:
            return QtGui.QWheelEvent(pos, global_pos, self.event['deltaY'], self.buttons(), self.modifiers())
        else:
            return QtGui.QWheelEvent(pos, global_pos, QtCore.QPoint(), QtCore.QPoint(self.event['deltaX'], self.event['deltaY']), self.event['deltaY'], QtCore.Qt.Vertical, self.buttons(), self.modifiers())

    
class WidgetProxy(QtCore.QObject):
    
    _incoming_event_signal = QtCore.Signal(object)
    
    def __init__(self, widget, socket, hide=True):
        QtCore.QObject.__init__(self)
        if hide:
            widget.setAttribute(QtCore.Qt.WA_DontShowOnScreen)
        self.widget = widget
        self._mouse_grabber = None
        self.socket = socket
        socket.set_callback(self._received_event)
        self._installFilter(widget)
        self._updateTimer = QtCore.QTimer()
        self._updateTimer.timeout.connect(self._sendUpdate)
        self._incoming_event_signal.connect(self._handle_event)
        
    def _installFilter(self, obj):
        obj.installEventFilter(self)
        for ch in obj.children():
            self._installFilter(ch)
    
    def eventFilter(self, obj, ev):
        #print (obj, ev)
        if ev.type() == QtCore.QEvent.Paint:
            self._updateTimer.start(0)
            return False
        elif ev.type() == QtCore.QEvent.ChildAdded:
            
            self._installFilter(obj)
        return False
    
    def _sendUpdate(self):
        #print("update!")
        px = self.widget.grab()
        # must come after grab() because it causes a paintEvent
        self._updateTimer.stop()
        ba = QtCore.QByteArray()
        buf = QtCore.QBuffer(ba)
        buf.open(QtCore.QIODevice.WriteOnly)
        px.save(buf, "JPG")
        data = ba.data()
        self.socket.send_image(data)
        
    def _received_event(self, ev):
        # new event arrived from socket; send back to GUI thread
        # via signal
        self._incoming_event_signal.emit(ev)
        
    def _handle_event(self, ev):
        ev_type = ev['event_type']
        if ev_type.startswith('mouse'):
            self._update_window_pos(ev)
            self._mouse_event(ev)
        elif ev_type == 'wheel':
            self._update_window_pos(ev)
            self._wheel_event(ev)
        elif ev_type.startswith('key'):
            self._key_event(ev)
        else:
            raise TypeError("Unknown event type: %s" % ev_type)

    def _update_window_pos(self, ev):
        ev_pos = (ev['screenX'] - ev['x'], ev['screenY'] - ev['y'])
        pos = self.widget.window().pos()
        if ev_pos != (pos.x(), pos.y()):
            self.widget.window().move(*ev_pos)
            #print("New position: ", self.widget.window().pos())
        
    def _wheel_event(self, ev):
        ev = BrowserMouseEvent(self.widget, ev)
        w = ev.widget()
        while w is not None:
            event = ev.wheelEvent(w)
            QtGui.QApplication.sendEvent(w, event)
            if event.isAccepted():
                break
            else:
                w = w.parent()
        
    def _mouse_event(self, ev):
        # Attempt to re-implement Qt's mouse event handling.
        # QTest is not quite up to this task, and there does not seem to be
        # another way to simulate mouse events.
    
        ev_type = ev['event_type']
        ev = BrowserMouseEvent(self.widget, ev)
        
        widget = self._mouse_grabber
        #print("--------------------------------")
        #print(ev_type, widget, ev.button(), ev.buttons())
        
        if widget is None:
            #print("  No grabber..")
            widget = ev.widget()
            if ev_type == 'mousePress':
                #print("  new grabber:", widget)
                self._mouse_grabber = widget
                self._click_focus(widget)
            elif ev_type == 'mouseMove' and not widget.hasMouseTracking():
                #print("    ignore move")
                return
        else:
            if ev_type == 'mouseRelease':
                #print("  released grabber")
                self._mouse_grabber = None
        
        w = widget
        while w is not None:
            event = ev.mouseEvent(w)
            #print("  send event:", ev_type, w)
            #print(" ", event.pos(), event.globalPos(), int(event.button()), int(event.buttons()))
            QtGui.QApplication.sendEvent(widget, event)
            if event.isAccepted():
                #print("  accepted!")
                break
            else:
                #print("  ignored; try parent..")
                w = w.parent()

    def _click_focus(self, widget):
        while widget is not None:
            if int(widget.focusPolicy() & QtCore.Qt.ClickFocus) > 0:
                QtGui.QApplication.setActiveWindow(widget.window())
                widget.setFocus(QtCore.Qt.MouseFocusReason)
                return
            widget = widget.parent()

    def _key_event(self, ev):
        typ = QtCore.QEvent.KeyPress if ev['event_type'] == 'keyDown' else QtCore.QEvent.KeyRelease
        key = key_map.get(ev['code'])
        if key is None:
            key = getattr(QtCore.Qt, 'Key_' + ev['code'], None)
        if key is None:
            print("Unknown browser key code: %s" % ev['code'])
            return
        mods = modifiers(ev)
        # Is there a better way to determine what text to insert?
        text = ev['key'] if len(ev['key'])  == 1 else ''
        autorep = ev['repeat']
        count = 1
        event = QtGui.QKeyEvent(typ, key, mods, text, autorep, count)
        QtGui.QApplication.sendEvent(QtGui.QApplication.focusWidget(), event)
