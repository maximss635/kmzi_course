from utils import Signleton


class CommonStorage(Signleton):
    def __init__(self):
        Signleton.__init__(self)

        self.ballots = list()


class ClientAPI:
    def add_ballot(self):
        CommonStorage.instance().ballots.append(len(CommonStorage.instance().ballots))


class ServerAPI:
    def show_ballots(self):
        return str(CommonStorage.instance().ballots)
