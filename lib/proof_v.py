from Crypto.Hash import SHAKE128

from lib.automorphism import phi
from lib.linear_alg import (inf_norm_matr, l2_norm_vect, matrix_vector, scalar,
                            vector_mult_by_scalar)
from lib.public import gen_public_b_with_extra
from lib.random_polynomials import (challenge, discrete_gaussian_vector_y,
                                    random_poly, random_poly_with_zeros,
                                    random_zq)
from lib.ring import INTT
from lib.utils import poly_to_bytes, randombytes, rejection_sampling_vector


def get_alpha_gamma(PP, t0, t1, t2, W):
    k = PP.k

    shake = SHAKE128.new()
    for i in range(PP.kappa):
        shake.update(poly_to_bytes(t0[i]))
    for i in range(PP.npoly):
        shake.update(poly_to_bytes(t1[i]))
    shake.update(poly_to_bytes(t2))
    for i in range(k):
        for j in range(PP.kappa):
            shake.update(poly_to_bytes(W[i][j]))
    ag_hash = shake.read(int(PP.seedlen))
    nonce = 0
    if k == 1:
        gamma, _ = random_poly(PP, ag_hash, nonce, PP.d // PP.l)
        return gamma, ag_hash
    else:
        alpha = [0] * (k * PP.npoly)
        for i in range(k * PP.npoly):
            alpha[i], nonce = random_poly(PP, ag_hash, nonce, PP.d)
        gamma, nonce = random_zq(PP, ag_hash, nonce, k)
        return alpha, gamma, ag_hash


def get_challenge_hash(PP, gamma_hash, t3, vpp, h, vulp):
    shake = SHAKE128.new()
    shake.update(gamma_hash)
    shake.update(poly_to_bytes(t3))
    shake.update(poly_to_bytes(vpp))
    shake.update(poly_to_bytes(h))
    if PP.k == 1:
        shake.update(poly_to_bytes(vulp))
    else:
        for i in range(PP.k):
            shake.update(poly_to_bytes(vulp[i]))
    c_hash = shake.read(int(PP.seedlen))
    return c_hash


def get_challenge(PP, c_hash):
    return challenge(PP, c_hash)


def check_z_len(PP, Z):
    for z in Z:
        if l2_norm_vect(z, PP.q) >= PP.beta1:
            return 1
    return 0


def _compute_single_z(PP, y, c, r):
    z = [0] * PP.baselen
    cr = [0] * PP.baselen
    for i in range(PP.baselen):
        cr[i] = (c * r[i]).mod(PP.X**PP.d + 1)
        z[i] = (y[i] + cr[i]).mod(PP.X**PP.d + 1)
    if (
        rejection_sampling_vector(z, cr, PP.sigma1, PP.average_rejection_tries1, PP.q)
        == 0
    ):
        return None, 1
    return z, 0


def _compute_z(PP, Y, c, r):
    Z = [0] * PP.k
    for i in range(PP.k):
        z, res_ok = _compute_single_z(PP, Y[i], c, r)
        if res_ok != 0:
            return None, res_ok
        Z[i] = z
        if PP.k != 1:
            c = phi(PP, c, 1)
    return Z, 0


def _compute_m_prime(PP):
    l = PP.l
    m_prime = [0] * PP.npoly
    for i in range(PP.npoly - 1):
        m_prime[i] = 1
    m_prime[PP.npoly - 1] = INTT(PP, [1] * (PP.Nc % l) + [0] * (l - (PP.Nc % l)))
    return m_prime


def proof_v(PP, t0, t1, r, m, public_seed):
    d = PP.d
    l = PP.l
    X = PP.X
    k = PP.k
    npoly = PP.npoly

    m_prime = _compute_m_prime(PP)
    B0, b = gen_public_b_with_extra(PP, public_seed)
    seed = randombytes(PP.seedlen)
    nonce = 0
    g, nonce = random_poly_with_zeros(PP, seed, nonce, d, PP.g_zeros)
    t2 = scalar(b[npoly], r, X, d) + g
    while True:
        Y = [0] * k
        W = [0] * k
        for i in range(PP.k):
            Y[i] = discrete_gaussian_vector_y(PP, PP.baselen, PP.sigma1)
            W[i] = matrix_vector(B0, Y[i], X, d)

        if k == 1:
            # PP.npoly should be 1
            y = Y[0]
            gamma, ag_hash = get_alpha_gamma(PP, t0, t1, t2, W)
            t3 = (
                scalar(b[npoly + 1], r, X, d)
                - (2 * m[0] - m_prime[0]) * scalar(b[0], y, X, d)
            ).mod(X**d + 1)
            vpp = (scalar(b[npoly + 1], y, X, d) + scalar(b[0], y, X, d) ** 2).mod(
                X**d + 1
            )
            intt_factor = gamma * l
            h = (g + intt_factor * m[0] - gamma).mod(X**d + 1)
            vulp = scalar(
                list((intt_factor * b[0][i] + b[npoly][i]) for i in range(PP.baselen)),
                y,
                X,
                d,
            )
        else:
            alpha, gamma, ag_hash = get_alpha_gamma(PP, t0, t1, t2, W)
            t3 = scalar(b[npoly + 1], r, X, d)
            vpp = scalar(b[npoly + 1], Y[0], X, d)
            for i in range(k):
                for j in range(npoly):
                    t3 -= (
                        alpha[i * npoly + j]
                        * phi(
                            PP,
                            ((2 * m[j] - m_prime[j]) * scalar(b[j], Y[i], X, d)).mod(
                                X**d + 1
                            ),
                            -i,
                        )
                    ).mod(X**d + 1)
                    vpp += (
                        alpha[i * npoly + j]
                        * phi(PP, (scalar(b[j], Y[i], X, d) ** 2).mod(X**d + 1), -i)
                    ).mod(X**d + 1)
            h = g
            for mu in range(k):
                coef = X**mu / k
                coef_inner = 0
                for nu in range(k):
                    coef_inner += phi(
                        PP,
                        (
                            d * gamma[mu] * sum(m[j] for j in range(npoly)) - gamma[mu]
                        ).mod(X**d + 1),
                        nu,
                    )
                h += (coef * coef_inner).mod(X**d + 1)
            vulp = [0] * k
            for i in range(k):
                for mu in range(k):
                    coef = X**mu / k
                    coef_inner = 0
                    for nu in range(k):
                        for j in range(npoly):
                            coef_inner += phi(
                                PP,
                                scalar(
                                    vector_mult_by_scalar(b[j], d * gamma[mu]),
                                    Y[(i - nu) % k],
                                    X,
                                    d,
                                ),
                                nu,
                            )
                    vulp[i] += (coef * coef_inner).mod(X**d + 1)
                vulp[i] += scalar(b[npoly], Y[i], X, d)

        c_hash = get_challenge_hash(PP, ag_hash, t3, vpp, h, vulp)
        c = get_challenge(PP, c_hash)

        Z, res_ok = _compute_z(PP, Y, c, r)
        if res_ok == 0 and inf_norm_matr(Z, PP.q) < PP.inf_bound1:
            break
    return (h, c_hash, Z), (t2, t3)


def verify_v(PP, proof, commitment, additional_com, public_seed):
    d = PP.d
    l = PP.l
    X = PP.X
    k = PP.k
    npoly = PP.npoly

    m_prime = _compute_m_prime(PP)
    B0, b = gen_public_b_with_extra(PP, public_seed)
    h, c_hash, Z = proof
    c = get_challenge(PP, c_hash)
    t0, t1 = commitment
    t2, t3 = additional_com
    if check_z_len(PP, Z):
        return 1
    W = [0] * k
    f1 = [0] * k
    f2 = [0] * k
    for i in range(k):
        B0z = matrix_vector(B0, Z[i], X, d)
        w = [0] * PP.kappa
        for j in range(PP.kappa):
            w[j] = (B0z[j] - c * t0[j]).mod(X**d + 1)
        W[i] = w

        f1[i] = list(
            (scalar(b[j], Z[i], X, d) - c * t1[j]).mod(X**d + 1) for j in range(npoly)
        )
        f2[i] = list(
            (scalar(b[j], Z[i], X, d) - c * (t1[j] - m_prime[j])).mod(X**d + 1)
            for j in range(npoly)
        )
        if k != 1:
            c = phi(PP, c, 1)

    f3 = (scalar(b[npoly + 1], Z[0], X, d) - c * t3).mod(X**d + 1)
    hlist = h.list()
    for i in range(PP.g_zeros):
        if hlist[i] != 0:
            return 1
    if k == 1:
        # PP.npoly should be 1
        gamma, ag_hash = get_alpha_gamma(PP, t0, t1, t2, W)
        vpp = (f1[0][0] * f2[0][0] + f3).mod(X**d + 1)
        intt_factor = l * gamma
        tau = (intt_factor * sum(t1[i] for i in range(npoly)) - gamma).mod(X**d + 1)
        vulp = (
            scalar(
                list(
                    (intt_factor * sum(b[j][i] for j in range(npoly)) + b[npoly][i])
                    for i in range(PP.baselen)
                ),
                Z[0],
                X,
                d,
            )
            - c * (tau + t2 - h)
        ).mod(X**d + 1)
    else:
        alpha, gamma, ag_hash = get_alpha_gamma(PP, t0, t1, t2, W)
        vpp = f3
        for i in range(k):
            for j in range(npoly):
                vpp += (
                    alpha[i * npoly + j]
                    * phi(PP, (f1[i][j] * f2[i][j]).mod(X**d + 1), -i)
                ).mod(X**d + 1)
        tau = 0
        for mu in range(k):
            coef = X**mu / k
            coef_inner = 0
            for nu in range(k):
                coef_inner += phi(
                    PP,
                    (d * gamma[mu] * sum(t1[j] for j in range(npoly)) - gamma[mu]).mod(
                        X**d + 1
                    ),
                    nu,
                )
            tau += (coef * coef_inner).mod(X**d + 1)
        vulp = [0] * k
        for i in range(k):
            for mu in range(k):
                coef = X**mu / k
                coef_inner = 0
                for nu in range(k):
                    for j in range(npoly):
                        coef_inner += phi(
                            PP,
                            scalar(
                                vector_mult_by_scalar(b[j], d * gamma[mu]),
                                Z[(i - nu) % k],
                                X,
                                d,
                            ),
                            nu,
                        )
                vulp[i] += (coef * coef_inner).mod(X**d + 1)
            vulp[i] += scalar(b[npoly], Z[i], X, d)
            vulp[i] -= (c * (tau + t2 - h)).mod(X**d + 1)
            c = phi(PP, c, 1)

    c_hash_prime = get_challenge_hash(PP, ag_hash, t3, vpp, h, vulp)
    if c_hash != c_hash_prime:
        return 1
    return 0


if __name__ == "__main__":
    from commit import commit
    from params import PublicParams
    from public import gen_public_b
    from utils import m_from_vote_arr

    public_seed = b'-\xc2\xbd\xc1\x12\x94\xac\xd0f\xab~\x9f\x13\xb5\xac\xcaT\xbaFgD\xa6\x93\xd9\x92\xf2"\xb5\x006\x02\xa3'

    PP = PublicParams(2, 129, 10)
    v = [0] * PP.Nc
    v[1] = 1
    m = m_from_vote_arr(PP, v)
    B0, b1 = gen_public_b(PP, public_seed)
    r_seed = randombytes(PP.seedlen)
    t0, t1, r, _ = commit(PP, B0, b1, m, r_seed, 0)

    proof, additional_com = proof_v(PP, t0, t1, r, m, public_seed)
    ver_result = verify_v(PP, proof, (t0, t1), additional_com, public_seed)
    if ver_result == 0:
        print("Verify is successfull")
    else:
        print("There is an error in verification")

    print("Trying negative scenarios")
    for v in ([1] * 2 + [0] * (PP.Nc - 2), [2] + [0] * (PP.Nc - 1)):
        m = m_from_vote_arr(PP, v)
        B0, b1 = gen_public_b(PP, public_seed)
        r_seed = randombytes(PP.seedlen)
        t0, t1, r, _ = commit(PP, B0, b1, m, r_seed, 0)

        proof, additional_com = proof_v(PP, t0, t1, r, m, public_seed)
        ver_result = verify_v(PP, proof, (t0, t1), additional_com, public_seed)
        assert ver_result == 1
