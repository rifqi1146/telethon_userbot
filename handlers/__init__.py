from .ping import register as ping_register
from .speedtest import register as speedtest_register
from .menu import register as menu_register

def load_handlers(app):
    ping_register(app)
    speedtest_register(app)
    menu_register(app)

