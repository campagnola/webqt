import os
from IPython.display import display, Javascript
import ipywidgets as widgets
from traitlets import Bytes, Unicode

from webqt import WidgetProxy


# Send js widget definition to the browser
for jsfile in ['webqt.js', 'qpyter.js']:
    jsfile = os.path.join(os.path.dirname(__file__), jsfile)
    js = open(jsfile, 'r').read()
    display(Javascript(js))


class QpyterWidget(widgets.DOMWidget):
    _view_name = Unicode('QpyterView').tag(sync=True)
    _view_module = Unicode('qpyter').tag(sync=True)
    image_data = Bytes('').tag(sync=True)
    
    def __init__(self, widget, **kwds):
        widgets.DOMWidget.__init__(self, **kwds)
        self.widget = widget
        self.proxy = WidgetProxy(widget, self)
        self.on_msg(self.msg_received)

    def send_image(self, data):
        self.image_data = data
        self.send({'action': 'image'})

    def set_callback(self, cb):
        self.event_callback = cb

    def msg_received(self, widget, content, buffers):
        if content.get('event_type') == 'closed':
            # widget was removed from notebook
            pass
        else:
            self.event_callback(content)
            