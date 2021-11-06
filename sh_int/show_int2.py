# general
import sys
import os
from getpass import getpass  # if not passing credentials from etc/.env file
import logging
import logging.handlers as handlers
f_logfile = 'log/' + sys.argv[0] + ".log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), handlers.TimedRotatingFileHandler(f_logfile, when='D', interval=2, backupCount=2)],
    #handlers=[logging.FileHandler(f_logfile, "w")],
)
logger = logging.getLogger(__name__)
import json

# env
from dotenv import load_dotenv

# ssh and tunnel
from netmiko.ssh_dispatcher import ConnectHandler
from netmiko import NetmikoAuthenticationException

# files, directories
dir_out = 'out'

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


def main():
    # target device
    target_device = ['10.1.1.1', '10.1.1.2']
    target = {
        "device_type": 'cisco_ios',
        "host": '',
        "username": username,
        "password": password,
        "secret": secret,
        "timeout": 5,
    }

    for device in target_device:
        logger.info(f'Working on {device}')
        target['host'] = device
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
                with open(f_out, 'w') as salida:
                    salida.write(json.dumps(dct_int, indent=2))
                    logger.info(f'Info written in {f_out}')
            except:
                logger.error(f'Failed to write the info in {f_out}')
        except NetmikoAuthenticationException:
            logger.error(f'Authentication error on {username}@{device}')
        except:
            logger.error(f'Unknown error when working on on {device}')

    return 0


if __name__ == "__main__":
    main()
