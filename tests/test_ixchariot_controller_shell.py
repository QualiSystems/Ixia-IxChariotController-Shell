
from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue
from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import (create_session_from_cloudshell_config, create_command_context,
                                                   end_reservation)

client_install_path = 'E:/Program Files (x86)/Ixia/IxChariot/webapi-96'

address = '192.168.42.167'
user = 'admin'
password = 'admin'
ports = ['ixchariot 96/Yoram-PC/192.168.15.23', 'ixchariot 96/IxServer/192.168.42.61',
         'ixchariot 96/Yoram-PC/localhost', 'ixchariot 96/IxServer/localhost']

address = 'ixchariot.airties.com'
user = 'ixchariot-testshell@airties.com'
password = 'QAteam2017'
ports = ['airties/A43-PC-MKOY/192.168.2.21', 'airties/A27-PC-MKOY/192.168.2.17']

attributes = [AttributeNameValue('Client Install Path', client_install_path),
              AttributeNameValue('Controller Address', address),
              AttributeNameValue('User', user),
              AttributeNameValue('Password', password)]


class TestIxChariotControllerShell():

    def setup(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'IxChariot Controller', attributes)

    def teardown(self):
        end_reservation(self.session, self.context.reservation.reservation_id)

    def test_load_config(self):
        self._load_config('simple_config', {0: 'Src', 1: 'Dst', 2: '', 3: ''})

    def test_run_and_stats(self):
        self._load_config('TestShell_Unicast_UDP_2min', {0: 'Src', 1: 'Dst'})
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxChariot Controller', 'Service',
                                    'start_test', [InputNameValue('blocking', 'True')])
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxChariot Controller', 'Service',
                                    'get_statistics', [InputNameValue('view_name', 'ixchariot'),
                                                       InputNameValue('output_type', 'CSV')])
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxChariot Controller', 'Service',
                                    'get_statistics', [InputNameValue('view_name', 'ixchariot'),
                                                       InputNameValue('output_type', 'PDF')])

    def test_two_eps_per_flow(self):
        self._load_config('two_eps', {0: 'Src', 1: 'Src', 2: 'Dst', 3: 'Dst'})
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxChariot Controller', 'Service',
                                    'start_test', [InputNameValue('blocking', 'True')])
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxChariot Controller', 'Service',
                                    'get_statistics', [InputNameValue('view_name', 'ixchariot'),
                                                       InputNameValue('output_type', 'CSV')])

    def test_two_flows(self):
        self._load_config('two_flows', {0: 'Src-1 Dst-2', 1: 'Dst-1 Src-2', 2: '', 3: ''})
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxChariot Controller', 'Service',
                                    'start_test', [InputNameValue('blocking', 'True')])
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxChariot Controller', 'Service',
                                    'get_statistics', [InputNameValue('view_name', 'ixchariot'),
                                                       InputNameValue('output_type', 'CSV')])

    def _load_config(self, config, ports):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Traffic Generator Test IP')
        for index, name in ports.items():
            set_family_attribute(self.session, reservation_ports[index], 'Logical Name', name)
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxChariot Controller', 'Service',
                                    'load_config', [InputNameValue('ixc_config', config)])
