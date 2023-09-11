# python3
# -*- coding:utf-8 -*-
"""
"""
# ------------------------------------------------------------------------------------------------------------------------------------------
import argparse
import logging
import sys
from pathlib import Path
from typing import List
from .config import Config
# ------------------------------------------------------------------------------------------------------------------------------------------
def cli(name:str, argv:List[str])->Config:
    """
    Command line interface handler.

    Creates and returns a :class:`Config` object build by the given command line arguments ``argv``.
    Additionally calls :meth:`Config.configure_logging` and :meth:`Config.set_env` on the created :class:`Config` object
    before returning it.

    :param name: Name of the instance which uses this function. There should be a section within the
        config file having such name.

    :param argv: List of command line argument strings.

    :returns: A :class:`Config` object build from the section with ``name`` from the used config file.

    :raise FileNotFoundError: If no config file was found.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-cf', '--config-file', dest='config_file', type=str, default='resources/config.json',
        help="Path to an optional config file. If omitted, resources/config.json beside this package is used.")
    
    options:argparse.Namespace = parser.parse_args(argv)

    cfg_file:Path = Path(options.config_file).expanduser()
    if not cfg_file.exists():
        if not cfg_file.is_absolute():
            cfg_file = (Path(__file__).parent / cfg_file).resolve()
        if not cfg_file.exists():
            print(f"no such config file '{cfg_file}'", file=sys.stderr)
            raise FileNotFoundError(f"no such config file '{cfg_file}'")
        
    cfg:Config = Config(name, cfg_file)
    cfg.configure_logging()
    cfg.set_env()
    logging.debug("using config file '%s'", cfg_file)
    return cfg
# ------------------------------------------------------------------------------------------------------------------------------------------
