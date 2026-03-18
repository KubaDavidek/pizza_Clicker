import logging
import os
from logging.handlers import RotatingFileHandler


def configure_logging(app):
    log_file = os.path.join(os.path.dirname(__file__), 'server.log')
    handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=3, encoding='utf-8')
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)
