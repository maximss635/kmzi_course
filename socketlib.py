import ast
import json
import logging
import select
import socket
import threading
from copy import copy

from utils import WithLogger


class ServerNotAnswerError(BaseException):
    pass


class ErrorInServer(BaseException):
    pass


class BaseServer(WithLogger):
    def __init__(self, host, port):
        WithLogger.__init__(self, "server")

        self.__host = host
        self.__port = port

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._connections = dict()  # [socket, addr]
        self._connections[self._server_socket] = "0.0.0.0"

        self._flag_stop = False
        self._thread = None

        self._logger.debug("Init server, host=%s, port=%d", self.__host, self.__port)

    def __del__(self):
        self._server_socket.close()
        self._connections.pop(self._server_socket)

        for s in copy(self._connections):
            self._on_close_connection(s)

    def _event_loop(self):
        while not self._flag_stop:
            events, _, _ = select.select(self._connections.keys(), [], [], 0.2)
            for event in events:
                if event is self._server_socket:
                    self._on_open_connection()
                else:
                    self._on_new_message(event)

    def _on_open_connection(self):
        cli_socket, cli_addr = self._server_socket.accept()
        self._logger.debug("New connection: %s", cli_addr)
        self._connections[cli_socket] = cli_addr

    def _on_new_message(self, event):
        data = event.recv(512)
        SOCKET_LOGGER.debug("[srv recv] {}".format(data))

        if not data:
            self._on_close_connection(event)
            return

        self._logger.debug("New message from %s: %s", self._connections[event], data)

        # Handle message
        try:
            answer_json = self._handle_message(data)
            answer_json["ret_code"] = 0
        except BaseException as err:
            self._logger.error("Exception while handle message: %s", err)
            answer_json = dict()
            answer_json["output"] = str(err)
            answer_json["ret_code"] = 1

        self._logger.debug("answer_json={}".format(answer_json))

        raw_answer = bytes(json.dumps(answer_json), "utf-8")
        self._logger.debug(
            "Send answer to %s: %s",
            self._connections[event],
            raw_answer
        )
        event.send(raw_answer)
        SOCKET_LOGGER.debug("[srv send] {}".format(raw_answer))

    def _on_close_connection(self, event):
        self._logger.debug("Close connection with %s", self._connections[event])
        event.close()
        self._connections.pop(event)

    def _handle_message(self, msg):
        return "OK"

    def _prerun_init(self):
        try:
            self._server_socket.bind((self.__host, self.__port))
            self._server_socket.listen()
            self._server_socket.setblocking(False)
        except OSError as err:
            self._logger.debug(err)
            raise err

    def run(self):
        self._logger.debug("Start listening")
        self._prerun_init()
        self._event_loop()

    def run_in_backround_thread(self):
        self._logger.debug("Start listening")
        self._prerun_init()
        self._thread = threading.Thread(target=self._event_loop)
        self._thread.start()

    def stop(self):
        if self._thread:
            self._flag_stop = True


class BaseClient(WithLogger):
    def __init__(self, host, port, timeout=1):
        WithLogger.__init__(self, "client")

        self.__host = host
        self.__port = port

        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.settimeout(timeout)
        self._s.connect((self.__host, self.__port))

        self._logger.debug("Init client")

    def __del__(self):
        self._s.close()

    def send_message(self, msg):
        if isinstance(msg, str):
            msg = bytes(msg, "utf-8")

        self._logger.debug("Send mesage: %s", msg)
        self._s.send(msg)
        SOCKET_LOGGER.debug("[cli send] {}".format(msg))

        try:
            answer = self._s.recv(512)
        except TimeoutError as err:
            self._logger.error("Not answer from server")
            raise ServerNotAnswerError() from err

        if not answer:
            raise ConnectionRefusedError()

        SOCKET_LOGGER.debug("[cli recv] {}".format(answer))
        try:
            answer = ast.literal_eval(answer.decode("utf-8"))
        except ValueError as err:
            raise ErrorInServer("Bad answer: {}".format(answer)) from err

        if "ret_code" not in answer:
            raise ErrorInServer("No field 'ret_code' in answer from server")

        ret_code = answer["ret_code"]
        output = answer.get("output", "")

        if output:
            self._logger.debug("Get answer: %s (ret_code=%d)", output.replace("\n", "\\n"), ret_code)
        else:
            self._logger.warning("Answer is empty")

        if ret_code != 0:
            raise ErrorInServer(output)

        return output


SOCKET_LOGGER = logging.getLogger("SOCKET_LOGGER")
handler = logging.FileHandler("logs/socket_history.log")
handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
SOCKET_LOGGER.addHandler(handler)
SOCKET_LOGGER.setLevel(logging.DEBUG)
