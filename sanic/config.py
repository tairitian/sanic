from sanic.defaultFilter import DefaultFilter
import os
import types

SANIC_PREFIX = 'SANIC_'


DEFAULT_LOG_CONF = {
    'version': 1,
    'filters': {
        'access_filter': {
            '()': DefaultFilter,
            'param': [0, 10, 20]
        },
        'error_filter': {
            '()': DefaultFilter,
            'param': [30, 40, 50]
        }
    },
    'formatters': {
        'simple': {
            'format': '%(asctime)s - (%(name)s)[%(levelname)s]: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'access': {
            'format': '%(asctime)s - [%(levelname)s][%(host)s]: ' +
                      '%(request)s %(message)s %(status)d %(byte)d',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'internal': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filters': ['access_filter'],
            'formatter': 'simple',
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'filename': 'access.log'
        },
        'access': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filters': ['access_filter'],
            'formatter': 'access',
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'filename': 'access.log'
        },
        'error': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filters': ['error_filter'],
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'filename': 'error.log',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'sanic': {
            'level': 'DEBUG',
            'handlers': ['internal', 'error']
        },
        'network': {
            'level': 'DEBUG',
            'handlers': ['access', 'error']
        }
    }
}


class Config(dict):
    def __init__(self, defaults=None, load_env=True):
        super().__init__(defaults or {})
        self.LOGO = """
                 ▄▄▄▄▄
        ▀▀▀██████▄▄▄       _______________
      ▄▄▄▄▄  █████████▄  /                 \\
     ▀▀▀▀█████▌ ▀▐▄ ▀▐█ |   Gotta go fast!  |
   ▀▀█████▄▄ ▀██████▄██ | _________________/
   ▀▄▄▄▄▄  ▀▀█▄▀█════█▀ |/
        ▀▀▀▄  ▀▀███ ▀       ▄▄
     ▄███▀▀██▄████████▄ ▄▀▀▀▀▀▀█▌
   ██▀▄▄▄██▀▄███▀ ▀▀████      ▄██
▄▀▀▀▄██▄▀▀▌████▒▒▒▒▒▒███     ▌▄▄▀
▌    ▐▀████▐███▒▒▒▒▒▐██▌
▀▄▄▄▄▀   ▀▀████▒▒▒▒▄██▀
          ▀▀█████████▀
        ▄▄██▀██████▀█
      ▄██▀     ▀▀▀  █
     ▄█             ▐▌
 ▄▄▄▄█▌              ▀█▄▄▄▄▀▀▄
▌     ▐                ▀▀▄▄▄▀
 ▀▀▄▄▀
"""
        self.REQUEST_MAX_SIZE = 100000000  # 100 megababies
        self.REQUEST_TIMEOUT = 60  # 60 seconds

        if load_env:
            self.load_environment_vars()

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as ke:
            raise AttributeError("Config has no '{}'".format(ke.args[0]))

    def __setattr__(self, attr, value):
        self[attr] = value

    def from_envvar(self, variable_name):
        """Load a configuration from an environment variable pointing to
        a configuration file.

        :param variable_name: name of the environment variable
        :return: bool. ``True`` if able to load config, ``False`` otherwise.
        """
        config_file = os.environ.get(variable_name)
        if not config_file:
            raise RuntimeError('The environment variable %r is not set and '
                               'thus configuration could not be loaded.' %
                               variable_name)
        return self.from_pyfile(config_file)

    def from_pyfile(self, filename):
        """Update the values in the config from a Python file.
        Only the uppercase variables in that module are stored in the config.

        :param filename: an absolute path to the config file
        """
        module = types.ModuleType('config')
        module.__file__ = filename
        try:
            with open(filename) as config_file:
                exec(compile(config_file.read(), filename, 'exec'),
                     module.__dict__)
        except IOError as e:
            e.strerror = 'Unable to load configuration file (%s)' % e.strerror
            raise
        self.from_object(module)
        return True

    def from_object(self, obj):
        """Update the values from the given object.
        Objects are usually either modules or classes.

        Just the uppercase variables in that object are stored in the config.
        Example usage::

            from yourapplication import default_config
            app.config.from_object(default_config)

        You should not use this function to load the actual configuration but
        rather configuration defaults. The actual config should be loaded
        with :meth:`from_pyfile` and ideally from a location not within the
        package because the package might be installed system wide.

        :param obj: an object holding the configuration
        """
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)

    def load_environment_vars(self):
        for k, v in os.environ.items():
            """
            Looks for any SANIC_ prefixed environment variables and applies
            them to the configuration if present.
            """
            if k.startswith(SANIC_PREFIX):
                _, config_key = k.split(SANIC_PREFIX, 1)
                self[config_key] = v
