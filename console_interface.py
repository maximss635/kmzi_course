from utils import WithLogger


class BaseConsoleInterface:
    def __init__(self, prommt):
        self.__prommt = prommt

    @staticmethod
    def _print(output):
        print(output)

    def run(self):
        while True:
            try:
                inp = input(self.__prommt)
            except (EOFError, KeyboardInterrupt):
                break

            if not inp:
                continue

            output = self._handle_input(inp)
            if output:
                self._print(output)

    def _handle_input(self, inp):
        pass
