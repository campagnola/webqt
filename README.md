An experiment in running PyQt applications in the browser
---------------------------------------------------------

How it works: a PyQt application runs on a server. The image of its window is sent to your browser to be displayed.
Meanwhile, the browser collects your mouse clicks and key presses and forwards them back to the server.

It's a sweet and easy way to run your application remotely, but comes with some drawbacks:

- Relatively slow user interaction depending on your network latency
- High bandwidth usage
- High overhead relative to a typical web application


Quick test instructions:
------------------------

1. You need a python environment with PyQt>=5.12, pyqtgraph, and websockets installed. With conda, this looks like:

```
$ conda create --name=webqt -c conda-forge python=3 pyqtgraph "pyqt>=5.12" pillow numpy
$ conda activate webqt
$ pip install websockets
```

2. Start a websocket server

```
$ python -i websocket-example.py
```

3. Connnect by loading `webqt.html` in your browser

```
file:///path/to/webqt.html
```
