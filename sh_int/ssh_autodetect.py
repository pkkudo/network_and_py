# general
__author__ = 'pkkudo@github'
__version__ = '0.20211127'
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
import csv

# env and config
from dotenv import load_dotenv
conf = {}

# ssh and tunnel
from netmiko.ssh_dispatcher import ConnectHandler
from netmiko.ssh_autodetect import SSHDetect
from netmiko import NetmikoAuthenticationException
from netmiko.ssh_exception import NetmikoTimeoutException

# socks proxy
import socket
import socks

# files, directories
dir_out = 'out'
f_device_list = 'etc/device_list.txt'
f_inventory = "etc/inventory.json"
f_inventory_csv = "etc/inventory.csv"

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
    parser = argparse.ArgumentParser(add_help=True,
        description='Go gets show interface from a remote device.')

    # arg on scope/target
    parser.add_argument('target', nargs='?', help='specify target device - "192.168.1.1", "router.example.net", "customport.example.com:9022"')
    parser.add_argument('--list', '-l', action='store_true', help='use list given in the file')
    parser.add_argument('--file', '-f', default='etc/device_list.txt', help='list file to use - default=etc/device_list.txt')

    # arg on options
    parser.add_argument('--socks_proxy', '-x', action='store_true', help='use socks proxy defined in the env file')
    parser.add_argument('--all', '-a', action='store_true', help='try ssh_autodetect despite the previous result')

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
    if options.socks_proxy:
        try:
            conf['socks_proxy_server'] = os.environ.get('NTA_SOCKS').split(':')[0]
            conf['socks_proxy_port'] = int(os.environ.get('NTA_SOCKS').split(':')[-1])
        except:
            logger.error('Error loading details on socks proxy from env file')

    if "socks_proxy_server" in conf.keys():
        proxy_server = conf.get('socks_proxy_server')
        proxy_port = conf.get('socks_proxy_port')
        # check if socks proxy is listening
        # then set the socks proxy
        try:
            logger.info(f'Checking if socks proxy is listening on {proxy_server}:{proxy_port}')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((proxy_server, proxy_port))
                s.shutdown(1)
            socks.set_default_proxy(socks.SOCKS5, proxy_server, proxy_port)
            socket.socket = socks.socksocket
            logger.info(f'Using socks proxy on {proxy_server}:{proxy_port}')
        except ConnectionRefusedError:
            logger.error('Socks proxy is not listening. Exit.')
            sys.exit(1)

    # target devices
    target_devices = []
    if options.target:
        target_devices.append(options.target)
    elif options.list:
        try:
            with open(f_device_list, 'r') as entrada:
                target_devices = entrada.read().splitlines()
        except:
            logger.exception(f'Failed to load target device list from {f_device_list}')
            sys.exit(1)

    # setting device type, credentials, and timeout
    target = {
        #"device_type": 'autodetect',
        "host": '',
        "username": username,
        "password": password,
        "secret": secret,
        "timeout": 5,
    }

    dct_inventory = {}
    for i, device in enumerate(target_devices, 1):
        target["device_type"] = "autodetect"
        best_match = ''
        timestamp = ''
        logger.info(f'Working on {device}')
        # skipping empty or commented out line
        if not device or re.match(r'^#', device):
            logger.info(f'Skipping "{device}" at line {i}')
            continue
        # check if successfully connected previously
        if not options.all:
            if os.path.exists(f_inventory):
                try:
                    with open(f_inventory, 'r') as entrada:
                        o = json.load(entrada)
                        for item in o:
                            if device == o[item].get('device') and o[item].get('last_connected_utc'):
                                logger.info(f'ssh_autodetect data for {device} already in {f_inventory}')
                                dct_inventory[i] = o[item]
                                continue
                except:
                    logger.info(f'Failed to find the previous ssh_autodetect result for {device} in {f_inventory}')
        target['host'] = device
        # if port is specified like 192.168.1.1:22, get those info
        if len(device.split(':')) == 2:
            host, port = device.split(':')
            port = int(port)
            target['host'] = host
            target['port'] = port
        # get information from a remote device
        try:
            with SSHDetect(**target) as guesser:
                logger.info(f"Connected - {device}")
                timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M")
                best_match = guesser.autodetect()
                logger.info(f"netmiko device_type guesser - {device}: {best_match}")
            # update target dictionary when successful
            target["device_type"] = best_match
        except NetmikoTimeoutException:
            logger.error(f'Could not connect - "{device}"')
            best_match = "access_failed"
        except NetmikoAuthenticationException:
            logger.error(f'Authentication error - {username}@{device}')
            best_match = "auth_error"
        except:
            logger.exception(f'Unknown error - "{device}"')
            best_match = "unknown_error"
        finally:
            dct_inventory[i] = {
                "_id": i,
                "device": device,
                "target": target,
                "netmiko_sshdetect": best_match,
            }
            if timestamp:
                dct_inventory[i]["last_connected_utc"] = timestamp
            if proxy_server and proxy_port:
                px = proxy_server + ':' + proxy_port
                dct_inventory[i]["jump_server"] = px
            # clean up "port"
            if "port" in target.keys():
                del target["port"]

    # save the result in files
    lst_headers = ["_id", "device", "netmiko_sshdetect", "last_connected_utc", "jump_server"]
    with open(f_inventory_csv, 'w') as salida:
        writer = csv.DictWriter(salida, fieldnames=lst_headers, extrasaction='ignore')
        writer.writeheader()
        for item in dct_inventory:
            writer.writerow(dct_inventory[item])
        logger.info(f'Result written in {f_inventory_csv}')

    with open(f_inventory, 'w') as salida:
        salida.write(json.dumps(dct_inventory, indent=2))
        logger.info(f'Result written in {f_inventory}')

    return 0


if __name__ == "__main__":
    main()
