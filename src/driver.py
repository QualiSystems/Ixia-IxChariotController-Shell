
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.context_utils import get_resource_name
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from ixc_handler import IxcHandler


class IxChariotControllerDriver(ResourceDriverInterface):

    def __init__(self):
        self.handler = IxcHandler()

    def initialize(self, context):
        """
        :param context: ResourceCommandContext,ReservationContextDetailsobject with all Resource Attributes inside
        :type context:  context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        address = context.resource.address
        username = context.resource.attributes['User']
        password = context.resource.attributes['Password']
        client_install_path = context.resource.attributes['Client Install Path']
        self.handler.initialize(address, username, password, client_install_path)

    def get_inventory(self, context):
        """ Return device structure with all standard attributes

        :type context: cloudshell.shell.core.driver_context.AutoLoadCommandContext
        :rtype: cloudshell.shell.core.driver_context.AutoLoadDetails
        """

        return self.handler.get_inventory()

    def load_config(self, context, ixc_config):
        """ Load IxChariot configuration and select end points.

        :param context: the context the command runs on
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param ixc_config: IxChariot configuration name.
        """

        api = CloudShellSessionContext(context).get_api()
        reservation_id = context.reservation.reservation_id
        resource_name = get_resource_name(context=context)
        api.EnqueueCommand(reservationId=reservation_id, targetName=resource_name, commandName="keep_alive",
                           targetType="Resource")

        self.handler.load_config(api, reservation_id, ixc_config)
        return ''

    def start_test(self, context, blocking):
        """
        :param context: the context the command runs on
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.start_test(blocking)

    def stop_test(self, context):
        """
        :param context: the context the command runs on
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.stop_test()

    def get_statistics(self, context, view_name):
        self.handler.get_statistics(context, view_name)
        return ''

    def cleanup(self):
        self.handler.tearDown()
        pass

    def keep_alive(self, context, cancellation_context):

        while not cancellation_context.is_cancelled:
            pass
        if cancellation_context.is_cancelled:
            self.handler.tearDown()
