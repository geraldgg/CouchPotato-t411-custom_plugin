from bs4 import BeautifulSoup
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.helpers.encoding import simplifyString, tryUrlencode
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media.movie.providers.base import MovieProvider
from couchpotato.core.media._base.searcher.main import Searcher
import cookielib
import re
import traceback
import urllib2, urllib
from StringIO import StringIO
import gzip, time

log = CPLog(__name__)


class T411(TorrentProvider, MovieProvider):
    t411root = 'http://www.t411.ch'

    urls = {
        'test': t411root+'/',
        'detail': t411root+'/torrents/?id=%s',
        'search': t411root+'/torrents/search/?',
        'download': t411root+'/torrents/download/?id=%s',
        'login': t411root+'/users/login/'
    }

    http_time_between_calls = 1 #seconds
    cat_backup_id = None
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    class NotLoggedInHTTPError(urllib2.HTTPError):
        def __init__(self, url, code, msg, headers, fp):
            urllib2.HTTPError.__init__(self, url, code, msg, headers, fp)

    class PTPHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            log.debug("302 detected; redirected to %s" % headers['Location'])
            if (headers['Location'] != 'login.php'):
                return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
            else:
                raise T411.NotLoggedInHTTPError(req.get_full_url(), code, msg, headers, fp)

    def getSearchParams(self, movie, quality):
        results = []
        MovieTitles = movie['info']['titles']
        moviequality = simplifyString(quality['identifier'])
        moviegenre = movie['info']['genres']
        if 'Animation' in moviegenre:
            subcat=455
        elif 'Documentaire' in moviegenre or 'Documentary' in moviegenre:
            subcat=634
        else:    
            subcat=631
        if moviequality in ['720p']:
            qualpar="&term%5B17%5D%5B%5D=541&term%5B17%5D%5B%5D=542&term%5B17%5D%5B%5D=719&term%5B17%5D%5B%5D=1160&term%5B17%5D%5B%5D=722&term%5B7%5D%5B%5D=15&term%5B7%5D%5B%5D=12&term%5B7%5D%5B%5D=1175"
        elif moviequality in ['1080p']:
            qualpar="&term%5B17%5D%5B%5D=541&term%5B17%5D%5B%5D=542&term%5B17%5D%5B%5D=719&term%5B17%5D%5B%5D=1160&term%5B17%5D%5B%5D=722&term%5B7%5D%5B%5D=16&term%5B7%5D%5B%5D=1162&term%5B7%5D%5B%5D=1174"
        elif moviequality in ['dvd-r','dvdr']:
            qualpar="&term%5B17%5D%5B%5D=541&term%5B17%5D%5B%5D=542&term%5B17%5D%5B%5D=719&term%5B17%5D%5B%5D=1160&term%5B17%5D%5B%5D=722&term%5B7%5D%5B%5D=13&term%5B7%5D%5B%5D=14"
        elif moviequality in ['br-disk']:
            qualpar="&term%5B17%5D%5B%5D=541&term%5B17%5D%5B%5D=542&term%5B17%5D%5B%5D=719&term%5B17%5D%5B%5D=1160&term%5B17%5D%5B%5D=722&term%5B7%5D%5B%5D=1171&term%5B7%5D%5B%5D=17"
        else:
            qualpar="&term%5B17%5D%5B%5D=541&term%5B17%5D%5B%5D=542&term%5B17%5D%5B%5D=719&term%5B17%5D%5B%5D=1160&term%5B17%5D%5B%5D=722&term%5B7%5D%5B%5D=8&term%5B7%5D%5B%5D=9&term%5B7%5D%5B%5D=10&term%5B7%5D%5B%5D=11&term%5B7%5D%5B%5D=18&term%5B7%5D%5B%5D=19"
        if quality['custom']['3d']==1:
            qualpar=qualpar+"&term%5B9%5D%5B%5D=24&term%5B9%5D%5B%5D=23"
            
        for MovieTitle in MovieTitles:
            try:
                TitleStringReal = str(MovieTitle.encode("latin-1").replace('-',' '))
            except:
                continue
            try:
                results.append(urllib.urlencode( {'search': TitleStringReal, 'cat' : 210, 'submit' : 'Recherche', 'subcat': subcat } ) + qualpar)
                results.append(urllib.urlencode( {'search': simplifyString(unicode(TitleStringReal,"latin-1")), 'cat' : 210, 'submit' : 'Recherche', 'subcat': subcat } ) + qualpar)
            except:
                continue
        
        return results

    def _searchOnTitle(self, title, movie, quality, results):

        # test the new title and search for it if valid
        newTitle = self.getFrenchTitle(title, str(movie['info']['year']))
        request = ''
        if isinstance(title, str):
            title = title.decode('utf8')
        if newTitle is not None:
            request = (u'(' + title + u')|(' + newTitle + u')').replace(':', '')
        else:
            request = title.replace(':', '')
        request = urllib2.quote(request.encode('iso-8859-1'))

        log.debug('Looking on T411 for movie named %s or %s' % (title, newTitle))
        url = self.urls['search'] + "search=%s %s" % (request, self.acceptableQualityTerms(quality))
        data = self.getHTMLData(url)

        log.debug('Received data from T411')
        if data:
            log.debug('Data is valid from T411')
            html = BeautifulSoup(data)

            try:
                result_table = html.find('table', attrs = {'class':'results'})
                if not result_table:
                    log.debug('No table results from T411')
                    return

                torrents = result_table.find('tbody').findAll('tr')
                for result in torrents:
                    idt = result.findAll('td')[2].findAll('a')[0]['href'][1:].replace('torrents/nfo/?id=','')
                    release_name = result.findAll('td')[1].findAll('a')[0]['title']
                    words = title.lower().replace(':',' ').split()
                    if self.conf('ignore_year'):
                        index = release_name.lower().find(words[-1] if words[-1] != 'the' else words[-2]) + len(words[-1] if words[-1] != 'the' else words[-2]) +1
                        index2 = index + 7
                        if not str(movie['info']['year']) in release_name[index:index2]:
                            release_name = release_name[0:index] + '(' + str(movie['info']['year']) + ').' + release_name[index:]
                    if 'the' not in release_name.lower() and (words[-1] == 'the' or words[0] == 'the'):
                        release_name = 'the.' + release_name
                    if 'multi' in release_name.lower():
                        release_name = release_name.lower().replace('truefrench','').replace('french','')
                    age = result.findAll('td')[4].text
                    results.append({
                        'id': idt,
                        'name': self.replaceTitle(release_name, title, newTitle),
                        'url': self.urls['download'] % idt,
                        'detail_url': self.urls['detail'] % idt,
						'age': age,
                        'size': self.parseSize(str(result.findAll('td')[5].text)),
                        'seeders': result.findAll('td')[7].text,
                        'leechers': result.findAll('td')[8].text,
                    })

            except:
                log.error('Failed to parse T411: %s' % (traceback.format_exc()))

    def _search(self, movie, quality, results):
        # Cookie login
        if not self.last_login_check and not self.login():
            return
        searchStrings= self.getSearchParams(movie,quality)
        lastsearch=0
        searcher = Searcher()

        for searchString in searchStrings:
            actualtime=int(time.time())
            if actualtime-lastsearch<10:
                timetosleep= 10-(actualtime-lastsearch)
                time.sleep(timetosleep)
            URL = self.urls['search']+searchString
                
            r = self.opener.open(URL)   
            soup = BeautifulSoup( r, "html.parser" )
            if soup.find('table', attrs = {'class':'results'}):
                resultdiv = soup.find('table', attrs = {'class':'results'}).find('tbody')
            else:
                continue
            if resultdiv:
                try:   
                    for result in resultdiv.findAll('tr'):
                        try:
                            categorie = result.findAll('td')[0].findAll('a')[0]['href'][result.findAll('td')[0].findAll('a')[0]['href'].find('='):]
                            insert = 0
                        
                            if categorie == '=631':
                                insert = 1
                            if categorie == '=455':
                                insert = 1
                            if categorie == '=634':
                                insert = 1
                         
                            if insert == 1 :
                         
                                new = {}
        
                                idt = result.findAll('td')[2].findAll('a')[0]['href'][1:].replace('torrents/nfo/?id=','')
                                name = result.findAll('td')[1].findAll('a')[0]['title']
                                testname=searcher.correctName(name,movie['title'])
                                if not testname:
                                    continue
                                url = (self.urls['download'] % idt)
                                detail_url = (self.urls['detail'] % idt)
                                leecher = result.findAll('td')[8].text
                                size = result.findAll('td')[5].text
                                age = result.findAll('td')[4].text
                                seeder = result.findAll('td')[7].text
        
                                def extra_check(item):
                                    return True
        
                                new['id'] = idt
                                new['name'] = name + ' french'
                                new['url'] = url
                                new['detail_url'] = detail_url
                                new['size'] = self.parseSize(str(size))
                                new['age'] = self.ageToDays(str(age))
                                new['seeders'] = tryInt(seeder)
                                new['leechers'] = tryInt(leecher)
                                new['extra_check'] = extra_check
                                new['download'] = self.download

                                log.debug("url='%s'"%str(url))
                                results.append(new)
    
                        except:
                            log.error('Failed parsing T411: %s', traceback.format_exc())
    
                except AttributeError:
                    log.debug('No search results found.')
            else:
                log.debug('No search results found.')

    def ageToDays(self, age_str):
        age = 0
        age_str = age_str.replace('&nbsp;', ' ')
        regex = '(\d*.?\d+).(sec|heure|heures|jour|jours|semaine|semaines|mois|ans|an)+'
        matches = re.findall(regex, age_str)
        for match in matches:
            nr, size = match
            mult = 0
            if size in ('jour','jours'):
                mult = 1
            if size in ('semaine','semaines'):
                mult = 7
            elif size == 'mois':
                mult = 30
            elif size in ('ans','an'):
                mult = 365

            age += tryInt(nr) * mult

        return tryInt(age)

    def login(self):
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko)'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'fr-fr,fr;q=0.5'),
            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
            ('Keep-Alive', '115'),
            ('Connection', 'keep-alive'),
            ('Cache-Control', 'max-age=0'),
        ]

        try:
            response = self.opener.open(self.urls['login'], self.getLoginParams())
        except urllib2.URLError as e:
            log.error('Login to T411 failed: %s' % e)
            return False

        if response.getcode() == 200:
            log.debug('Login HTTP T411 status 200; seems successful')
            self.last_login_check = self.opener
            return True
        else:
            log.error('Login to T411 failed: returned code %d' % response.getcode())
            return False

    def getLoginParams(self):
        return tryUrlencode({
             'login': self.conf('username'),
             'password': self.conf('password'),
             'remember': '1',
             'url': '/'
        })
        
        
    def download(self, url = '', nzb_id = ''):
        if not self.last_login_check and not self.login():
            return
        try:
            request = urllib2.Request(url)

            log.debug('Reading url %s'%url)
            response = self.last_login_check.open(request)
            # unzip if needed
            if response.info().get('Content-Encoding') == 'gzip':
                log.debug("gzip content")
                buf = StringIO(response.read())
                f = gzip.GzipFile(fileobj = buf)
                data = f.read()
                f.close()
            else:
                log.debug("not gziped")
                data = response.read()
            log.debug("closing")
            response.close()
            return data
        except Exception, e:
            log.error(str(e))
            return 'try_next'

    def acceptableQualityTerms(self, quality):
        """
        This function retrieve all the acceptable terms for a quality (eg hdrip and bdrip for brrip)
        Then it creates regex accepted by t411 to search for one of this term
        t411 have to handle alternatives as OR and then the regex is firstAlternative|secondAlternative

        In alternatives, there can be "doubled terms" as "br rip" or "bd rip" for brrip
        These doubled terms have to be handled as AND and are then (firstBit&secondBit)
        """
        alternatives = quality.get('alternative', [])
        # first acceptable term is the identifier itself
        acceptableTerms = [quality['identifier']]
        log.debug('Requesting alternative quality terms for : ' + str(acceptableTerms) )
        # handle single terms
        acceptableTerms.extend([ term for term in alternatives if type(term) == type('') ])
        # handle doubled terms (such as 'dvd rip')
        doubledTerms = [ term for term in alternatives if type(term) == type(('', '')) ]
        acceptableTerms.extend([ '('+first+'%26'+second+')' for (first,second) in doubledTerms ])
        # join everything and return
        log.debug('Found alternative quality terms : ' + str(acceptableTerms).replace('%26', ' '))
        return '|'.join(acceptableTerms)

    def replaceTitle(self, releaseNameI, titleI, newTitleI):
        """
        This function is replacing the title in the release name by the old one,
        so that couchpotato recognise it as a valid release.
        """

        if newTitleI is None: # if the newTitle is empty, do nothing
            return releaseNameI
        else:
            # input as lower case
            releaseName = releaseNameI.lower()
            title = titleI.lower()
            newTitle = newTitleI.lower()
            #log.debug('Replacing -- ' + newTitle.decode('ascii', errors='replace') + ' -- in the release -- ' + releaseName.decode('ascii', errors='replace') + ' -- by the original title -- ' + title.decode('ascii', errors='replace'))
            separatedWords = []
            for s in releaseName.split(' '):
                separatedWords.extend(s.split('.'))
            # test how far the release name corresponds to the original title
            index = 0
            while separatedWords[index] in title.split(' '):
                index += 1
            # test how far the release name corresponds to the new title
            newIndex = 0
            while separatedWords[newIndex] in newTitle.split(' '):
                newIndex += 1
            # then determine if it correspoinds to the new title or old title
            if index >= newIndex:
                # the release name corresponds to the original title. SO no change needed
                log.debug('The release name is already corresponding. Changed nothing.')
                return releaseNameI
            else:
                # otherwise, we replace the french title by the original title
                finalName = [title]
                finalName.extend(separatedWords[newIndex:])
                newReleaseName = ' '.join(finalName)
                log.debug('The new release name is : ' + newReleaseName)
                return newReleaseName

    def getFrenchTitle(self, title, year):
        """
        This function uses TMDB API to get the French movie title of the given title.
        """

        url = "https://api.themoviedb.org/3/search/movie?api_key=0f3094295d96461eb7a672626c54574d&language=fr&query=%s" % title
        log.debug('Looking on TMDB for French title of : ' + title)
        #data = self.getJsonData(url, decode_from = 'utf8')
        data = self.getJsonData(url)
        try:
            if data['results'] != None:
                for res in data['results']:
                    yearI = res['release_date']
                    if year in yearI:
                        break
                frTitle = res['title'].lower()
                if frTitle == title:
                    log.debug('TMDB report identical FR and original title')
                    return None
                else:
                    log.debug(u'API TMDB found a french title => ' + frTitle)
                    return frTitle
            else:
                log.debug('TMDB could not find a movie corresponding to : ' + title)
                return None
        except:
            log.error('Failed to parse TMDB API: %s' % (traceback.format_exc()))
