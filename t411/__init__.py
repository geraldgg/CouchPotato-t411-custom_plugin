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
            'description': 'See <a href="https://t411.li">T411</a>',
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
