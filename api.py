from utils import Signleton


class CommonStorage(Signleton):
    def __init__(self):
        Signleton.__init__(self)

        self.ballots = list()


class ClientAPI:
    def __init__(self):
        self._storage = CommonStorage.instance()

        self._HELP = "get bulletin\nupload ballot\nhelp"

    def help(self, command):
        return self._HELP

    def get_bulletin(self, command):
        return "get_bulletin {}".format(command)

    def upload_ballot(self, command):
        return "upload_ballot {}".format(command)


class ServerAPI:
    def __init__(self):
        self._storage = CommonStorage.instance()

        self._HELP = "show ballots\nsend ballots\nshow calculations"

    def help(self, command):
        return self._HELP

    def show_all_ballots(self, command):
        return "show_all_ballots {}".format(command)

    def send_ballots_to_admins(self, command):
        return "send_ballots_to_admins {}".format(command)

    def show_calculations(self, command):
        return "show_calculations {}".format(command)
