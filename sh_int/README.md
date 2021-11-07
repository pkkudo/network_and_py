# show interfaces

Run `show int` on Cisco IOS device using [netmiko](https://github.com/ktbyers/netmiko).

# todos

- [x] use netmiko ConnectHandler to access single device and get `show int` output and write it in a file
- [x] do the same for multiple devices, and add some logging
- [x] read target device list from a file
- [x] argparse to give one target in cli or option to use device list file
- [ ] argparse option to use proxy
- [ ] use netmiko SSHDetect and save the result
- [ ] use SSHDetect result
- [ ] ...
