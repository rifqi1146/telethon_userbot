from .ping import register as ping_register


def load_handlers(app):
    ping_register(app)

