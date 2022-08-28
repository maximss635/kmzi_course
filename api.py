from utils import Signleton


class CommonStorage(Signleton):
    def __init__(self):
        Signleton.__init__(self)

        self.ballots = list()


class ClientAPI:
    def __init__(self):
        self._storage = CommonStorage.instance()

    def add_ballot(self):
        self._storage.ballots.append(len(self._storage.ballots))


class ServerAPI:
    def __init__(self):
        self._storage = CommonStorage.instance()

    def show_ballots(self):
        return str(self._storage.ballots)
