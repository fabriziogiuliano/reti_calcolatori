"""
Start os-ken applications (os-ken no longer ships the osken-manager command).

Usage, from this folder:
    python run_controller.py rest_router

The controller listens for OpenFlow switches on port 6653.
"""
import logging
import sys

from os_ken import cfg
from os_ken.base.app_manager import AppManager

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)s: %(message)s',
                        datefmt='%H:%M:%S')
    apps = sys.argv[1:] or ['rest_router']
    cfg.CONF(args=[], project='os_ken')
    AppManager.run_apps(apps)
