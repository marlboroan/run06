import logging
import logging.__init__ as l_init

# Custom formatter
import os


class SimpleFormatter(logging.Formatter):
    dbg_fmt = "[%(levelname)-8s] --- %(message)-50s (%(filename)s:%(lineno)s) %(funcName)s()"
    info_fmt = "[%(levelname)-8s] --- %(message)-50s"
    err_fmt = "[%(levelname)-8s] --- %(message)-50s %(funcName)s()"

    def __init__(self, fmt=info_fmt):
        logging.Formatter.__init__(self, fmt=fmt)

    def format(self, record):
        # Save the original format configured by the user
        # when the logger formatter was instantiated
        fmt_ori = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno <= logging.DEBUG:
            self._style._fmt = SimpleFormatter.dbg_fmt
        elif logging.WARNING < record.levelno <= logging.CRITICAL:
            self._style._fmt = SimpleFormatter.err_fmt
        else:
            self._style._fmt = SimpleFormatter.info_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)
        # Restore the original format configured by the user
        self._style._fmt = fmt_ori

        return result


def set_level(level):
    __logger.setLevel(level)


def set_level_by_name(level_name):
    set_level(l_init._nameToLevel.get(str(level_name).upper(), l_init.INFO))


def d(msg, *args, **kwargs):
    __logger.debug(msg, stacklevel=2, *args, **kwargs)


def i(msg, *args, **kwargs):
    __logger.info(msg, stacklevel=2, *args, **kwargs)


def w(msg, *args, **kwargs):
    __logger.warning(msg, stacklevel=2, *args, **kwargs)


def e(msg, *args, **kwargs):
    __logger.error(msg, stacklevel=2, *args, **kwargs)


def c(msg, *args, **kwargs):
    __logger.critical(msg, stacklevel=2, *args, **kwargs)


def ex(msg, *args, **kwargs):
    __logger.exception(msg, stacklevel=3, *args, **kwargs)


ARGS_SEPARATOR = "##"
__logger = logging.getLogger(__name__)
__handler = logging.StreamHandler()
set_level_by_name(os.environ.get("DEBUG", l_init.INFO))
__fmt = SimpleFormatter()
__handler.setFormatter(__fmt)
__logger.addHandler(__handler)
