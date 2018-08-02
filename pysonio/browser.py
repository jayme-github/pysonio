import os
import stat
import logging
import re
from requests import Session
from http.cookiejar import LWPCookieJar
from bs4 import BeautifulSoup

import pysonio.attendance as attendance

DEFAULT_USERAGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'  # noqa: E501
RE_EMPLOYEEID = re.compile(r'\/staff\/details\/(\d+$)')


class Browser(object):
    def __init__(self, url=None, username=None, password=None):
        self._url = url
        self._username = username
        self._password = password
        self._csrf = None
        self._employee_id = None
        self.logger.info('Initialized with user: %s', self._username)
        self.session = Session()
        self.set_useragent()

        cookie_file = os.path.expanduser('~/.pysonio.lwp')
        self.session.cookies = LWPCookieJar(cookie_file)
        if not os.path.exists(cookie_file):
            # initialize new cookie file
            self.logger.info('Creating new cookie file: "%s"', cookie_file)
            self._save_cookies()
            os.chmod(cookie_file,  stat.S_IRUSR | stat.S_IWUSR)
        else:
            # load cookies
            self.logger.info('Loading cookies from file: "%s"', cookie_file)
            self.session.cookies.load(ignore_discard=True)

    @property
    def logger(self):
        if not getattr(self, '_logger', False):
            name = '.'.join((__name__, self.__class__.__name__))
            self._logger = logging.getLogger(name)
        return self._logger

    def set_useragent(self, useragent=DEFAULT_USERAGENT):
        self.session.headers.update({'User-Agent': useragent})
        self.logger.debug('User-Agent set to: "%s"', useragent)

    def set_csrf_token(self, token):
        self.session.headers.update({'x-csrf-token': token})

    def _save_cookies(self):
        self.logger.debug('Saving cookies to disk')
        return self.session.cookies.save(ignore_discard=True)

    def _hash_cookies(self):
        ''' Returns the hash of a list of hashes from sorted repr() of every
            cookie in jar as LWPCookieJar does not change it's hash when
            cookies change.
        '''
        return hash(frozenset([hash(c) for c in sorted([repr(c) for c in self.session.cookies])]))  # noqa: E501

    def get(self, url, **kwargs):
        self.logger.debug('GET "%s", kwargs: "%s"', url, kwargs)
        h = self._hash_cookies()
        if 'allow_redirects' not in kwargs:
            kwargs['allow_redirects'] = False
        r = self.session.get(url, **kwargs)

        if url != self._url + '/login/index' and \
                r.status_code in (301, 302) and \
                r.headers.get('Location') == self._url + '/login/index':
            # Session expired, login again
            self.logger.warning(
                    'Session expired while GET, trying to login again'
            )
            if self.login():
                self.logger.info('Login during GET: success!')
                return self.get(url, **kwargs)
            else:
                self.logger.error('Login failed during GET')

        # Will raise HTTPError on 4XX client error or 5XX server error response
        r.raise_for_status()
        if h != self._hash_cookies():
            # Cookies have changed
            self._save_cookies()

        return r

    def post(self, url, data=None, **kwargs):
        self.logger.debug(
                'POST "%s", data: "%s", kwargs: "%s"', url, data, kwargs
        )
        h = self._hash_cookies()
        if 'allow_redirects' not in kwargs:
            kwargs['allow_redirects'] = False
        r = self.session.post(url, data, **kwargs)

        if url != self._url + '/login/index' and \
                r.status_code in (301, 302) and \
                r.headers.get('Location') == self._url + '/login/index':
            self.logger.warning(
                    'Session expired while POST, trying to login again'
            )
            if self.login():
                self.logger.info('Login during POST: success!')
                return self.post(url, data, **kwargs)
            else:
                self.logger.error('Login failed during POST')

        # Will raise HTTPError on 4XX client error or 5XX server error response
        r.raise_for_status()
        if h != self._hash_cookies():
            # Cookies have changed
            self._save_cookies()

        return r

    @staticmethod
    def _handle_emailtoken():  # pylint:disable=unused-argument
        ''' Called when Personio requires email token...
        Asks the user to enter the token.

        Args:
            message: Optional.

        Returns:
            A string containing the token.
        '''
        print('Personio requires an E-Mail token...')
        email_token = input('Please enter the code sent to you via E-Mail: ')
        return email_token

    def login(self):
        def _logged_in(r):
            if r.status_code in (301, 302):
                r = self.get(self._url + '/staff/me', allow_redirects=True)
                # Store employee id
                m = RE_EMPLOYEEID.search(r.url)
                if m:
                    self._employee_id = int(m.group(1))
                    self.logger.info('Employee ID: %d', self._employee_id)
                else:
                    return False

            if 'logout' in r.text:
                self.logger.debug('Login successful')
                return True

            return False

        url = self._url + '/login/index'
        if not self._csrf:
            r = self.get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')
            attrs = {
                'name': '_token',
                'type': 'hidden'
            }
            self._csrf = soup.find('input', attrs=attrs).get('value')
            self.set_csrf_token(self._csrf)
            self.logger.debug('CSRF Token: %s', self._csrf)
            del(soup)

        data = {
            '_token': self._csrf,
            'email': self._username,
            'password': self._password
        }
        r = self.post(url, data)
        if _logged_in(r):
            return True

        # FIXME: Check if token auth is required
        token_url = self._url + '/login/token-auth'  # noqa: E501
        soup = BeautifulSoup(r.content, 'html.parser')

        attrs = {
            'action': token_url,
            'method': 'POST'
        }
        email_token_form = soup.find('form', attrs=attrs)
        if email_token_form:
            self.logger.info('Token auth is required')
            email_token = self._handle_emailtoken()
            self.logger.info('E-Mail token: %s', email_token)
            data = {
                '_token': self._csrf,
                'token': email_token
            }
            r = self.post(token_url, data)
            if _logged_in(r):
                return True

        return False

    def post_attendance(self, attendance_data):
        if isinstance(attendance_data, attendance.AttendanceRow):
            rows = repr([attendance_data])
        elif isinstance(attendance_data, attendance.AttendanceDay):
            rows = repr(attendance_data)
        else:
            raise ValueError(
                    'attendance_data must be of type AttandenceRow or \
AttendenceDay'
            )

        if self._employee_id is None:
            self.login()

        url = '{}/attendance/update-date/{}'.format(
                self._url, self._employee_id
        )

        data = {
                'rows': rows
        }
        r = self.post(url, data)
        rj = r.json()
        if rj['status'] == 'error':
            self.logger.error(rj['message'])
        return rj
