from prettytable import PrettyTable

from lib.main import main as run_all
from lib.params import PublicParams
from utils import Signleton


def make_json(func):
    def wrap(*args, **kwargs):
        return {"output": func(*args, **kwargs)}
    return wrap


class CommonStorage(Signleton):
    def __init__(self):
        Signleton.__init__(self)

        self.ballots = list()


class ClientAPI:
    def __init__(self):
        self._storage = CommonStorage.instance()

        self._HELP = "get bulletin\nupload ballot\nshow ballot\nhelp"

    @make_json
    def help(self, command):
        return self._HELP

    def get_bulletin(self, command):
        # TODO Разобраться - наверное здесь надо генерить случайным образом
        votes = [
            [1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1],
            [0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0],
        ]

        bulletin = dict()

        # Generate trusted public parameter
        bulletin["public_seed"] = "\xc2\x84\x80y\xef\xfew\xaf\n\x03\x95h\xa1\xee\xda}D\xbf\x87\x10a\xf3\xc6\x92\xe7\xa3\xa3\x9dTR\tY"

        # Number of authorities
        bulletin["Na"] = 2

        # Number of candidates
        bulletin["Nc"] = 5

        # Number of voters
        bulletin["Nv_max"] = 10  # max

        PP = PublicParams(bulletin["Na"], bulletin["Nc"], bulletin["Nv_max"])

        return bulletin

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
