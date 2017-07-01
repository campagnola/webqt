import numpy as np
import io
from PIL import Image
import threading, time, itertools
import asyncio
import datetime
import random
import websockets
import json
import sys

import PyQt5
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui



class WebSocketThread(threading.Thread):
    def __init__(self, event_callback):
        threading.Thread.__init__(self)
        self.event_callback = event_callback
        self.daemon = True
        self.lock = threading.Lock()
        self.data = None
        
    async def send_updates(self, websocket):
        while True:
            with self.lock:
                data = self.data
                self.data = None
            
            if data is None:
                await asyncio.sleep(0.03)
                continue
            
            await websocket.send(data)
            await asyncio.sleep(0.01)

    async def recv_events(self, websocket):
        while True:
            message = await websocket.recv()
            try:
                self.event_callback(message)
            except Exception:
                sys.excepthook(*sys.exc_info())

    async def handler(self, websocket, path):
        tasks = [asyncio.ensure_future(self.send_updates(websocket)),
                 asyncio.ensure_future(self.recv_events(websocket))]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()
        
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = websockets.serve(self.handler, '127.0.0.1', 12345)
        loop.run_until_complete(start_server)
        loop.run_forever()

    def set_data(self, data):
        with self.lock:
            self.data = data


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
        return QtCore.QPoint(ev['x'], ev['y'])
    
    def globalPos(self):
        return self.root_widget.mapToGlobal(self.pos())
    
    def widgetPos(self, widget):
        return widget.mapFromGlobal(self.globalPos())
        
    def widget(self):
        widget = self.root_widget.childAt(self.pos())
        if widget is None:
            widget = self.root_widget
        return widget
        
    def button(self):
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
        return QtCore.Qt.NoModifier        

    def mouseEvent(self):
        return QtGui.QMouseEvent(self.type(), self.pos(), self.globalPos(), self.button(), self.buttons(), self.modifiers())
    
    def wheelEvent(self):
        if pg.Qt.lib in ['PyQt4', 'PySide']:
            return QtGui.QWheelEvent(self.pos(), self.globalPos(), self.event['deltaY'], self.buttons(), self.modifiers())
        else:
            return QtGui.QWheelEvent(self.pos(), self.globalPos(), QtCore.QPoint(), QtCore.QPoint(self.event['deltaX'], self.event['deltaY']), self.event['deltaY'], QtCore.Qt.Vertical, self.buttons(), self.modifiers())

    
class WebSocketProxy(QtCore.QObject):
    
    _incoming_event_signal = QtCore.Signal(object)
    
    def __init__(self, widget, hide=True):
        QtCore.QObject.__init__(self)
        if hide:
            widget.setAttribute(QtCore.Qt.WA_DontShowOnScreen)
        self.widget = widget
        self._mouse_grabber = None
        self.thread = WebSocketThread(event_callback=self._received_event)
        self.thread.start()
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
        self.thread.set_data(data)
        
    def _received_event(self, msg):
        # new event arrived from socket; send back to GUI thread
        # via signal
        ev = json.loads(msg)
        self._incoming_event_signal.emit(ev)
        
    def _handle_event(self, ev):
        ev_type = ev['event_type']
        if ev_type.startswith('mouse'):
            self._mouse_event(ev)
        elif ev_type == 'wheel':
            self._wheel_event(ev)
        else:
            raise TypeError("Unknown event type: %s" % ev_type)
        
    def _wheel_event(self, ev):
        ev = BrowserMouseEvent(self.widget, ev)
        event = ev.wheelEvent()
        QtGui.QApplication.sendEvent(ev.widget(), event)
        
    def _mouse_event(self, ev):
        # Attempt to re-implement Qt's mouse event handling.
        # QTest is not quite up to this task, and there does not seem to be
        # another way to simulate mouse events.
    
        ev = BrowserMouseEvent(self.widget, ev)
        ev_type = ev.type()
        
        widget = self._mouse_grabber
        if widget is None:
            if ev_type == 'mouseRelease':
                return
            widget = ev.widget()
            if ev_type == 'mouseMove' and not widget.hasMouseTracking():
                return
        
        #print(ev_type, widget, ev['x'], ev['y'], ev['button'], ev['buttons'])
        global last_grabber
        last_grabber = widget
        
        event = ev.mouseEvent()
        QtGui.QApplication.sendEvent(widget, event)
        
        #print("  accepted:", event.isAccepted())
        
        if ev_type == 'mousePress' and event.isAccepted():
            self._mouse_grabber = widget
        elif ev_type == 'mouseRelease':
            self._mouse_grabber = None
    

if __name__ == '__main__':
    pg.mkQApp()


    w = pg.PlotWidget()
    w.plot(np.random.normal(size=10000), antialias=True)
    w.addLine(x=0, movable=True)
    
    #w = QtGui.QSplitter(QtCore.Qt.Vertical)
    
    #plt = pg.PlotWidget()
    #plt.plot(np.random.normal(size=100))
    #w.addWidget(plt)
    
    #import pyqtgraph.console
    #console = pg.console.ConsoleWidget(namespace={'pg': pg, 'plt': plt})
    #w.addWidget(console)




    #w.setLayout(l)
    #btns = []
    #def mkfn(i, j):
        #def fn():
            #print("clicked", i, j)
        #return fn
    #for i in range(4):
        #for j in range(4):
            #btn = QtGui.QPushButton('%d-%d' % (i, j))
            #btn.clicked.connect(mkfn(i, j))
            #btns.append(btn)
            #l.addWidget(btn, i, j)
    
    w.resize(400, 800)
    wsp = WebSocketProxy(w)
    w.show()
