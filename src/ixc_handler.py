
import sys
import logging
import imp
import time
import os
import zipfile

from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext


class IxcHandler(object):

    def initialize(self, address, username, password, client_install_path):
        """
        """

        log_file = 'IXC_logger.log'
        logging.basicConfig(filename=log_file, level=logging.DEBUG)
        self.logger = logging.getLogger('log')
        self.logger.addHandler(logging.FileHandler(log_file))
        self.logger.setLevel('DEBUG')
        self.result = 0




        sys.path.append(client_install_path)
        webapi = imp.load_source('webapi', os.path.join(client_install_path, 'ixia/webapi.py'))
        self.ixchariotapi = imp.load_source('ixchariotapi', os.path.join(client_install_path, 'ixchariotApi.py'))

        self.connection = webapi.webApi.connect('https://' + address, 'v1', None, username, password)
        self.session = None

    def tearDown(self):
        if self.session:
            self.session.stopSession()

    def get_inventory(self):
        return AutoLoadDetails([], [])

    def load_config(self, api, reservation_id, ixc_config):
        """
        :param reservation_id: current reservation ID
        :param ixc_config: IxChariot configuration name.
        """

        self.session = self.connection.createSession('ixchariot')
        self.session.startSession()

        self.session.loadConfiguration(ixc_config)

        src_resources = []
        dst_resources = []
        reservation_details = api.GetReservationDetails(reservationId=reservation_id)
        for resource in reservation_details.ReservationDescription.Resources:
            self.logger.info("Resource name *******:%s"%(resource.ResourceModelName))
            if resource.ResourceFamilyName == 'IxChariot test IP':
                ep_name = resource.Name
                logical_name = api.GetAttributeValue(resourceFullPath=ep_name, attributeName="Logical Name").Value
                if logical_name.lower() in ['src', 'source']:
                    src_resources.append(ep_name.split('/')[1])
                elif logical_name.lower() in ['dst', 'destination']:
                    dst_resources.append(ep_name.split('/')[1])
                else:
                    self.logger.info('Ignore EP {} - logical name {} not in [src, source, dst, destination]'.
                                     format(ep_name, logical_name))

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

        self.logger.info("Load Configuration Completed")

    def start_test(self, blocking):
        """
        """

        if blocking == 'True':
            self.result = self.session.runTest()
        else:
            self.result = self.session.startTest()
            time.sleep(4)


    def stop_test(self):
        self.session.stopTest()

    def get_statistics(self, context, view_name):
        """
        :param context: the context the command runs on
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param view_name: IxChariot results view to retrieve (csv file name in c:/temp/ixChariotTestResults.zip).
        """


        filePath = "c:/temp/ixChariotTestResults.zip"

        with open(filePath, "wb+") as statsFile:
            self.connection.getStatsCsvZipToFile(self.result.testId, statsFile)

        archive = zipfile.ZipFile(filePath, 'r')
        csv = archive.read(view_name + '.csv')

        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()
        my_api.WriteMessageToReservationOutput(reservation_id, csv)

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
