
import time

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from cloudshell.traffic.driver import TrafficControllerDriver

from ixc_handler import IxcHandler


class IxChariotControllerDriver(TrafficControllerDriver):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.handler = IxcHandler()

    def load_config(self, context, ixc_config):
        """ Load IxChariot configuration and select end points.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param ixc_config: IxChariot configuration name.
        """

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

    def end_session(self, context):
        self.handler.end_session()

    def del_session(self, context):
        self.handler.del_session()

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context):
        super(self.__class__, self).initialize(context)

    def cleanup(self):
        super(self.__class__, self).cleanup()

    def keep_alive(self, context, cancellation_context):
        super(self.__class__, self).keep_alive(context, cancellation_context)
