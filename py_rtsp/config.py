# python3
# -*- coding:utf-8 -*-
"""

"""
# ------------------------------------------------------------------------------------------------------------------------------------------
import json
import os
import logging
import logging.config
from pathlib import Path
from typing import Union, Any, Dict
# ------------------------------------------------------------------------------------------------------------------------------------------
logger:logging.Logger = logging.getLogger('config')
# ------------------------------------------------------------------------------------------------------------------------------------------
class Config(dict):
    """
    Holds the current configuration.
    """
    
    def __init__(self, section:str, file_or_config:Union[None,dict,str,Path,"Config"]=None, **kwargs):
        """
        Create the config object from either file, dict, other :class:`Config` from param ``file_or_config``.
        In case of file see :meth:`load_config`, a dict or :class:`Config` instance is still copied (shallow).
        Additional keyword arguments ``kwargs`` will update the configuration (after beeing loaded or copied).
        """
        #: The internal config dict.
        self._config:Dict[str, Any] = {}
        self._section:str = section
        self.config_file:Union[None,Path]=None
        if isinstance(file_or_config, dict):
            self._config = file_or_config
        elif isinstance(file_or_config, Config):
            self._config = file_or_config._config
        elif isinstance(file_or_config, (str, Path)):
            self.load_config(Path(file_or_config))
        elif file_or_config is not None:
            raise TypeError(f"Unexpected type for `file_or_config`: {type(file_or_config)}")
        self._config.update(**kwargs)

    def load_config(self, filepath:Path, section:Union[None,str]=None):
        """
        Loads the configuration file (JSON format) from ``filepath`` and sets the config from section ``section``.
        If the latter is None, :attr:`_section` is used as section name.

        :raise: ``FileNotFoundError`` if ``filepath`` doesn't exist.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Config file {filepath} doesn't exist")
        try:
            cfg = json.load(filepath.open(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.error('failed to parse json from %s: %s', filepath, exc)
            raise exc

        self.config_file = filepath

        if section is None:
            section = self._section
        try:
            self._config = cfg[section]
        except KeyError as exc:
            raise KeyError(f"No section {section} in config file {filepath}")

    def configure_logging(self, **kwargs):
        """
        Configures the logging from key ``logging`` which should be a dictionary according to specs from :func:`logging.config.dictConfig`.
        Optional keyword arguments from ``kwargs`` are used to update the logging config dict before using it.

        :param section: The section to configure logging for.
        """
        config = dict(self.logging)
        config.update(**kwargs)
        logging.config.dictConfig(config)
   
    def set_env(self):
        if not 'env' in self._config:
            return
        env = self.env
        if not isinstance(env, dict):
            raise ValueError(f"Config section 'env' has to be a dictionary!")
        logger.info("setting up environment")
        logger.debug("env = %s", env)
        os.environ.update(env)

    def __getattr__(self, name:str)->Any:
        """
        Returns item of key ``name`` from the config dictionary like ``Config.<name> --> Config[name]``
        """
        try:
            return self._config[name]
        except KeyError as exc:
            raise AttributeError(f"{self} doesn't have an attribute {name!r}!")
# ------------------------------------------------------------------------------------------------------------------------------------------