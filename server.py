import numpy as np
import io
from PIL import Image
import threading, time, itertools
import asyncio
import datetime
import random
import websockets

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
            #img = Image.fromarray(data, 'RGB')
            #f = io.BytesIO()
            ##img.save(f, format='png', compress_level=5)
            #img.save(f, format='jpeg')
            #f.seek(0)
            #await websocket.send(f.read())
            
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


thread = WebSocketThread()
thread.start()

import PyQt5
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

plt = pg.plot([1,4,2,3])
plt.window().setAttribute(QtCore.Qt.WA_DontShowOnScreen)

def update():
    global ba
    px = plt.grab()
    ba = QtCore.QByteArray()
    buf = QtCore.QBuffer(ba)
    buf.open(QtCore.QIODevice.WriteOnly)
    px.save(buf, "JPG")
    data = ba.data()
    thread.set_data(data)
        
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(100)

#frames = np.random.normal(size=(10, 800, 800, 3), loc=128, scale=20).astype('ubyte')

#for d in itertools.cycle(frames):
    #thread.set_data(d)
    #time.sleep(0.02)
