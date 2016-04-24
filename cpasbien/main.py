import cookielib
import re
import traceback
import urllib2
import urllib
import unicodedata

from bs4 import BeautifulSoup
from couchpotato import fireEvent
from couchpotato.core.helpers.variable import getTitle, tryInt, possibleTitles
from couchpotato.core.logger import CPLog
from couchpotato.core.helpers.encoding import simplifyString, tryUrlencode
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media.movie.providers.base import MovieProvider
from couchpotato.core.media._base.searcher.main import Searcher

log = CPLog(__name__)


class Cpasbien(TorrentProvider, MovieProvider):
    cpasbienroot = 'http://www.cpasbien.io/'
    urls = {
        'test': cpasbienroot,
        'search': cpasbienroot + 'recherche/',
        'download': cpasbienroot + 'telechargement/%s'
    }

    class NotLoggedInHTTPError(urllib2.HTTPError):
        def __init__(self, url, code, msg, headers, fp):
            urllib2.HTTPError.__init__(self, url, code, msg, headers, fp)

    class PTPHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            log.debug("302 detected; redirected to %s" % headers['Location'])
            if (headers['Location'] != 'login.php'):
                return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
            else:
                raise Cpasbien.NotLoggedInHTTPError(req.get_full_url(), code, msg, headers, fp)

    def _search(self, movie, quality, results):

		  # Cookie login
        #if not self.last_login_check and not self.login():
        #    pass
        #    return

        TitleStringReal = (getTitle(movie['info']) + ' ' + simplifyString(quality['identifier'] )).replace('-',' ').replace(' ',' ').replace(' ',' ').replace(' ',' ').encode("utf8")
        self._searchOnTitle(TitleStringReal, movie, quality, results)

        if not results:
            media_title = fireEvent('library.query', movie, include_year = False, single = True)

            for title in possibleTitles(media_title):
                self._searchOnTitle(title, movie, quality, results)

    def getEncodedString(self, s, encoding='utf-8'):
        if isinstance(s, str):
            try:
                return unicode(s).encode(encoding)
            except UnicodeDecodeError:
                return unicode(s, 'cp1252').encode(encoding)
        elif isinstance(s, unicode):
            return s.encode(encoding)
        else:
            return s

    def _searchOnTitle(self, title, movie, quality, results):
        try:
            URL = (self.urls['search']).encode('UTF8')
            URL=unicodedata.normalize('NFD',unicode(URL,"utf8","replace"))
            URL=URL.encode('ascii','ignore')
            URL = urllib2.quote(URL.encode('utf8'), ":/?=")

            values = {
              'champ_recherche' : self.getEncodedString(title)
            }

            data_tmp = urllib.urlencode(values)
            req = urllib2.Request(URL, data_tmp, headers={'User-Agent' : "Mozilla/5.0"} )
            searcher = Searcher()
            data = urllib2.urlopen(req )
            id = 1000

            if data:
                try:
                    html = BeautifulSoup(data)
                    lin=0
                    erlin=0
                    resultdiv=[]
                    while erlin==0:
                        try:
                            classlin='ligne'+str(lin)
                            resultlin=html.findAll(attrs = {'class' : [classlin]})
                            if resultlin:
                                for ele in resultlin:
                                    resultdiv.append(ele)
                                lin+=1
                            else:
                                erlin=1
                        except:
                            erlin=1
                    for result in resultdiv:
                        try:
                            new = {}
                            name = result.findAll(attrs = {'class' : ["titre"]})[0].text
                            testname=searcher.correctName(name, movie['title'])
                            if testname==0:
                                continue
                            detail_url = result.find("a")['href']
                            tmp = detail_url.split('/')[-1].replace('.html','.torrent')
                            url_download = (self.urls['download'] % tmp)
                            size = result.findAll(attrs = {'class' : ["poid"]})[0].text
                            seeder = self.getEncodedString(result.findAll(attrs = {'class' : ["seed_ok"]})[0].text)
                            leecher = result.findAll(attrs = {'class' : ["down"]})[0].text
                            age = '1'

                            verify = getTitle(movie['info']).split(' ')
                            add = 1

                            for verify_unit in verify:
                                if (name.lower().find(verify_unit.lower()) == -1) :
                                    add = 0

                            def extra_check(item):
                                return True

                            if add == 1:

                                new['id'] = id
                                new['name'] = self.getEncodedString(name.strip())
                                new['url'] = url_download
                                new['detail_url'] = detail_url

                                new['size'] = self.parseSize(self.getEncodedString(size))
                                new['age'] = self.ageToDays(age)
                                new['seeders'] = tryInt(seeder)
                                new['leechers'] = tryInt(leecher)
                                new['extra_check'] = extra_check
                                new['download'] = self.loginDownload

                                #new['score'] = fireEvent('score.calculate', new, movie, single = True)
                                #log.error('score')
                                #log.error(new['score'])

                                results.append(new)
                                id = id+1

                        except:
                            log.error('Failed parsing cPASbien: %s', traceback.format_exc())

                except AttributeError:
                    log.debug('No search results found.')
            else:
                log.debug('No search results found.')
        except UnicodeEncodeError, e:
            s = str(e)



    def ageToDays(self, age_str):
        age = 0
        age_str = age_str.replace('&nbsp;', ' ')

        regex = '(\d*.?\d+).(sec|heure|jour|semaine|mois|ans)+'
        matches = re.findall(regex, age_str)
        for match in matches:
            nr, size = match
            mult = 1
            if size == 'semaine':
                mult = 7
            elif size == 'mois':
                mult = 30.5
            elif size == 'ans':
                mult = 365

            age += tryInt(nr) * mult

        return tryInt(age)

    def login(self):

        cookieprocessor = urllib2.HTTPCookieProcessor(cookielib.CookieJar())
        opener = urllib2.build_opener(cookieprocessor, Cpasbien.PTPHTTPRedirectHandler())
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko)'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'fr-fr,fr;q=0.5'),
            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
            ('Keep-Alive', '115'),
            ('Connection', 'keep-alive'),
            ('Cache-Control', 'max-age=0'),
        ]

        try:
            response = opener.open(self.cpasbienroot, tryUrlencode({'url': '/'}))
        except urllib2.URLError as e:
            log.error('Login to cPASbien failed: %s' % e)
            return False

        if response.getcode() == 200:
            log.debug('Login HTTP cPASbien status 200; seems successful')
            self.last_login_check = opener
            return True
        else:
            log.error('Login to cPASbien failed: returned code %d' % response.getcode())
            return False


    def loginDownload(self, url = '', nzb_id = ''):
        values = {
          'url' : '/'
        }
        data_tmp = urllib.urlencode(values)
        req = urllib2.Request(url, data_tmp, headers={'User-Agent' : "Mozilla/5.0"} )

        try:
            if not self.last_login_check and not self.login():
                log.error('Failed downloading from %s', self.getName())
            return urllib2.urlopen(req).read()
        except:
            log.error('Failed downloading from %s: %s', (self.getName(), traceback.format_exc()))

    def download(self, url = '', nzb_id = ''):
        if not self.last_login_check and not self.login():
            return

        values = {
          'url' : '/'
        }
        data_tmp = urllib.urlencode(values)
        req = urllib2.Request(url, data_tmp, headers={'User-Agent' : "Mozilla/5.0"} )

        try:
            return urllib2.urlopen(req).read()
        except:
            log.error('Failed downloading from %s: %s %s', (self.getName(), url, traceback.format_exc()))

