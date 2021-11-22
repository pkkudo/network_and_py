# general
__author__ = 'pkkudo@github'
__version__ = '1.20211107'
import sys
import os
from getpass import getpass  # if not passing credentials from etc/.env file
import logging
import logging.handlers as handlers
f_logfile = 'log/' + sys.argv[0] + ".log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    #handlers=[logging.StreamHandler(), handlers.TimedRotatingFileHandler(f_logfile, when='D', interval=2, backupCount=2)],
    #handlers=[logging.FileHandler(f_logfile, "w")],
    handlers=[logging.StreamHandler(), logging.FileHandler(f_logfile, "w")],
)
logger = logging.getLogger(__name__)
import json
import re
import argparse

# figlet
from pyfiglet import Figlet

# env
from dotenv import load_dotenv

# ssh and tunnel
from netmiko.ssh_dispatcher import ConnectHandler
from netmiko import NetmikoAuthenticationException
from netmiko.ssh_exception import NetmikoTimeoutException

# files, directories
dir_out = 'out'
f_device_list = 'etc/device_list.txt'

# load credentials from etc/.env
f_env = 'etc/.env'
if os.path.isfile(f_env):
    load_dotenv(f_env)
    username = os.environ.get('NTA_USERNAME')
    password = os.environ.get('NTA_PASSWORD')
    secret = os.environ.get('NTA_SECRET')
else:
    print(f".env file not found at {f_env}")
    username = input('username: ')
    password = getpass('password: ')
    secret = getpass('secret: ')


# classes, functions

def parse_options():
    # parser
    f = Figlet(font='standard')
    print(f.renderText(sys.argv[0]))
    print('Author: {}'.format(__author__))
    print('Version: {}\n'.format(__version__))

    parser = argparse.ArgumentParser(add_help=True,
        description='Go gets show interface from a remote device.')

    parser.add_argument('target', nargs='?', help='specify target device - "192.168.1.1", "router.example.net", "customport.example.com:9022"')
    parser.add_argument('--list', '-l', action='store_true', help='use list given in the file')
    parser.add_argument('--file', '-f', default='etc/device_list.txt', help='list file to use - default=etc/device_list.txt')

    # process
    if len(sys.argv) > 1:
        try:
            return parser.parse_args()
        except(argparse.ArgumentError):
            parser.error()
    else:
        parser.print_help()
        sys.exit(1)


def main():
    options = parse_options()
    print(options.target)
    logger.info('hi')
    # target devices
    target_devices = []
    if options.target:
        target_devices.append(options.target)
    elif options.list:
        try:
            f_device_list = options.file
            with open(f_device_list, 'r') as entrada:
                target_devices = entrada.read().splitlines()
        except:
            logger.exception(f'Failed to load target device list from {f_device_list}')
            sys.exit(1)

    # setting device type, credentials, and timeout
    target = {
        "device_type": 'cisco_ios',
        "host": '',
        "username": username,
        "password": password,
        "secret": secret,
        "timeout": 5,
    }

    for i, device in enumerate(target_devices, 1):
        logger.info(f'Working on {device}')
        # skipping empty or commented out line
        if not device or re.match(r'^#', device):
            logger.info(f'Skipping "{device}" at line {i}')
            continue
        target['host'] = device
        # if port is specified like 192.168.1.1:22, get those info
        if len(device.split(':')) == 2:
            host, port = device.split(':')
            port = int(port)
            target['host'] = host
            target['port'] = port
        # get information from a remote device
        try:
            with ConnectHandler(**target) as net_connect:
                logger.info(f"Connected - {device}")
                net_connect.session_preparation()
                dct_int = net_connect.send_command_timing('show interfaces', use_textfsm=True)
                logger.info(f"Got show int from {device}")
            try:
                # write the retrieved information to a file
                f_out = '/'.join([dir_out, device])
                f_out += '_show_int.json'
                # replace ":" in the output file name
                if "port" in target.keys():
                    f_out = f_out.replace(':', '_p')
                with open(f_out, 'w') as salida:
                    salida.write(json.dumps(dct_int, indent=2))
                    logger.info(f'Info written in {f_out}')
            except:
                logger.error(f'Failed to write the info in {f_out}')
            finally:
                # clean up "port"
                if "port" in target.keys():
                    del target["port"]
        except NetmikoTimeoutException:
            logger.error(f'Could not connect - "{device}"')
        except NetmikoAuthenticationException:
            logger.error(f'Authentication error - {username}@{device}')
        except:
            logger.exception(f'Unknown error - "{device}"')
        finally:
            # clean up "port"
            if "port" in target.keys():
                del target["port"]

    return 0


if __name__ == "__main__":
    main()
