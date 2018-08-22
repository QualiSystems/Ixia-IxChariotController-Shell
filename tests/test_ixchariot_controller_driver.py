
import sys
import logging
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config, create_command_context

from cloudshell.traffic import tg_helper
from driver import IxChariotControllerDriver


client_install_path = 'C:/Program Files (x86)/Ixia/IxChariot/webapi-95'
address = '192.168.42.191'
user = 'yoram-s@qualisystems.com'
password = 'Zoliro123'

ports = ['ixchariot 95/QS-IL-YORAM/192.168.15.23', 'ixchariot 95/QS-SRV-IXserver/192.168.42.61']
ports = ['ixchariot 95/QS-IL-YORAM/192.168.15.23', 'ixchariot 95/QS-SRV-IXserver/192.168.42.61',
         'ixchariot 95/QS-IL-YORAM/QS-IL-YORAM', 'ixchariot 95/QS-SRV-IXserver/QS-SRV-IXserver']
attributes = {'Client Install Path': client_install_path,
              'Controller Address': address,
              'User': user,
              'Password': password}


class TestIxChariotControllerDriver():

    def setup(self):

        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'IxChariot Controller', attributes)
        self.driver = IxChariotControllerDriver()
        self.driver.initialize(self.context)

    def teardown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id,
                                                            'Traffic Generator Test IP')
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Src')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Dst')
        self.session.SetAttributeValue(reservation_ports[2].Name, 'Logical Name', 'Src')
        self.session.SetAttributeValue(reservation_ports[3].Name, 'Logical Name', 'Dst')
        print self.driver.load_config(self.context, 'two_eps')

    def test_run_test(self):

        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id,
                                                            'Traffic Generator Test IP')
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Src')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Dst')
        self.session.SetAttributeValue(reservation_ports[2].Name, 'Logical Name', 'Src')
        self.session.SetAttributeValue(reservation_ports[3].Name, 'Logical Name', 'Dst')
        self.driver.load_config(self.context, 'two_eps')

        self.driver.start_test(self.context, 'False')
        self.driver.stop_test(self.context)
        print self.driver.get_statistics(self.context, 'ixchariot')

        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'ixchariot')

    def test_two_flows(self):
        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id,
                                                            'Traffic Generator Test IP')
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Src-1 Dst-2')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Dst-1 Src-2')
        self.driver.load_config(self.context, 'two_flows')

        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'ixchariot')
