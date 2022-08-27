import ast

from api import ClientAPI, ServerAPI
from console_interface import BaseConsoleInterface
from socketlib import BaseServer
from utils import WithLogger, call_with_lock


class MessageFormatError(BaseException):
    pass


class InternalLogicError(BaseException):
    pass


class CommandHandler(WithLogger):
    def __init__(self):
        WithLogger.__init__(self, "server")

    @call_with_lock
    def handle_command(self, command, api):
        if not isinstance(command, dict):
            raise MessageFormatError("Command must be a dict")

        self._logger.debug("Handle command: %s", command)

        method_name = command.pop("method", None)
        if not method_name:
            raise MessageFormatError("Need field 'method'")

        command = getattr(api, method_name, None)
        if not command:
            raise InternalLogicError("No such command: {}".format(method_name))

        self._logger.debug(
            "Calling method %s for api %s", command.__name__, api.__class__.__name__
        )
        return command()


class Server(BaseServer):
    def __init__(self, host, port):
        BaseServer.__init__(self, host, port)

        self._client_api = ClientAPI()

    def _handle_message(self, msg):
        # str to dict
        msg = ast.literal_eval(msg.decode("utf-8"))

        return command_handler.handle_command(msg, self._client_api)


class ServerConsoleInterface(BaseConsoleInterface, WithLogger):
    def __init__(self):
        BaseConsoleInterface.__init__(self, "server> ")
        WithLogger.__init__(self, "server")

        self._server_api = ServerAPI()

    def _handle_input(self, inp):
        self._logger.debug("Handle input: %s", inp)

        command = self.__parse_message(inp)

        try:
            return command_handler.handle_command(command, self._server_api)
        except BaseException as err:
            self._logger.error(err)
            return "% " + str(err)

    def __parse_message(self, msg) -> dict:
        command = dict()
        command["raw"] = msg
        command["method"] = "show_ballots"

        return command


if __name__ == "__main__":
    command_handler = CommandHandler()

    server = Server("localhost", 9_000)
    server.run_in_backround_thread()

    interface = ServerConsoleInterface()
    interface.run()
