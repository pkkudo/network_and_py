# show interfaces

Run `show int` on Cisco IOS device using [netmiko](https://github.com/ktbyers/netmiko).

# Setup

1. (optional) use venv
2. install requirements
3. (optional) update `etc/.env` file

```
python3 -m venv venv
source venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
# edit etc/.env file to have the scripts use username/password in the file
# then execute the scripts
```

"sh_int1.py" for example tries to load etc/.env file to get the credential to use, and if not found, the script prompts user to manually input each time you run this script. The destination host/ipaddr and the netmiko "device_type" is hardcoded in the script. 


# todos

- [x] use netmiko ConnectHandler to access single device and get `show int` output and write it in a file
- [x] do the same for multiple devices, and add some logging
- [x] read target device list from a file
- [x] argparse to give one target in cli or option to use device list file
- [x] argparse option to use proxy
  - `show_int5.py`
  - run `ssh -D {port} {server}` to establish dynamic port forwarding before running the script
  - example) ssh -D 1080 10.5.5.5
  - `python show_int5.py --socks_proxy 192.168.1.2`
- [ ] use netmiko SSHDetect and save the result
- [ ] use SSHDetect result
- [ ] label/group devices and execute the script against the specific target set
