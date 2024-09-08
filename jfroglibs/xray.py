import requests
import json
import threading
from concurrent.futures import ThreadPoolExecutor

requests.packages.urllib3.disable_warnings()

class Xray:
    '''
    This module provides methods for getting information about a 
    particular Xray instance in an Artifactory cluster.
    '''

    def __init__(self, *, url, token, ssl_verify=True, concurrent_workers=20):
        self.url           = url
        self.token         = token
        self._watches      = {}
        self.ssl_verify    = ssl_verify
        self.concurrent_workers = concurrent_workers
        self.session_storage    = threading.local()
        setattr(self.session_storage, 'session', requests.Session())

    @property
    def watches(self):
        if not self._watches:
            self._watches = self._get_all_watches()
        return self._watches

    def _requests_get(self, url):
        try:
            session = getattr(self.session_storage, 'session', None)
            if session is None:
                session = requests.Session()
                setattr(self.session_storage, 'session', session)
            response = session.get(
                url,
                headers={"Authorization": "Bearer " + self.token},
                verify=self.ssl_verify
            )
        except Exception as ex:
            error = {'errors': '{}'.format(ex)}
            raise ValueError(json.dumps(error, indent=2))

        if response.status_code != requests.codes.ok:
            raise ValueError(response.text)

        return json.loads(response.text)

    def _get_all_watches(self):
        url = self.url + '/xray/api/v2/watches'
        watches = self._requests_get(url)
        new_watches = {}
        for watch in watches:
            new_watches[watch['general_data']['name']] = watch
        return new_watches
