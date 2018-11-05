
import sys
import logging
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config, create_command_context

from cloudshell.traffic import tg_helper
from driver import IxChariotControllerDriver

client_install_path = 'C:/Program Files (x86)/Ixia/IxChariot/webapi-96'
address = '192.168.42.167'
user = 'admin'
password = 'DxTbqlSgAVPmrDLlHvJrsA=='

ports = ['ixchariot 96/Yoram-PC/192.168.15.23', 'ixchariot 96/IxServer/192.168.42.61',
         'ixchariot 96/Yoram-PC/localhost', 'ixchariot 96/IxServer/localhost']


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
        print 'New session ID = {}'.format(self._load_config('simple_config', {0: 'Src', 1: 'Dst', 2: '', 3: ''}))

    def test_run_and_stats(self):
        self._load_config('simple_config', {0: 'Src', 1: 'Dst', 2: '', 3: ''})
        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'ixchariot', 'CSV')
        print self.driver.get_statistics(self.context, 'ixchariot', 'PDF')

    def test_two_eps_per_flow(self):
        self._load_config('two_eps', {0: 'Src', 1: 'Src', 2: 'Dst', 3: 'Dst'})
        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'ixchariot', 'CSV')

    def test_two_flows(self):
        self._load_config('two_flows', {0: 'Src-1 Dst-2', 1: 'Dst-1 Src-2', 2: '', 3: ''})
        self.driver.start_test(self.context, 'True')
        print self.driver.get_statistics(self.context, 'ixchariot', 'CSV')

    def _load_config(self, config, ports):
        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id,
                                                            'Traffic Generator Test IP')
        for index, name in ports.items():
            self.session.SetAttributeValue(reservation_ports[index].Name, 'Logical Name', name)
        return self.driver.load_config(self.context, config)
