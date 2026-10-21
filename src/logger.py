"""Centralized Application Logging """
import logging 
_configured = False
APP_NAME = "Deep Agent"

def configure_logging(level: int | str =logging.INFO) ->None: 
    global _configured
    if _configured:
        return
    # Root at warning quiets all third Party loggers by default 
    logging.basicConfig(level=logging.WARNING, format= "%(asctime)s %(name)s %(levelname)s %(message)s")
    logging.getLogger(APP_NAME).setLevel(level)
    _configured = True

def get_logger(name: str | None = None)-> logging.Logger:
    "Return the app logger, or a named child of it (pass: __name__)"
    configure_logging()
    if not name or name ==APP_NAME:
        return logging.getLogger(APP_NAME)
    if name.startswith(f"{APP_NAME}."):
        name = name.removeprefix(f"{APP_NAME}.")
    return logging.getLogger(APP_NAME).getChild(name)