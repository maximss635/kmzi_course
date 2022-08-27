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

        self._logger.debug("Init server")

    def __del__(self):
        for s in copy(self._connections):
            self._on_close_connection(s)

    def _event_loop(self):
        while True:
            events, _, _ = select.select(self._connections.keys(), [], [])
            for event in events:
                if event is self._server_socket:
                    self._on_open_connection()
                else:
                    self._on_new_message(event)

    def _on_open_connection(self):
        cli_socket, cli_addr = self._server_socket.accept()
        self._logger.debug("New connection: %s", cli_addr[0])
        self._connections[cli_socket] = cli_addr[0]

    def _on_new_message(self, event):
        data = event.recv(512)

        if not data:
            self._on_close_connection(event)
            return

        self._logger.debug("New message from %s: %s", self._connections[event], data)

        # Handle message
        try:
            answer = self._handle_message(data)
            ret_code = 0
        except BaseException as err:
            self._logger.error("Exception while handle message: %s", err)
            answer = str(err)
            ret_code = 1

        raw_answer = ret_code.to_bytes(1, byteorder="big")
        if answer:
            raw_answer += bytes(answer, "utf-8")

        self._logger.debug(
            "Send answer to %s: %s (ret_code=%d)",
            self._connections[event],
            answer,
            ret_code,
        )
        event.send(raw_answer)

    def _on_close_connection(self, event):
        self._logger.debug("Close connection with %s", self._connections[event])
        event.close()
        self._connections.pop(event)

    def _handle_message(self, msg):
        return "OK"

    def run(self):
        self._logger.debug("Start listening")

        try:
            self._server_socket.bind((self.__host, self.__port))
        except OSError as err:
            self._logger.error(err)
            return

        self._server_socket.listen()
        self._event_loop()

    def run_in_backround_thread(self):
        self._logger.debug("Start listening")

        try:
            self._server_socket.bind((self.__host, self.__port))
        except OSError as err:
            self._logger.error(err)
            return

        self._server_socket.listen()
        threading.Thread(target=self._event_loop).start()


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

        try:
            answer = self._s.recv(512)
        except TimeoutError as err:
            self._logger.error("Not answer from server")
            raise ServerNotAnswerError() from err

        ret_code = int(answer[0])
        answer = answer[1:].decode("utf-8")

        if answer:
            self._logger.debug("Get answer: %s (ret_code=%d)", answer, ret_code)
        else:
            self._logger.warning("Answer is empty")

        if ret_code != 0:
            raise ErrorInServer(answer)

        return answer
