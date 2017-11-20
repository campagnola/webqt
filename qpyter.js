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
            this.el.append(this.image);
            this.qtwidget = WebQt.WebQtWidget(this, this.image);
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
