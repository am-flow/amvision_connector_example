"""Base class for all connectors."""
import logging
import argparse
import sys
import yaml
import functools
import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request

try:
    import bjoern
except ImportError:
    bjoern = None

from .api_client import APIClient

log = logging.getLogger(__name__)

class BaseConnector():
    """Base class for customer connector."""
    def __init__(self, ip, port, amv_url, amv_token, single_sync=False, interval=30):
        # pylint: disable=W0613,R0201
        self.single_sync = single_sync
        self.conn_ip = ip
        self.conn_port = port
        self.api = APIClient(amv_url, amv_token)
        self._endpoint_name = 'hook'
        self._endpoint_url = "http://{}/{}/".format(
            self.conn_ip,
            self.conn_port,
            self._endpoint_name
        )
        self.app = Flask(__name__)
        self.app.add_url_rule(
            rule='/{}/'.format(self._endpoint_name), 
            endpoint=self._endpoint_name,
            view_func=self._on_hook,
            methods=['POST']
        )
        self._scheduler = BackgroundScheduler()
        self._events = [
            'batch.started', 'batch.ended', 'batch.reset', 'scan.captured', 'scan.rejected',
            'scan.assigned', 'scan.reassigned', 'scan.unassigned', 'auth.login_user', 
            'auth.logout_user',
        ]
        self._event_handlers = {}
        self._scheduler.add_job(
            self.synchronize, 'interval', 
            minutes=interval, 
            next_run_time=datetime.datetime.now()+datetime.timedelta(minutes=1)
        )

    def synchronize(self):
        pass

    def _on_hook(self):
        post = request.json
        if 'hook' not in post or 'data' not in post:
            return 'Invalid request', 400
        event = post['hook'].get('event')
        log.info("Received hook for event %s", event)
        if event not in self._event_handlers:
            log.info("No handler registered for event %s", event)
            return '', 404
        else:
            try:
                response = self._event_handlers[event](event, post['data'])
                return response or '', 204
            except Exception:
                log.exception("Error handling hook for event %s", event)
                return 'Server error', 500

    def register_handlers(self, handlers):
        for event, handler in handlers.items():
            if event not in self._events:
                log.error("Invalid event %s, skipping", event)
                continue
            if event in self._event_handlers:
                log.warning("Overwriting existing handler for %s", event)
            log.info("Registering handler for %s", event)
            self.api.webhook.post({
                'event': event,
                'target': self._endpoint_url
            })
            self._event_handlers[event] = handler

    def run(self):
        if self.single_sync:
            return self.synchronize()

        self._scheduler.start()
        if bjoern is not None:
            log.info("Connector running with Bjoern")
            bjoern.run(self.app, host=self.conn_ip, port=self.conn_port)
        else:
            log.info("Connector running with Flask dev server")
            self.app.run(host=self.conn_ip, port=self.conn_port)

def base_parser():
    parser = argparse.ArgumentParser(description='AM-Vision Connector')
    parser.add_argument('ip', type=str, help='ip address to run connector on')
    parser.add_argument('port', type=str, help='port to run connector on')
    parser.add_argument('amv_url', type=str, help='url to AM-Vision API')
    parser.add_argument('amv_token', type=str, help='token for AM-Vision API')
    parser.add_argument(
        '-s', '--single-sync', action='store_true', help='run single sync and exit'
    )
    parser.add_argument(
        '-i', '--interval', type=int, default=30, help='sync interval in minutes'
    )
    return parser
