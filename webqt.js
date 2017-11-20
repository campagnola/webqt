var WebQt = (function () {
    var pub = {};

    pub.WebQtWidget = WebQtWidget;
    function WebQtWidget(socket, image) {
        this.socket = socket;
        socket.onRecv = windowEvent.bind(this);

        this.lastImageUpdate = undefined;
        if( image === undefined ) {
            image = new Image();
        }
        this.image = image;

        function mkMouseEvent(ev, type) {
            o = {'event_type': type, 'x': ev.offsetX, 'y': ev.offsetY, 'screenX': ev.screenX, 'screenY': ev.screenY, 'button': ev.button, 'buttons': ev.buttons, 'altKey': ev.altKey, 'ctrlKey': ev.ctrlKey, 'shiftKey': ev.shiftKey, 'metaKey': ev.metaKey}
            
            if (type == 'wheel') {
                o['deltaY'] = ev.deltaY
                o['deltaX'] = ev.deltaX
            }
            return JSON.stringify(o)
        }
        function onMousePress(ev) {
            this.socket.send(mkMouseEvent(ev, 'mousePress'))
        }
        function onMouseRelease(ev) {
            this.socket.send(mkMouseEvent(ev, 'mouseRelease'))
        }
        function onMouseMove(ev) {
            this.socket.send(mkMouseEvent(ev, 'mouseMove'))
        }
        function onWheel(ev) {
            this.socket.send(mkMouseEvent(ev, 'wheel'))
        }
        
        function mkKeyEvent(ev, type) {
            return JSON.stringify({'event_type': type, 'code': ev['code'], 'key': ev['key'], 'repeat': ev['repeat'], 'altKey': ev.altKey, 'ctrlKey': ev.ctrlKey, 'shiftKey': ev.shiftKey, 'metaKey': ev.metaKey})
        }
        function onKeyDown(ev) {
            this.socket.send(mkKeyEvent(ev, 'keyDown'))
            // This is tricky: maybe we could wait for the server to say 
            // whether it accepted the event, but this will probably make
            // typing very unresponsive.
            ev.stopPropagation()
            ev.preventDefault()
        }
        function onKeyUp(ev) {
            this.socket.send(mkKeyEvent(ev, 'keyUp'))
            ev.stopPropagation()
            ev.preventDefault()
        }
        
        this.image.addEventListener('mousedown', onMousePress.bind(this), false);
        this.image.addEventListener('mouseup', onMouseRelease.bind(this), false);
        this.image.addEventListener('mousemove', onMouseMove.bind(this), false);
        this.image.addEventListener('wheel', onWheel.bind(this), false);
        this.image.addEventListener('keydown', onKeyDown.bind(this), false);
        this.image.addEventListener('keyup', onKeyUp.bind(this), false);
        this.image.ondragstart = function() { return false; };
        this.image.oncontextmenu = function() { return false; };

        
        function windowEvent(imageData) {
            // Called when the socket receives an update from the server
            this.lastImageUpdate = imageData;
        }
        
        function updateImage() {
            if( this.lastImageUpdate == undefined ) {
                return
            }
            image.src = this.lastImageUpdate;
            this.lastImageUpdate = undefined;
        }

        window.setInterval(updateImage.bind(this), 20);
    }

    
    pub.WebSocketAdapter = WebSocketAdapter;
    function WebSocketAdapter(address='ws://127.0.0.1:12345') {
        this.socket = new WebSocket(address);
        this.onRecv = undefined;
        
        function onSocketOpen(ev) {
        }
        
        function onSocketError(err) {
        }
        
        function onSocketMessage(ev) {
            if( this.onRecv === undefined ) {
                return;
            }
            url = URL.createObjectURL(ev.data);
            this.onRecv(url);
        }
        
        this.socket.onopen = onSocketOpen.bind(this);
        this.socket.onerror = onSocketError.bind(this);
        this.socket.onmessage = onSocketMessage.bind(this);
        
        this.send = this.socket.send.bind(this.socket);
    }
    return pub;
})();
