from utils import Signleton
from lib.main import main as run_all
from prettytable import PrettyTable


class CommonStorage(Signleton):
    def __init__(self):
        Signleton.__init__(self)

        self.ballots = list()


class ClientAPI:
    def __init__(self):
        self._storage = CommonStorage.instance()

        self._HELP = "get bulletin\nupload ballot\nshow ballot\nhelp"

    def help(self, command):
        return self._HELP

    def get_bulletin(self, command):
        return "get_bulletin {}".format(command)

    def upload_ballot(self, command):
        return "upload_ballot {}".format(command)


class ServerAPI:
    def __init__(self, server):
        self._storage = CommonStorage.instance()
        self._server = server
        self._HELP = "show clients\nshow ballots\nsend ballots\nshow calculations\nhelp"

    def help(self, command):
        return self._HELP

    def show_all_ballots(self, command):
        run_all()
        return "show_all_ballots {}".format(command)

    def send_ballots_to_admins(self, command):
        return "send_ballots_to_admins {}".format(command)

    def show_calculations(self, command):
        return "show_calculations {}".format(command)

    def show_clients(self, command):
        table = PrettyTable()
        table.field_names = ["Host", "Port"]
        for host, port in self._server.get_connections():
            table.add_row([host, port])

        return str(table)
