require.undef('qpyter');

define('qpyter', ["jupyter-js-widgets"], function(widgets) {

    var QpyterView = widgets.DOMWidgetView.extend({

        initialize: function (parameters) {
            QpyterView.__super__.initialize.apply(this, [parameters]);
            this.model.on('msg:custom', this.on_msg, this);
            
            // For some reason this is never called, so we rely on a separate message
            // to respond to image updates.
            this.model.on('change:image_data', this.image_changed, this);
        },
            
        render: function() {
            this.image = document.createElement('img');
//             this.image.onload = this.resize_image.bind(this);
            //this.image.src = "http://localhost:8888/static/base/images/logo.png";
//             this.image.style = "border: 3px solid #F00; width: 200px; height: 200px;";
            this.el.append(this.image);
        },
        
        on_msg: function(msg) {
            var b = new Blob([this.model.get('image_data').buffer]);
            this.url = URL.createObjectURL(b);
            this.image.src = this.url;
        },

        image_changed: function() {
            console.log("image data changed");
            console.log(self.model.get('image_data'));
        },
        
//         resize_image: function() {
//             console.log(this);
//             console.log(this.image);
//             
//             this.image.width = this.image.naturalWidth;
//             this.image.height = this.image.naturalHeight;
//             console.log(this.image.height, this.image.naturalHeight);
//         },
//         
        remove: function() {
            // Inform Python that the widget has been removed.
            this.send({
                msg_type: 'status',
                contents: 'removed'
            });
        },
    });

    return {
        QpyterView: QpyterView
    };
});
