from .ping import register as ping_register
from .speedtest import register as speedtest_register
from .menu import register as menu_register
from .alive import register as alive_register
from .info import register as info_register
from .qr import register as qr_register
from .id import register as id_register
from .dm_protect import register as dm_register
from .network import register as network_register 
from .afk import register as afk_register
from .dl import register as douyindl_register

def load_handlers(app):
    ping_register(app)
    qr_register(app)
    douyindl_register(app)
    dm_register(app)
    afk_register(app)
    network_register(app)
    id_register(app)
    info_register(app)
    speedtest_register(app)
    menu_register(app)
    alive_register(app)
