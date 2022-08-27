import json

from console_interface import BaseConsoleInterface
from utils import WithLogger
from socketlib import BaseClient, ServerNotAnswerError, ErrorInServer


class ClientConsoleInterface(BaseConsoleInterface, WithLogger):
    def __init__(self):
        BaseConsoleInterface.__init__(self, "client> ")
        WithLogger.__init__(self, filename="client")

        try:
            self.__client = BaseClient(host="localhost", port=9_000)
        except ConnectionRefusedError as err:
            self._logger.error(err)
            raise err

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

        return json.dumps(message)


if __name__ == '__main__':
    try:
        interface = ClientConsoleInterface()
    except ConnectionRefusedError:
        print("% Server is unavailable")
        exit(1)

    interface.run()
