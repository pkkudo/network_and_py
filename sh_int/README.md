# show interfaces

Run `show int` on Cisco IOS device using [netmiko](https://github.com/ktbyers/netmiko).

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
