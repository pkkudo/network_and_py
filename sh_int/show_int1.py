# general
import os
from getpass import getpass  # if not passing credentials from etc/.env file
import json

# env
from dotenv import load_dotenv

# ssh and tunnel
from netmiko.ssh_dispatcher import ConnectHandler

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
    target_device = '10.1.1.1'
    target = {
        "device_type": 'cisco_ios',
        "host": target_device,
        "username": username,
        "password": password,
        "secret": secret,
        "timeout": 5,
    }

    # get information from a remote device
    with ConnectHandler(**target) as net_connect:
        net_connect.session_preparation()
        # use ntc_template
        dct_int = net_connect.send_command_timing('show interfaces', use_textfsm=True)
        # get raw output
        o_int = net_connect.send_command_timing('show interfaces')

    # write the retrieved information to a file
    f_out = '/'.join([dir_out, target_device])
    f_out += '_show_int.json'
    with open(f_out, 'w') as salida:
        salida.write(json.dumps(dct_int, indent=2))
    f_out = f_out[:-5] + '.txt'
    with open(f_out, 'w') as salida:
        salida.write(o_int)

    return 0


if __name__ == "__main__":
    main()
