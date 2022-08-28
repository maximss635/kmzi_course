import argparse
import ast

from api import ClientAPI, ServerAPI
from socketlib import BaseServer
from utils import BaseConsoleInterface, WithLogger, call_with_lock


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
        BaseConsoleInterface.__init__(self, "server# ")
        WithLogger.__init__(self, "server")

        self._server_api = ServerAPI()

    def run(self):
        BaseConsoleInterface.run(self)

        self._logger.debug("Exit from server console")

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()

    command_handler = CommandHandler()

    try:
        server = Server(args.host, args.port)
        server.run_in_backround_thread()
    except OSError as err:
        print(err)
        exit(1)

    ServerConsoleInterface().run()
    server.stop()
