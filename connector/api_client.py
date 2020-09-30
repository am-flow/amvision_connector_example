import logging
import time

import requests
import slumber

log = logging.getLogger(__name__)


class APISession(requests.Session):
    """Logging wrapper around requests session"""
    def request(self, method, url, data=None, params=None, files=None, headers=None):
        start = time.time()
        resp = super().request(method, url, data=data, params=params, files=files, headers=headers)
        dur = int(1000 * (time.time() - start))
        log.info("[AM-Vision API] %s %s %s %dms", method, url, resp.status_code, dur)
        if 400 <= resp.status_code <= 499:
            log.warning("AMvision Error message: %s", resp.content)
        return resp


class APIClient(slumber.API):
    def __init__(self, url, token):
        session = APISession()
        super().__init__(url, session=session)
        self._store['session'].auth = None
        self._store['session'].headers['Authorization'] = "Token " + token