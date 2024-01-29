import argparse
import sys
import traceback

from main import run


class _ArgParser:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='[stream] [detector]',
            conflict_handler="resolve"
        )
        parser.add_argument(
            'stream',
            help='The KVS Stream name.',
        )
        parser.add_argument(
            'detector',
            help='The Lambda detector function name.',
        )

        self._args = vars(parser.parse_args())

    def __contains__(self, key: str):
        return key in self._args

    def __getitem__(self, key: str):
        return self._args[key]

    def args(self):
        return self._args.items()


def _entry():
    run()


if __name__ == '__main__':
    try:
        _entry()
        sys.exit(0)
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, file=sys.stdout)
        sys.exit(1)
