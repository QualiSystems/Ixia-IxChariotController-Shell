
import sys
import imp
import time
import os
import zipfile

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from cloudshell.traffic.tg_helper import get_reservation_resources, attach_stats_csv


class IxcHandler(object):

    def initialize(self, context, logger):

        self.logger = logger

        address = context.resource.attributes['Controller Address']
        username = context.resource.attributes['User']
        encripted_password = context.resource.attributes['Password']
        password = CloudShellSessionContext(context).get_api().DecryptPassword(encripted_password).Value
        client_install_path = context.resource.attributes['Client Install Path']

        sys.path.append(client_install_path)
        self.logger.info(os.path.join(client_install_path, 'ixia/webapi.py'))
        webapi = imp.load_source('webapi', os.path.join(client_install_path, 'ixia/webapi.py'))
        self.ixchariotapi = imp.load_source('ixchariotapi', os.path.join(client_install_path, 'ixchariotApi.py'))

        self.connection = webapi.webApi.connect('https://' + address, 'v1', None, username, password)
        self.session = None

    def tearDown(self):
        self.del_session()

    def load_config(self, context, ixc_config):

        self.session = self.connection.createSession('ixchariot')
        self.session.startSession()
        self.session.loadConfiguration(ixc_config)

        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()

        src_resources = {}
        dst_resources = {}
        mips = {}
        for tip in get_reservation_resources(my_api, reservation_id, 'Traffic Generator Test IP'):
            ep = my_api.GetResourceDetails('/'.join(tip.Name.split('/')[:-1]))
            logical_name = my_api.GetAttributeValue(tip.Name, 'Logical Name').Value.strip()
            for end in logical_name.split():
                flow_end = end.split('-')[0].lower()
                flow_index = int(end.split('-')[1]) if len(end.split('-')) == 2 else 1
                if flow_end in ['src', 'source']:
                    mips[tip.Name] = my_api.GetAttributeValue(ep.Name, 'Management IP').Value
                    src_resources.setdefault(flow_index, []).append(tip.Name)
                elif flow_end in ['dst', 'destination']:
                    mips[tip.Name] = my_api.GetAttributeValue(ep.Name, 'Management IP').Value
                    dst_resources.setdefault(flow_index, []).append(tip.Name)
                else:
                    raise Exception('Invalid logical name {} - {} not in [src, source, dst, destination]'.
                                    format(logical_name, flow_end))

        flows_url = self._get_flows_url()
        flows = self.session.httpGet(flows_url)
        ids = [f.id for f in flows]
        if sorted(src_resources) != sorted(ids):
            raise Exception('Src resource ids {} do not match flow IDs {}'.format(src_resources, ids))
        if sorted(dst_resources) != sorted(ids):
            raise Exception('Dst resource ids {} do not match flow IDs {}'.format(dst_resources, ids))
        for id_ in ids:
            network_url = '{}/{}/network/'.format(flows_url, id_)
            self.session.httpDelete(network_url + 'sourceEndpoints')
            self.session.httpDelete(network_url + 'destinationEndpoints')

        for id_ in src_resources:
            for src_ep in src_resources[id_]:
                ep = self.ixchariotapi.createEndpoint(src_ep.split('/')[2], mips[src_ep])
                self.session.httpPost('{}/{}/network/sourceEndpoints'.format(flows_url, id_), data=ep)

        for id_ in dst_resources:
            for dst_ep in dst_resources[id_]:
                ep = self.ixchariotapi.createEndpoint(dst_ep.split('/')[2], mips[dst_ep])
                self.session.httpPost('{}/{}/network/destinationEndpoints'.format(flows_url, id_), data=ep)

        # In case of multiple eps delay is required to make sure configuration completed (based on trial and error).
        time.sleep(4)
        self.logger.info("Load Configuration Completed")

        return self.session.sessionId

    def start_test(self, blocking):
        if blocking.lower().strip() == 'true':
            self.result = self.session.runTest()
        else:
            self.result = self.session.startTest()
            time.sleep(4)

    def stop_test(self):
        self.session.stopTest()

    def get_statistics(self, context, view_name, output_type):

        reservation_id = context.reservation.reservation_id
        ts = time.ctime().replace(' ', '_').replace(':', '-')
        filename = 'c:/temp/IxChariotShellResults/{}/{}'.format(reservation_id, ts)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        if output_type == 'CSV':
            filename += '.zip'
            with open(filename, "wb+") as statsFile:
                self.connection.getStatsCsvZipToFile(self.result.testId, statsFile)
            archive = zipfile.ZipFile(filename, 'r')
            output = archive.read(view_name + '.csv')
            attach_stats_csv(context, self.logger, view_name, output)
            return output
        else:
            filename += '.pdf'
            self.ixchariotapi.generatePdfReport(self.connection, filename, 1, True, True, True, False, False, 0)
            with open(filename, "r") as statsFile:
                output = statsFile.read()
            return attach_stats_csv(context, self.logger, view_name, output, 'pdf')

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

    def _get_flows_url(self):
        config = self.session.httpGet('config/ixchariot')
        if config.appMixes:
            return 'config/ixchariot/appMixes'
        elif config.flowGroups:
            return 'config/ixchariot/flowGroups'
        else:
            return 'config/ixchariot/multicastGroups'
