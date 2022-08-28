from lib.params import PublicParams
from lib.utils import max_with_index, reset_all
from lib.voting_classes import BBoard
from lib.voting_scheme import tally_all, tally_j, testballots, verify, vote

"""
Parameters:
    PP - public parameters
    BB - bulletin board - entity operating committed bulletins
    votes - list of votes
    public_seed - trusted public parameter
"""


def emulate_voting(PP, BB, votes, public_seed):
    Nv = len(votes)
    print("creating votes")

    # on Nv clients, send result to BB
    # creating votes
    # they are posted to the bulletin board
    # secured transport protocol should be used to transfer ballots to BB
    for i in range(Nv):
        print(f"\tvoter {i} casting {votes[i]}")
        vote(PP, i, votes[i], public_seed, BB)

    # on Na authority servers
    # each authority must test ballots on BB for validity
    # test uses VProof zero-knowledge proof
    # only after that ballots are considered valid
    # tallying authorities can be offline during this stage
    print("testing ballots")
    for j in range(PP.Na):
        testballots(PP, j, public_seed, BB)

    # on Na authority servers
    # tallying votes
    # after total tally is computed, tallying authorities publish result and zero-knowledge proof
    print("creating tallies")
    for j in range(PP.Na):
        print(f"\tauthority {j} creating tally")
        tally_j(PP, j, public_seed, BB)
    print("computing total results")

    # on Na authority servers or one trusted server
    # total result is counted using homomorphic operations
    res = tally_all(PP, public_seed, BB)
    winner_votes, winner_indexes = max_with_index(res)
    winner_indexes = ", ".join(str(x) for x in winner_indexes)
    print(
        f'results of voting:\n{res}\nWinner is candidate(s) "{winner_indexes}" with {winner_votes} votes'
    )

    # everyone (including voters) can check correctness of result using public parameters
    ver_result = verify(PP, res, public_seed, BB)
    if ver_result == 0:
        print("Voting is successfull")
    else:
        print("There is an error in voting")


def vote_from_candidate(Nc, candidate):
    v = [0] * Nc
    v[candidate] = 1
    return v


def main():
    # Generate trusted public parameter
    public_seed = b"\xc2\x84\x80y\xef\xfew\xaf\n\x03\x95h\xa1\xee\xda}D\xbf\x87\x10a\xf3\xc6\x92\xe7\xa3\xa3\x9dTR\tY"

    # Number of authorities
    Na = 2
    authorities = list(range(Na))

    # Number of voters
    Nv_max = 10  # max
    Nv = 6  # current
    assert Nv <= Nv_max

    CA = {}
    BB = BBoard(CA, authorities)

    # Number of candidates
    Nc = 5

    # Voters' choices (only one '1' is allowed, otherwise - cheating)
    votes = [
        [
            1,
            0,
            0,
            0,
            0,
        ],  # if [2, 0, ...] or [1, 1, 0, 0, ...], bulletin will be dropped out
        [0, 0, 0, 0, 1],
        [0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0],
    ]
    assert len(votes) == Nv

    # Generate public parameters
    PP = PublicParams(Na, Nc, Nv_max)

    emulate_voting(PP, BB, votes, public_seed)


if __name__ == "__main__":
    main()
