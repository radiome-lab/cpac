#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import logging
import random
import string

from .. import __version__

_logger = logging.getLogger(__name__)


class ExtendAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        items = (getattr(namespace, self.dest) or []) + values
        items = [x for n, x in enumerate(items) if x not in items[:n]]
        setattr(namespace, self.dest, items)


def address(str):
    addr, port = str.split(':')
    port = int(port)
    return addr, port


def parse_args(args):
    parser = argparse.ArgumentParser(
        description='cpac: a Python package that simplifies using C-PAC. CCs development version'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='cpac {ver}'.format(ver=__version__)
    )

    parser.add_argument(
        '-v',
        '--verbose',
        dest="loglevel",
        help="set loglevel to INFO",
        action='store_const',
        const=logging.INFO
    )

    parser.add_argument(
        '-vv',
        '--very-verbose',
        dest="loglevel",
        help="set loglevel to DEBUG",
        action='store_const',
        const=logging.DEBUG
    )

    subparsers = parser.add_subparsers(dest='command')

    scheduler_parser = subparsers.add_parser('scheduler')
    scheduler_parser.add_argument('--address', action='store', type=address, default='localhost:3333')
    scheduler_parser.add_argument('--proxy', action='store_true')
    scheduler_parser.add_argument('--backend', choices=['docker', 'singularity', 'slurm'], default='singularity')

    scheduler_parser.add_argument('--singularity-image', nargs='?')
    
    scheduler_parser.add_argument('--docker-image', nargs='?')

    scheduler_parser.add_argument('--slurm-host', nargs='?')
    scheduler_parser.add_argument('--slurm-username', nargs='?')
    scheduler_parser.add_argument('--slurm-key', nargs='?')
    scheduler_parser.add_argument('--slurm-control', nargs='?',
            default=f'~/.ssh/{"".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(24))}')
    scheduler_parser.add_argument('--slurm-pip-install', nargs='?')
    scheduler_parser.add_argument('--slurm-singularity-image', nargs='?')

    parsed = parser.parse_args(args)

    return parsed


def setup_logging(loglevel):
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


async def start(args):
    from cpac.api.server import start
    from cpac.api.backends import available_backends
    from cpac.api.scheduling import Scheduler
    from cpac.api.authKey import AuthKey

    print("Running server")
    print("Auth key: ", AuthKey.generateKey())

    backend = args.backend
    cmd_args = vars(args)

    backend = available_backends[backend](
        id=backend,
        **{
            arg.split('_', 1)[1]: val
            for arg, val in cmd_args.items()
            if arg.startswith(backend)
        }
    )

    async with Scheduler(backend, proxy=args.proxy) as scheduler:
        await start(args.address, scheduler)
        await scheduler


def main(args):
    command = args[0]
    args = parse_args(args[1:])
    setup_logging(args.loglevel)

    if args.command == 'scheduler':
        import asyncio
        asyncio.run(start(args))


def run():
    main(sys.argv)


if __name__ == "__main__":
    run()
