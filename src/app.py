import logging
from src.core.logger import configure_logging

class Application:
    def run(self):
        configure_logging()
        logging.getLogger(__name__).info("ORB Behavior Atlas started.")
