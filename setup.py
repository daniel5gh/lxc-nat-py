from setuptools import setup

setup(
    name='lxc-nat-py',
    version='1.0.dev0',
    packages=['lxc_nat'],
    scripts=['scripts/lxc-nat.py'],
    url='https://github.com/daniel5gh/lxc-nat-py',
    license='MIT',
    author='Daniel van Adrichem',
    author_email='daniel5git@spiet.nl',
    description='Python script to setup iptables to forward to LXC'
                'containers according to forwarder config in a YAML file.',
    # PyYAML requirement is probably way lower version, this is what I had
    # installed
    install_requires=['PyYAML>=3.11'],
    setup_requires=['setuptools>=15.2', 'wheel>=0.24.0'],
)
