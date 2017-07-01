import numpy as np
import io
from PIL import Image
import threading, time, itertools
import asyncio
import datetime
import random
import websockets

import PyQt5
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui



class WebSocketThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.lock = threading.Lock()
        self.data = None
        
    async def send_updates(self, websocket, path):
        while True:
            with self.lock:
                data = self.data
                self.data = None
            if data is None:
                asyncio.sleep(0.03)
                continue
            
            await websocket.send(data)
            
            await asyncio.sleep(0.01)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = websockets.serve(self.send_updates, '127.0.0.1', 12345)
        loop.run_until_complete(start_server)
        loop.run_forever()

    def set_data(self, data):
        with self.lock:
            self.data = data


class WebSocketProxy(QtCore.QObject):
    def __init__(self, widget):
        QtCore.QObject.__init__(self)
        #widget.setAttribute(QtCore.Qt.WA_DontShowOnScreen)
        self.widget = widget
        self.thread = WebSocketThread()
        self.thread.start()
        self._installFilter(widget)
        self._updateTimer = QtCore.QTimer()
        self._updateTimer.timeout.connect(self._sendUpdate)
        
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
        px = self.widget.grab()
        # must come after grab() because it causes a paintEvent
        self._updateTimer.stop()
        ba = QtCore.QByteArray()
        buf = QtCore.QBuffer(ba)
        buf.open(QtCore.QIODevice.WriteOnly)
        px.save(buf, "JPG")
        data = ba.data()
        self.thread.set_data(data)
        
    
if __name__ == '__main__':
    pg.mkQApp()
    plt = pg.PlotWidget()
    plt.plot(np.random.normal(size=100))
    plt.show()
    wsp = WebSocketProxy(plt)
