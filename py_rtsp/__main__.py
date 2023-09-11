# python3
# -*- coding:utf-8 -*-
"""
"""
# ------------------------------------------------------------------------------------------------------------------------------------------
import sys
import signal
import logging
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Union
from .cli import cli
from .config import Config
# ------------------------------------------------------------------------------------------------------------------------------------------
logger:logging.Logger = logging.getLogger("rtsp")
# ------------------------------------------------------------------------------------------------------------------------------------------
class ProcessWatcher:
    def __init__(self, cfg:Config):
        self._run = True
        self.config:Config = cfg
        self.processes:Dict[str, subprocess.Popen] = {}

    def __call__(self)->int:
        result:int = self.start_scripts()
        if result:
            return result

        all_alive:bool = True
        while self._run and all_alive:
            for name, process in self.processes.items():
                if process.poll() is not None:
                    logger.warning("process '%s' with pid %s stopped unexpectedly with exitcode %s", name, process.pid, process.returncode)
                    all_alive = False
            else:
                time.sleep(1) # break in foor loop not called!
        
        return self.stop_scripts()
    
    def open_process(self, cmdline:List[str])->subprocess.Popen:
        kwargs = {}
        if sys.platform == "win32":
            # create a new process group to avoid that SIGTERM kills the parent process
            kwargs.update(creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        return subprocess.Popen(cmdline, **kwargs)
    
    def start_scripts(self)->int:
        # start scripts
        this_path = Path(__file__).parent
        for script in map(Path, self.config.scripts):
            name = script
            if not script.exists():
                script = script.expanduser()
                if not script.is_absolute():
                    script = (this_path / script).resolve()
                if not script.exists():
                    logger.error("no such script '%s'", script)
                    return 1
            cmdline = [sys.executable, script]
            if self.config.config_file:
                cmdline += ['-cf', str(self.config.config_file)]
            try:
                process = self.open_process(cmdline)
            except Exception as exc:
                logger.error("failed to start process '%s', with command line '%s': %s", name, subprocess.list2cmdline(cmdline), exc)
                return 1
            logger.info("process '%s' started with '%s' has pid %s", name, subprocess.list2cmdline(cmdline), process.pid)
            self.processes[name] = process
        return 0
    
    def stop_scripts(self):
        for name in list(self.processes):
            process = self.processes[name]     
            # send a CTRL-C to each process which is still alive yet and put it back to self.processes
            if process.poll() is None:
                logger.info("sending CTRL-C to process '%s' with pid %s", name, process.pid)
                process.send_signal(signal.CTRL_C_EVENT)
            else:
                logger.info("process '%s' with pid %s finished with exitcode %s", name, process.pid, process.returncode)
                del self.processes[name]
        return 0

    def __enter__(self):
        return self
    
    def _wait_for(self, name:str, process:subprocess.Popen)->Union[int,None]:
        try:
            logger.debug("wait max. 5 seconds for process '%s' to finish.", name)
            return process.wait(5.0)
        except subprocess.TimeoutExpired:
            return None
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        logger.debug('on exit')
        self.stop_scripts()

        # now wait for each processes to finish within thime
        for name, process in self.processes.items():
            if self._wait_for(name, process) is None:
                logger.warning("terminating process '%s' with pid %s using SIGKILL", name, process.pid)
                process.kill()
                if self._wait_for(name, process) is None:
                    logger.error("failed to terminate process '%s' with pid %s", name, process.pid)
                    continue
            logger.info("process '%s' with pid %s finished with exitcode %s", name, process.pid, process.returncode)
# ------------------------------------------------------------------------------------------------------------------------------------------
def main(argv:List[str]):

    cfg:Config = cli('rtsp', argv)

    try:
        with ProcessWatcher(cfg) as process_watcher:
            result = process_watcher()
    except (KeyboardInterrupt, SystemExit) as exc:
        logger.warning("stopping due to %s", exc)
    except Exception: # pylint:disable=broad-exception-caught
        logger.exception("caught unhandled exception")
    logger.info("stopped")
    return result
# ------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))