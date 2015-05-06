# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Daniël van Adrichem
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Based on the following ruby scripts referenced on
# http://terrarum.net/blog/building-an-lxc-server-1404.html
#
# https://github.com/jtopjian/lxc-nat/blob/master/lxc-nat.rb
# https://gist.github.com/zanloy/a5648941383d519bb9c4
#
# example YAML input:
# forwards:
#   - source:
#       ip: 10.0.0.1
#       port: 8080
#     destination:
#       name: www
#       port: 80
#   - source:
#       port: 3306
#     destination:
#       name: mysql_server
#   - proto: udp
#     source:
#       interface: eth1
#       port: 53333
#     destination:
#       name: dns_server
#   - source:
#       port: 1234
#     destination:
#       name: test1
#       port: 22

import argparse
import subprocess
import sys
import yaml

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", help="show the iptables commands that are run",
        action='store_true')
    # capital F to match iptables -F for flush
    parser.add_argument(
        "-F", "--flush", help="flush and delete rules and chains only",
        action='store_true')
    parser.add_argument(
        "--dry-run", help="don't actually run the iptables commands",
        action='store_true')
    parser.add_argument(
        "-c", "--conf", help="YAML file containing forwarding rule definitions",
        default='./nat-conf.yml')
    cmdline_args = parser.parse_args()

    # will hold a mapping between lxc container name and their IP
    containers = {}
    # will hold iptables commands to be exectuted
    forwards = []

    # run lxc-ls to query running containers and their IPs
    cmd = 'lxc-ls -f -F name,ipv4'
    args = cmd.split()
    p = subprocess.Popen(args, stdout=subprocess.PIPE)

    # skip first two lines of stdout
    p.stdout.next()
    p.stdout.next()
    # parse remaining stdout lines
    for line in p.stdout:
        con, ip = line.strip().split()
        # if ip is '-', container has no ip
        # TODO: what happens in case of multiple IPs?
        if ip != '-':
            containers[con] = ip

    # read in YAML file
    d = yaml.load(open(cmdline_args.conf))
    # fill the forwards list accoring to YAML contents
    for forward in d['forwards']:
        # TODO: check existance of mandatory keys
        src_iface = forward['source'].get('interface')
        src_ip = forward['source'].get('ip')
        src_port = forward['source']['port']
        proto = forward.get('proto')
        lxc_name = forward['destination']['name']
        lxc_port = forward['destination'].get('port')

        proto = proto or 'tcp'
        if not src_iface and not src_ip:
            src_iface = 'eth0'
        lxc_port = lxc_port or src_port

        if lxc_name in containers:
            lxc_ip = containers[lxc_name]

            # TODO: check input :) esp. spaces are nasty because we split on
            # them in runcmd
            cmd = "iptables -t nat -A lxc-nat"
            if src_iface:
                cmd += " -i {}".format(src_iface)
            if src_ip:
                cmd += " -d {}".format(src_ip)
            if proto:
                cmd += " -p {}".format(proto)
            cmd += " --dport {}".format(src_port)
            cmd += " -j DNAT --to {}:{}".format(lxc_ip, lxc_port)

            forwards.append(cmd)
        else:
            print("{} configured but not running".format(lxc_name))

    # only when the chain exists
    if chain_exists('lxc-nat'):
        # flush and delete
        runcmd('iptables -t nat -F lxc-nat', cmdline_args.dry_run,
               cmdline_args.verbose)
        runcmd('iptables -t nat -D PREROUTING -j lxc-nat', cmdline_args.dry_run,
               cmdline_args.verbose)
        runcmd('iptables -t nat -X lxc-nat', cmdline_args.dry_run,
               cmdline_args.verbose)

    # don't do these if user only want the flush
    if not cmdline_args.flush:
        # create chain
        runcmd('iptables -t nat -N lxc-nat', cmdline_args.dry_run,
               cmdline_args.verbose)
        # and add it to PREROUTING
        runcmd('iptables -t nat -A PREROUTING -j lxc-nat', cmdline_args.dry_run,
               cmdline_args.verbose)
        # add forward rules
        for cmd in forwards:
            runcmd(cmd, cmdline_args.dry_run, cmdline_args.verbose)


def runcmd(cmd, noop, verbose=True):
    # Popen wants args as list, split on space
    args = cmd.split()
    if verbose:
        print(' '.join(args))
    if not noop:
        p = subprocess.Popen(args)
        p.wait()


def chain_exists(name):
    # list rules in chain 'name'
    args = 'iptables -t nat -L'.split()
    args.append(name)
    p = subprocess.Popen(
        args,
        stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    # no output on stderr means it exists
    # return len(p.stderr.read()) == 0
    # exit code 0 means it exists, 1 when it errors out because the chain
    # doesn't exist.
    return p.wait() == 0

if __name__=='__main__':
    main()
