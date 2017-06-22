
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

import tg_helper
from ixc_handler import IxcHandler


class IxChariotControllerDriver(ResourceDriverInterface):

    def __init__(self):
        self.handler = IxcHandler()

    def initialize(self, context):
        """
        :param context: ResourceCommandContext,ReservationContextDetailsobject with all Resource Attributes inside
        :type context:  context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        address = context.resource.attributes['Controller Address']
        username = context.resource.attributes['User']
        password = context.resource.attributes['Password']
        client_install_path = context.resource.attributes['Client Install Path']
        self.handler.initialize(address, username, password, client_install_path)

    def load_config(self, context, ixc_config):
        """ Load IxChariot configuration and select end points.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param ixc_config: IxChariot configuration name.
        """

        tg_helper.enqueue_keep_alive(context)
        session_id = self.handler.load_config(context, ixc_config)
        my_api = CloudShellSessionContext(context).get_api()
        my_api.WriteMessageToReservationOutput(context.reservation.reservation_id,
                                               ixc_config + ' loaded, endpoints reserved')
        return session_id

    def start_test(self, context, blocking):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.start_test(blocking)

    def stop_test(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.stop_test()

    def get_statistics(self, context, view_name):
        return self.handler.get_statistics(context, view_name)

    def cleanup(self):
        self.handler.tearDown()
        pass

    def keep_alive(self, context, cancellation_context):

        while not cancellation_context.is_cancelled:
            pass
        if cancellation_context.is_cancelled:
            self.handler.tearDown()
