#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `IxChariotControllerDriver`
"""

import unittest
import yaml

import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers

from src.ixc_handler import IxcHandler

reservation_id = '762716df-cc40-41d0-8ee8-f6f9095c853a'

address = 'ixchariot.corp.airties.com'

ixc_config = 'tcp sample'


class TestIxChariotControllerDriver(unittest.TestCase):

    def setUp(self):

        with open('../cloudshell_config.yml', 'r') as f:
            doc = yaml.load(f)
        username = doc['install']['username']
        password = doc['install']['password']
        domain = doc['install']['domain']
        host = doc['install']['host']
        port = doc['install']['port']

        dev_helpers.attach_to_cloudshell_as(username, password, domain, reservation_id, host, port)
        self.api = helpers.get_api_session()
        reservation = self.api.GetReservationDetails(reservation_id)

        for resource in reservation.ReservationDescription.Resources:
            if resource.ResourceFamilyName == 'Traffic Generator Controller':
                controller = resource
                break

        self.handler = IxcHandler()

        address = controller.FullAddress
        username = self.api.GetAttributeValue(resourceFullPath=controller.Name, attributeName='User').Value
        password = self.api.GetAttributeValue(resourceFullPath=controller.Name, attributeName='Password').Value
        client_install_path = self.api.GetAttributeValue(resourceFullPath=controller.Name,
                                                         attributeName='Client Install Path').Value
        self.handler.initialize(address, username, password, client_install_path)

    def tearDown(self):
        self.handler.tearDown()

    def testLoadConfig(self):
        self.handler.load_config(self.api, reservation_id, ixc_config)

        self.handler.start_test('True')

        self.handler.start_test('False')
        self.handler.stop_test()

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
