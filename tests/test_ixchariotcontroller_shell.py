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
server_user = 'ixchariot@airties.com'
server_password = 'QAteam2017'

client_install_path = "c:/"

ixc_config = 'TestShell_Unicast_TCP'


class TestIxChariotControllerDriver(unittest.TestCase):

    def setUp(self):

        with open('../cloudshell_config.yml', 'r') as f:
            doc = yaml.load(f)
        username = doc['install']['username']
        password = doc['install']['password']
        domain = doc['install']['domain']
        host = doc['install']['host']

        self.session = CloudShellAPISession(host, username, password, domain)
        self.context = tg_helper.create_context(self.session, '[Mkoy-CTI] CTI Mesh Setups', 'IxChariot Controller',
                                                client_install_path, server_address)
        self.context.resource.attributes.update({'User': server_user,
                                                 'Password': server_password})
        self.driver = IxChariotControllerDriver()
        self.driver.initialize(self.context)

    def tearDown(self):
        self.driver.cleanup()

    def testInit(self):
        pass

    def test_load_config(self):

        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id,
                                                            'Traffic Generator Test IP')
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Src')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Dst')
        print self.driver.load_config(self.context, ixc_config)

    def test_run_test(self):

        self.test_load_config()

        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'ixchariot')

        self.driver.start_test(self.context, 'False')
        self.driver.stop_test(self.context)
        print self.driver.get_statistics(self.context, 'ixchariot')

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
