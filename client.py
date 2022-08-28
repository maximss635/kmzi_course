import argparse
import json

from socketlib import BaseClient, ErrorInServer, ServerNotAnswerError
from utils import BaseConsoleInterface, WithLogger


class LocalAPI(WithLogger):
    def show_ballot(self):
        return "show_ballot"


class ClientConsoleInterface(BaseConsoleInterface, WithLogger):
    def __init__(self, host, port):
        BaseConsoleInterface.__init__(self, "client> ")
        WithLogger.__init__(self, filename="client")

        self.api = LocalAPI()

        try:
            self.__client = BaseClient(host=host, port=port)
        except ConnectionRefusedError as err:
            self._logger.error(err)
            raise err

    def run(self):
        try:
            BaseConsoleInterface.run(self)
        except ConnectionRefusedError as err:
            self._print("% Error with connection to the server")
            self._logger.error(err)

        self._logger.debug("Exit from client console")

    def _handle_input(self, inp) -> str:
        self._logger.debug("Handle input: %s", inp)

        try:
            msg, remote = self.__parse_message(inp)
        except SyntaxError as err:
            err_msg = "% Syntax error"
            if err.args:
                err_msg += ": " + err.args
            self._logger.error(err_msg)
            return err_msg

        self._logger.debug(
            "Packing %s command: %s", "remote" if remote else "local", msg
        )

        if not remote:
            return getattr(self.api, msg)()

        try:
            return self.__client.send_message(msg)
        except ServerNotAnswerError as err:
            self._logger.error(err)
            return "Time out... not answer from server"
        except ErrorInServer as err:
            self._logger.error(err)
            return "% " + str(err)

    def __parse_message(self, raw_message) -> (str, bool):
        message = dict()
        raw_message = raw_message.strip()
        message["raw"] = raw_message

        if raw_message in ["help", "?"]:
            message["method"] = "help"
            return json.dumps(message), True
        if raw_message.startswith("show"):
            raw_message = raw_message.split(" ")
            raw_message = [i for i in raw_message if i]
            if len(raw_message) != 2:
                raise SyntaxError()
            if raw_message[1] == "ballot":
                return "show_ballot", False
            raise SyntaxError()
        if raw_message.startswith("get"):
            raw_message = raw_message.split(" ")
            raw_message = [i for i in raw_message if i]
            if len(raw_message) != 2:
                raise SyntaxError()
            if raw_message[1] != "bulletin":
                raise SyntaxError()
            message["method"] = "get_bulletin"
            return json.dumps(message), True
        if raw_message.startswith("upload"):
            raw_message = raw_message.split(" ")
            raw_message = [i for i in raw_message if i]
            if len(raw_message) != 2:
                raise SyntaxError()
            if raw_message[1] != "ballot":
                raise SyntaxError
            message["method"] = "upload_ballot"
            return json.dumps(message), True

        raise SyntaxError()


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
