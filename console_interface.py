class BaseConsoleInterface:
    def __init__(self, prommt):
        self.__prommt = prommt
        self._flag_run = True

    def stop(self):
        self._flag_run = False

    @staticmethod
    def _print(output):
        print(output)

    def _base_parse(self, inp):
        if (inp == "exit") or (inp == "exi") or (inp == "ex"):
            self.stop()

    def run(self):
        while self._flag_run:
            try:
                inp = input(self.__prommt)
            except (EOFError, KeyboardInterrupt):
                break

            self._base_parse(inp)

            if not inp:
                continue

            output = self._handle_input(inp)
            if output:
                self._print(output)

    def _handle_input(self, inp):
        pass
