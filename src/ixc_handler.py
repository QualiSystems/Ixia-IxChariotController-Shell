
import sys
import imp
import time
import os
import zipfile

from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from cloudshell.traffic import tg_helper


class IxcHandler(object):

    def initialize(self, context, logger):

        self.logger = logger

        address = context.resource.attributes['Controller Address']
        username = context.resource.attributes['User']
        password = context.resource.attributes['Password']
        client_install_path = context.resource.attributes['Client Install Path']

        sys.path.append(client_install_path)
        self.logger.info(os.path.join(client_install_path, 'ixia/webapi.py'))
        webapi = imp.load_source('webapi', os.path.join(client_install_path, 'ixia/webapi.py'))
        self.ixchariotapi = imp.load_source('ixchariotapi', os.path.join(client_install_path, 'ixchariotApi.py'))

        self.connection = webapi.webApi.connect('https://' + address, 'v1', None, username, password)
        self.session = None

    def tearDown(self):
        self.del_session()

    def get_inventory(self):
        return AutoLoadDetails([], [])

    def load_config(self, context, ixc_config):
        """
        :param reservation_id: current reservation ID
        :param ixc_config: IxChariot configuration name.
        """

        self.session = self.connection.createSession('ixchariot')
        self.session.startSession()
        self.session.loadConfiguration(ixc_config)

        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()

        src_resources = []
        dst_resources = []
        for ep in tg_helper.get_reservation_ports(my_api, reservation_id, 'Traffic Generator Test IP'):
            logical_name = my_api.GetAttributeValue(ep.Name, 'Logical Name').Value.strip()
            if logical_name.lower() in ['src', 'source']:
                src_resources.append(ep.Name.split('/')[1])
            elif logical_name.lower() in ['dst', 'destination']:
                dst_resources.append(ep.Name.split('/')[1])
            else:
                self.logger.info('Ignore EP {} - logical name {} not in [src, source, dst, destination]'.
                                 format(ep.Name, logical_name))

        if not src_resources:
            raise Exception('No Src resources')
        if not dst_resources:
            raise Exception('No Dst resources')

        network_url = self._get_network_url()
        self.session.httpDelete(network_url + 'sourceEndpoints')
        self.session.httpDelete(network_url + 'destinationEndpoints')

        for src_ep in src_resources:
            ep = self.ixchariotapi.getEndpointFromResourcesLibrary(self.session, src_ep)
            self.session.httpPost(network_url + 'sourceEndpoints', data=ep)

        for dst_ep in dst_resources:
            ep = self.ixchariotapi.getEndpointFromResourcesLibrary(self.session, dst_ep)
            self.session.httpPost(network_url + 'destinationEndpoints', data=ep)

        # In case of multiple eps delay is required to make sure configuration completed (based on trial and error).
        time.sleep(4)
        self.logger.info("Load Configuration Completed")

        return self.session.sessionId

    def start_test(self, blocking):
        """
        """

        if blocking.lower().strip() == 'true':
            self.result = self.session.runTest()
        else:
            self.result = self.session.startTest()
            time.sleep(4)

    def stop_test(self):
        self.session.stopTest()

    def get_statistics(self, context, view_name):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param view_name: IxChariot results view to retrieve (csv file name in c:/temp/ixChariotTestResults.zip).
        """

        reservation_id = context.reservation.reservation_id
        ts = time.ctime().replace(' ', '_').replace(':', '-')
        filename = 'c:/temp/IxChariotShellResults/' + reservation_id + '/' + ts + '.zip'
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        with open(filename, "wb+") as statsFile:
            self.connection.getStatsCsvZipToFile(self.result.testId, statsFile)

        archive = zipfile.ZipFile(filename, 'r')
        output = archive.read(view_name + '.csv')

        tg_helper.attach_stats_csv(context, self.logger, view_name, output)
        return output

    def end_session(self):
        if self.session:
            self.session.stopSession()

    def del_session(self):
        if self.session:
            if self.session.httpGet().state.lower() in ['starting', 'active']:
                self.end_session()
            self.session.httpDelete()

    #
    # Private auxiliary methods.
    #

    def _get_network_url(self):
        condif = self.session.httpGet('config/ixchariot')
        if condif.appMixes:
            return 'config/ixchariot/appMixes/1/network/'
        elif condif.flowGroups:
            return 'config/ixchariot/flowGroups/1/network/'
        else:
            return 'config/ixchariot/multicastGroups/1/network/'
