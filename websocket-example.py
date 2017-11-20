

    
        
if __name__ == '__main__':
    import numpy as np
    import PyQt5  # because PyQt4 is broken on my machine
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtGui, QtCore
    
    from websocket_adapter import WebSocketAdapter
    from webqt import WidgetProxy
    
    pg.mkQApp()


    #w = pg.PlotWidget()
    #w.plot(np.random.normal(size=10000), antialias=True)
    #w.addLine(x=0, movable=True)


    
    w = QtGui.QSplitter(QtCore.Qt.Vertical)
    
    plt = pg.PlotWidget()
    plt.plot(np.random.normal(size=100))
    w.addWidget(plt)
    
    import pyqtgraph.console
    console = pg.console.ConsoleWidget(namespace={'pg': pg, 'plt': plt})
    w.addWidget(console)
    
    class MouseTestWidget(QtGui.QWidget):
        def __init__(self, name, accept, focus):
            self.name = name
            self.accept = accept
            QtGui.QWidget.__init__(self)
            self.setMouseTracking(True)
            if focus:
                self.setFocusPolicy(QtCore.Qt.StrongFocus)
        def mousePressEvent(self, ev):
            print("  press:", self.name, ev.pos(), ev.globalPos(), int(ev.button()), int(ev.buttons()))
            ev.setAccepted(self.accept)
        def mouseReleaseEvent(self, ev):
            print("release:", self.name, ev.pos(), ev.globalPos(), int(ev.button()), int(ev.buttons()))
        def mouseMoveEvent(self, ev):
            print("   move:", self.name, ev.pos(), ev.globalPos(), int(ev.button()), int(ev.buttons()))
        def keyPressEvent(self, ev):
            print(" key dn:", self.name, repr(ev.text()), ev.key())
        def keyReleaseEvent(self, ev):
            print(" key up:", self.name, ev.key())
        def focusInEvent(self, ev):
            print("  focus: in", self.name)
        def focusOutEvent(self, ev):
            print("  focus: out", self.name)
        def paintEvent(self, ev):
            p = QtGui.QPainter(self)
            for x in range(0, self.width(), 10):
                p.setPen(pg.mkPen('k'))
                p.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 10):
                p.setPen(pg.mkPen('k'))
                p.drawLine(0, y, self.width(), y)
            p.end()
            
    mtw1 = MouseTestWidget('w1', True, focus=True)
    w.addWidget(mtw1)
            
    mtw2 = MouseTestWidget('w2', False, focus=False)
    mtw2.setParent(mtw1)
    mtw2.move(55, 55)

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
    
    socket = WebSocketAdapter()
    wsp = WidgetProxy(w, socket)
    w.show()
