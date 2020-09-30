import logging
import sys

from .base import BaseConnector, base_parser
from .importer import Importer

log = logging.getLogger(__name__)

class DemoConnector(BaseConnector):
    """Demonstration connector."""

    def __init__(self, *args, print_fn=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_handlers({
            'batch.started': self.on_event,
            'batch.ended': self.on_event,
            'batch.reset': self.on_event,
            'scan.captured': self.on_event,
            'scan.rejected': self.on_event,
            'scan.assigned': self.on_event,
            'scan.unassigned': self.on_event,
        })
        self.print_fn = print_fn
        self.importer = Importer(self.api)
        self.importer.one_time_imports(self.print_fn)

    def synchronize(self):
        log.info("Synchronizing")
        if self.print_fn:
            self.importer.import_all(self.print_fn)

    def on_event(self, event, data):
        log.info("Got event %s with data %s", event, str(data))


if __name__ == '__main__':
    """Demo connector."""
    parser = base_parser()
    parser.add_argument(
        '-p', '--prints', type=str,
        help='path to yaml file with prints definition',
    )
    args = parser.parse_args()
    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO,
        format='[%(asctime)s: %(levelname)s] %(message)s'
    )
    conn = DemoConnector(
        args.ip, args.port, args.amv_url, args.amv_token, 
        single_sync=args.single_sync, interval=args.interval, 
        print_fn=args.prints
    )
    conn.run()


