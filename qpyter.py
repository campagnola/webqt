import os
from IPython.display import display, Javascript
import ipywidgets as widgets
from traitlets import Bytes, Unicode


# Send js widget definition to the browser
for jsfile in ['webqt.js', 'qpyter.js']:
    jsfile = os.path.join(os.path.dirname(__file__), jsfile)
    js = open(jsfile, 'r').read()
    display(Javascript(js))


class QpyterWidget(widgets.DOMWidget):
    _view_name = Unicode('QpyterView').tag(sync=True)
    _view_module = Unicode('qpyter').tag(sync=True)
    image_data = Bytes('').tag(sync=True)
    
    def __init__(self, *args, **kwds):
        widgets.DOMWidget.__init__(self, *args, **kwds)
        self.on_msg(self.msg_received)

    def msg_received(self, widget, content, buffers):
        if content.get('msg_type') == 'status' and content.get('contents') == 'removed':
            # widget was removed from notebook
            print("Goodbye!")
            