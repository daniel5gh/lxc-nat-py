# lxc-nat-py
Python script to setup iptables to forward to LXC containers according to
forwarder config in a YAML file.

Based on the following ruby scripts referenced on
http://terrarum.net/blog/building-an-lxc-server-1404.html

* https://github.com/jtopjian/lxc-nat/blob/master/lxc-nat.rb
* https://gist.github.com/zanloy/a5648941383d519bb9c4

I took those and made a python version, I like python. When no filename is
passed to `--conf`, `./nat-conf.yml` is used.

Usage:
```
  usage: lxc-nat.py [-h] [-v] [-F] [--dry-run] [-c CONF]

  optional arguments:
    -h, --help            show this help message and exit
    -v, --verbose         show the iptables commands that are run
    -F, --flush           flush and delete rules and chains only
    --dry-run             don't actually run the iptables commands
    -c CONF, --conf CONF  YAML file containing forwarding rule definitions
```

An example YAML conf file:
```
  forwards:
    - source:
        ip: 10.0.0.1
        port: 8080
      destination:
        name: www
        port: 80
    - source:
        port: 3306
      destination:
        name: mysql_server
    - proto: udp
      source:
        interface: eth1
        port: 53333
      destination:
        name: dns_server
    - source:
        port: 1234
      destination:
        name: test1
        port: 22
```
