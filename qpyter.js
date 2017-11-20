require.undef('qpyter');

define('qpyter', ["jupyter-js-widgets", "webqt"], function(widgets, WebQt) {

    var QpyterView = widgets.DOMWidgetView.extend({

        initialize: function (parameters) {
            QpyterView.__super__.initialize.apply(this, [parameters]);
            this.model.on('msg:custom', this.onMsg, this);
            
            // For some reason this is never called, so we rely on a separate message
            // to respond to image updates.
            //this.model.on('change:image_data', this.imageChanged, this);
        },
        
        render: function() {
            this.image = document.createElement('img');
            this.el.append(this.image);
            this.qtwidget = WebQt.WebQtWidget(this, this.image);
            // initial image update
            this.imageChanged();
        },
        
        onMsg: function(msg) {
            this.imageChanged();
        },

        imageChanged: function() {
            var b = new Blob([this.model.get('image_data').buffer]);
            this.url = URL.createObjectURL(b);
            this.onRecv(this.url); // sends image to qt widget
        },

        remove: function() {
            // Inform Python that the widget has been removed.
            this.send({event_type: 'closed'});
        },
    });

    return {
        QpyterView: QpyterView
    };
});
