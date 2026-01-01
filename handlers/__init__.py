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
from .douyindl import register as douyindl_register
from .moderation import register as moderation_register
from .ai import register as ai_register
from .add import register as add_register
from .textfun import register as textfun_register
from .groupmanage import register as groupmanage_register
from .weather import register as weather_register
from .sticker import register as sticker_register
from .quotly import register as quotly_register 
from .admins import register as admins_register
from .restart import register as restart_register

def load_handlers(kiyoshi):
    add_register(kiyoshi)
    quotly_register(kiyoshi)
    restart_register(kiyoshi)
    admins_register(kiyoshi)
    sticker_register(kiyoshi)
    weather_register(kiyoshi)
    groupmanage_register(kiyoshi)
    ping_register(kiyoshi)
    textfun_register(kiyoshi)
    moderation_register(kiyoshi)
    ai_register(kiyoshi)
    qr_register(kiyoshi)
    douyindl_register(kiyoshi)
    dm_register(kiyoshi)
    afk_register(kiyoshi)
    network_register(kiyoshi)
    id_register(kiyoshi)
    info_register(kiyoshi)
    speedtest_register(kiyoshi)
    menu_register(kiyoshi)
    alive_register(kiyoshi)
