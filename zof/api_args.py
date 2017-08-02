"""

Environment Variables:
    zof_OFTR_PREFIX
    zof_OFTR_PATH
    zof_OFTR_ARGS

"""

import argparse
import importlib
import sys
import os
from .controller import Controller
from .logging import EXT_STDERR

DEFAULT_ENDPOINTS = [6633, 6653]
DEFAULT_LOGFILE = EXT_STDERR
DEFAULT_LOGLEVEL = 'info'


class _SplitCommaAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError('nargs not allowed')
        super().__init__(option_strings, dest, **kwargs)
        self._count = 0

    def __call__(self, parser, namespace, values, option_string=None):
        self._count += 1
        if self._count > 1:
            raise argparse.ArgumentError(self, 'Option present more than once')
        values = [s.strip() for s in values.split(',')]
        setattr(namespace, self.dest, values)


class _ArgParserTest(argparse.ArgumentParser):
    """ArgumentParser subclass that does not exit.
    """

    def exit(self, status=0, message=None):
        raise RuntimeError('_ArgParserTest: status=%d, message="%s"' %
                           (status, message))


def _parent_args():
    return [
        app.arg_parser for app in Controller.singleton().apps
        if app.arg_parser is not None
    ]


def common_args(*, under_test=False, include_x_modules=False):
    """Construct default ArgumentParser parent.

    Args:
        under_test (Boolean): When true, create an argument parser subclass
            that raises an exception instead of calling exit.
        include_x_modules (Boolean): When true, include "--x-modules" argument.
    """
    if include_x_modules:
        _import_extra_modules()

    parser_class = _ArgParserTest if under_test else argparse.ArgumentParser
    parser = parser_class(add_help=False, parents=_parent_args())

    log_group = parser.add_argument_group('log arguments')
    log_group.add_argument(
        '--loglevel',
        metavar='LEVEL',
        help='log level',
        default=DEFAULT_LOGLEVEL)
    log_group.add_argument(
        '--logfile', metavar='FILE', help='log file', default=DEFAULT_LOGFILE)

    listen_group = parser.add_argument_group('listen arguments')
    listen_group.add_argument(
        '--listen-endpoints',
        metavar='ENDPOINT,...',
        action=_SplitCommaAction,
        help='listen endpoints separated by commas',
        default=DEFAULT_ENDPOINTS)
    listen_group.add_argument(
        '--listen-versions',
        metavar='VERSION,...',
        action=_SplitCommaAction,
        help='listen versions (1-6) separated by commas')
    listen_group.add_argument(
        '--listen-cert',
        type=file_contents_type,
        metavar='FILE',
        help='certificate chain')
    listen_group.add_argument(
        '--listen-cacert',
        type=file_contents_type,
        metavar='FILE',
        help='certificate authority')
    listen_group.add_argument(
        '--listen-privkey',
        type=file_contents_type,
        metavar='FILE',
        help='private key')

    x_group = parser.add_argument_group('experimental')
    x_group.add_argument('--x-uvloop', action='store_true', help='use uvloop')
    x_group.add_argument(
        '--x-oftr-path',
        help='path to oftr executable',
        default=os.getenv('zof_OFTR_PATH'))
    x_group.add_argument(
        '--x-oftr-args',
        help='arguments passed to oftr',
        default=os.getenv('zof_OFTR_ARGS'))
    x_group.add_argument(
        '--x-oftr-prefix',
        help='prefix used to launch oftr (valgrind, strace, catchsegv)',
        default=os.getenv('zof_OFTR_PREFIX'))
    x_group.add_argument(
        '--x-under-test',
        action='store_true',
        default=under_test,
        help='special test mode')

    # --x-modules is included here for documentation purposes only. This arg
    # is pre-processed by the `import_extra_modules()` function.
    if include_x_modules:
        x_group.add_argument(
            '--x-modules',
            metavar='MODULE,...',
            action=_SplitCommaAction,
            help='modules to import')

    return parser


def _import_extra_modules(*, under_test=False):
    """Find the --x-modules argument and process it alone.
    """
    parser_class = _ArgParserTest if under_test else argparse.ArgumentParser
    parser = parser_class(add_help=False)
    parser.add_argument(
        '--x-modules',
        metavar='MODULE,...',
        action=_SplitCommaAction,
        help='modules to import')

    args, _ = parser.parse_known_args()
    if args.x_modules:
        _import_modules(args.x_modules)


def _import_modules(modules):
    """Import modules."""
    try:
        for module in modules:
            importlib.import_module(module)
    except ImportError as ex:
        print(ex, file=sys.stderr, flush=True)
        sys.exit(1)


def file_contents_type(filename):
    """Return contents of file."""
    with open(filename, encoding='utf-8') as afile:
        return afile.read()