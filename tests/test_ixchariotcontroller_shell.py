#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `IxChariotControllerDriver`
"""

import unittest
import yaml

from cloudshell.api.cloudshell_api import CloudShellAPISession

import tg_helper
from driver import IxChariotControllerDriver

server_address = 'ixchariot.corp.airties.com'
server_user = 'fetullah.turkeli@airties.com'
server_password = '123456789aA.'

client_install_path = "c:/"

ixc_config = 'erztest2'


class TestIxChariotControllerDriver(unittest.TestCase):

    def setUp(self):

        with open('../cloudshell_config.yml', 'r') as f:
            doc = yaml.load(f)
        username = doc['install']['username']
        password = doc['install']['password']
        domain = doc['install']['domain']
        host = doc['install']['host']

        self.session = CloudShellAPISession(host, username, password, domain)
        self.context = tg_helper.create_context(self.session, 'ixchariot test', 'IxChariot Controller',
                                                client_install_path, server_address)
        self.context.resource.attributes.update({'User': server_user,
                                                 'Password': server_password})
        self.driver = IxChariotControllerDriver()
        self.driver.initialize(self.context)

    def tearDown(self):
        self.driver.cleanup()

    def testInit(self):
        pass

    def testLoadConfig(self):

        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id,
                                                            'Traffic Generator Test IP')
        self.driver.load_config(self.context, ixc_config)

        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'ixchariot')

        self.driver.start_test(self.context, 'False')
        self.driver.stop_test(self.context)
        print self.driver.get_statistics(self.context, 'ixchariot')

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
