from .main import t411
from .updater import ST411Updater
from couchpotato.core.logger import CPLog
from couchpotato.core.event import fireEventAsync

log = CPLog(__name__)

def autoload():
    log.info('Checking if new update available')
    update = ST411Updater()

    if update.check() and update.isEnabled():
        if update.doUpdate():
            log.info('T411 update sucessful, Restarting CouchPotato')
            fireEventAsync('app.restart')
    log.debug('load success')
    return t411()

config = [{
    'name': 't411',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'torrent_providers',
            'name': 'T411',
            'description': '<a href="https://t411.ai" target="_blank">T411</a>',
            'icon': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4QMbCQYSe0YliAAAAlRJREFUOMvNkktPE2EARe830+l0pp1O6VMBhQQxIbjAKGiiCwI+mrgRJCRGo4nxP5i4cIOJe/+BJESNhoWRBWJ8bgy1EB6tWqYFS+m7paVMO3Re7gwmLnTHWd3c5OwOcCC497H4f8Lj6O9J9v9P06bwNiR1r4dCLZlcQTdtQkPztsnq4S6ZdHTVtgZRVVmi7ncIADxabnqeJyqDkOsXuY2VYG7+U0e1lNeboLZ1K58jgpiXwWyBsSYRaEujWs6AETcs50aixDeVPkHtbE9o5eJwo1IWiLQE+cM0XH4Phq4EkdzKIrz6AwNnB0AEF77ML6L9kE+p1ZRYlQtM0Ebf6MOr7fQNbjPKxsJfoekakIlj5PYtXBsfA6w2NCkGI8EhtPAsSkshBIfPWyqpZKCQymgUvTh34W6PHf6dTaBShGkS9J7ph6+1FVIiAcrCIJUt4P3sHExCo1Aqo76nwud2AYrcR6lrC6yUyuLV61nAUGFxe3A5eAkGKDQ1HV7RgboURb5QhNthQ1XRoCoKeDsP0AxLGXJlZTVVwun+k0BTgdXpwq4B9BzrRMDvh9vjBS+IsNoFBJw8iN0FQRRgcwgAxURouvNUMSnFb7Z3dWMtU4Dq78DCcgQzL6YBQ0c5l0P4mwSW52FjaITjaaiqCbmhGrrgmSQAMPoyduTzsycPKrv1cfVoL0dSMQrJ76ZJLCYYq0F4p0nsokFzDkXguYToFBf3WMe79Hp55o+Qjk+uu9dWI9dNhu2Frilg7Xnwjp9guSSc3jju+LJ/LTM4Ffn3jO+/wcHiF3wh/My3arJ1AAAAAElFTkSuQmCC',
            'wizard': True,
            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False,
                },
                {
                    'name': 'username',
                    'default': '',
                },
                {
                    'name': 'password',
                    'default': '',
                    'type': 'password',
                },
                {
                    'name': 'ignore_year',
                    'label': 'ignore year',
                    'default': 0,
                    'type': 'bool',
                    'description': 'Will ignore the year in the search results',
                },
                {
                    'name': 'seed_ratio',
                    'label': 'Seed ratio',
                    'type': 'float',
                    'default': 1,
                    'description': 'Will not be (re)moved until this seed ratio is met.',
                },
                {
                    'name': 'seed_time',
                    'label': 'Seed time',
                    'type': 'int',
                    'default': 40,
                    'description': 'Will not be (re)moved until this seed time (in hours) is met.',
                },
                {
                    'name': 'extra_score',
                    'advanced': True,
                    'label': 'Extra Score',
                    'type': 'int',
                    'default': 20,
                    'description': 'Starting score for each release found via this provider.',
                },
                {
                    'name': 'auto-update',
                    'advanced': True,
                    'label': 'Automatic Update',
                    'type': 'bool',
                    'default': 1,
                    'description': 'Automatic update at startup.',
                }
            ],
        },
    ],
}]
