import logging

from js import console  # type: ignore[attr-defined]


class ConsoleHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)

            if record.levelno >= logging.ERROR:
                console.error(msg)
            elif record.levelno >= logging.WARNING:
                console.warn(msg)
            elif record.levelno >= logging.INFO:
                console.info(msg)
            else:
                console.debug(msg)
        except Exception:
            self.handleError(record)


# why the heck does python's standard lib use camelCase? :(  I'm just mimicking logging.getLogger ...
def getLogger(name, show_time: bool = False) -> logging.Logger:
    """
    to get a logger in another file that outputs only to the browser javascript console and doesn't insert
    its output into the webpage, simply use:

    from consolelogger import getLogger
    log = getLogger(__name__)
    log.debug. ("This is a log message") # etc.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # set up the logger so it only outputs to the browser's javascript console. Spiffy
    handler = ConsoleHandler()
    if not show_time:
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    else:
        formatter = logging.Formatter("[%(levelname)s %(asctime)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
        handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)

    return logger
