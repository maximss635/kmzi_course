import argparse
import json

from console_interface import BaseConsoleInterface
from socketlib import BaseClient, ErrorInServer, ServerNotAnswerError
from utils import WithLogger


class ClientConsoleInterface(BaseConsoleInterface, WithLogger):
    def __init__(self, host, port):
        BaseConsoleInterface.__init__(self, "client> ")
        WithLogger.__init__(self, filename="client")

        try:
            self.__client = BaseClient(host=host, port=port)
        except ConnectionRefusedError as err:
            self._logger.error(err)
            raise err

    def run(self):
        BaseConsoleInterface.run(self)

        self._logger.debug("Exit from client console")

    def _handle_input(self, inp) -> str:
        self._logger.debug("Handle input: %s", inp)

        msg = self.__parse_message(inp)

        try:
            return self.__client.send_message(msg)
        except ServerNotAnswerError as err:
            self._logger.error(err)
            return "Time out... not answer from server"
        except ErrorInServer as err:
            self._logger.error(err)
            return "% " + str(err)

    def __parse_message(self, raw_message):
        message = dict()
        message["raw"] = raw_message
        message["method"] = "add_ballot"

        return json.dumps(message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()

    try:
        interface = ClientConsoleInterface(host=args.host, port=args.port)
    except ConnectionRefusedError:
        print("% Server is unavailable")
        exit(1)

    interface.run()
