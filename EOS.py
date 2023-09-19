# calcluates EOS and absorption for forsterite
# fully in SI units
import uuid
import matplotlib.pyplot as plt
import numpy as np
import woma
from tqdm import tqdm

np.set_printoptions(precision=4)
from scipy.interpolate import RegularGridInterpolator, interp1d
from scipy.optimize import minimize, root
from multiprocessing import Pool

import sys
import os

sys.path.append(f'{os.getcwd()}/aneos-forsterite-2019-1.0.0')
import eostable

print('Loading EOS tables...')

# loads the eos table from file
NewEOS_fst = eostable.extEOStable()  # FIRST make new empty EOS object
NewEOS_iron = eostable.extEOStable()  # FIRST make new empty EOS object


def load_fst_EOS():

    # LOAD EXTENDED 301 SESAME FILE GENERATED BY STSM VERSION OF ANEOS
    NewEOS_fst.loadextsesame('aneos-forsterite-2019-1.0.0/NEW-SESAME-EXT.TXT')
    # LOAD STANDARD 301 SESAME FILE GENERATED BY STSM VERSION OF ANEOS
    NewEOS_fst.loadstdsesame('aneos-forsterite-2019-1.0.0/NEW-SESAME-STD.TXT')

    NewEOS_fst.MODELNAME = 'Forsterite-ANEOS-SLVTv1.0G1'  # string set above in user input
    NewEOS_fst.MDQ = np.zeros((NewEOS_fst.NT, NewEOS_fst.ND))  # makes the empty MDQ array

    NewEOS_fst.MATID = 1.0
    NewEOS_fst.DATE = 190802
    NewEOS_fst.VERSION = 0.1
    NewEOS_fst.FMN, NewEOS_fst.FMW = 70., 140.691
    NewEOS_fst.R0REF, NewEOS_fst.K0REF = 3.22, 1.1E12
    NewEOS_fst.T0REF, NewEOS_fst.P0REF = 298., 1.E6

    NewEOS_fst.loadaneos(aneosinfname='aneos-forsterite-2019-1.0.0/ANEOS.INPUT',
                         aneosoutfname='aneos-forsterite-2019-1.0.0/ANEOS.OUTPUT', silent=True)

    # change units to SI
    NewEOS_fst.rho = NewEOS_fst.rho * 1e3
    NewEOS_fst.P, NewEOS_fst.S = NewEOS_fst.P * 1e9, NewEOS_fst.S * 1e6
    NewEOS_fst.U = NewEOS_fst.U * 1e6
    NewEOS_fst.cs = NewEOS_fst.cs * 1e2

    NewEOS_fst.vc.Sl, NewEOS_fst.vc.Sv = NewEOS_fst.vc.Sl * 1e6, NewEOS_fst.vc.Sv * 1e6
    NewEOS_fst.vc.Pl, NewEOS_fst.vc.Pv = NewEOS_fst.vc.Pl * 1e9, NewEOS_fst.vc.Pv * 1e9
    NewEOS_fst.vc.rl = NewEOS_fst.vc.rl * 1e3
    NewEOS_fst.cp.P, NewEOS_fst.cp.S = NewEOS_fst.cp.P * 1e9, NewEOS_fst.cp.S * 1e6


def load_iron_EOS():
    # LOAD EXTENDED 301 SESAME FILE GENERATED BY STSM VERSION OF ANEOS
    NewEOS_iron.loadextsesame('aneos-iron-2020-1.0/NEW-SESAME-EXT.TXT')
    # LOAD STANDARD 301 SESAME FILE GENERATED BY STSM VERSION OF ANEOS
    NewEOS_iron.loadstdsesame('aneos-iron-2020-1.0/NEW-SESAME-STD.TXT')

    NewEOS_iron.MODELNAME = 'Forsterite-ANEOS-SLVTv1.0G1'  # string set above in user input
    NewEOS_iron.MDQ = np.zeros((NewEOS_iron.NT, NewEOS_iron.ND))  # makes the empty MDQ array

    NewEOS_iron.MATID = 1.0
    NewEOS_iron.DATE = 191105
    NewEOS_iron.VERSION = 0.2
    NewEOS_iron.FMN, NewEOS_iron.FMW = 26., 55.847
    NewEOS_iron.R0REF, NewEOS_iron.K0REF = 8.06, 1.51E12
    NewEOS_iron.T0REF, NewEOS_iron.P0REF = 298., 1.E6

    NewEOS_iron.loadaneos(aneosinfname='aneos-iron-2020-1.0/ANEOS.INPUT',
                         aneosoutfname='aneos-iron-2020-1.0/ANEOS.OUTPUT', silent=True)

    # change units to SI
    NewEOS_iron.rho = NewEOS_iron.rho * 1e3
    NewEOS_iron.P, NewEOS_iron.S = NewEOS_iron.P * 1e9, NewEOS_iron.S * 1e6
    NewEOS_iron.U = NewEOS_iron.U * 1e6
    NewEOS_iron.cs = NewEOS_iron.cs * 1e2

    NewEOS_iron.vc.Sl, NewEOS_iron.vc.Sv = NewEOS_iron.vc.Sl * 1e6, NewEOS_iron.vc.Sv * 1e6
    NewEOS_iron.vc.Pl, NewEOS_iron.vc.Pv = NewEOS_iron.vc.Pl * 1e9, NewEOS_iron.vc.Pv * 1e9
    NewEOS_iron.vc.rl = NewEOS_iron.vc.rl * 1e3
    NewEOS_iron.cp.P, NewEOS_iron.cp.S = NewEOS_iron.cp.P * 1e9, NewEOS_iron.cp.S * 1e6


load_fst_EOS()
load_iron_EOS()


# EQUATION OF STATE CALCULATIONS HERE #


method = 'linear'
u_fst_interp = RegularGridInterpolator((NewEOS_fst.rho, NewEOS_fst.T), NewEOS_fst.U.T, method=method, bounds_error=False, fill_value=np.NaN)
P_fst_interp = RegularGridInterpolator((NewEOS_fst.rho, NewEOS_fst.T), NewEOS_fst.P.T, method=method, bounds_error=False, fill_value=np.NaN)
S_fst_interp = RegularGridInterpolator((NewEOS_fst.rho, NewEOS_fst.T), NewEOS_fst.S.T, method=method, bounds_error=False, fill_value=np.NaN)
cs_fst_interp = RegularGridInterpolator((NewEOS_fst.rho, NewEOS_fst.T), NewEOS_fst.cs.T, method=method, bounds_error=False, fill_value=np.NaN)

rho_fst_interp, T_fst_interp = lambda x: np.full_like(x, np.NaN), lambda x: np.full_like(x, np.NaN)
T2_fst_interp, T2_iron_interp = lambda x: np.full_like(x, np.NaN), lambda x: np.full_like(x, np.NaN)

u_iron_interp = RegularGridInterpolator((NewEOS_iron.rho, NewEOS_iron.T), NewEOS_iron.U.T, method=method, bounds_error=False, fill_value=np.NaN)
P_iron_interp = RegularGridInterpolator((NewEOS_iron.rho, NewEOS_iron.T), NewEOS_iron.P.T, method=method, bounds_error=False, fill_value=np.NaN)
S_iron_interp = RegularGridInterpolator((NewEOS_iron.rho, NewEOS_iron.T), NewEOS_iron.S.T, method=method, bounds_error=False, fill_value=np.NaN)
cs_iron_interp = RegularGridInterpolator((NewEOS_iron.rho, NewEOS_iron.T), NewEOS_iron.cs.T, method=method, bounds_error=False, fill_value=np.NaN)


def globalize(func):
    def result(*args, **kwargs):
        return func(*args, **kwargs)
    result.__name__ = result.__qualname__ = uuid.uuid4().hex
    setattr(sys.modules[result.__module__], result.__name__, result)
    return result


def frac_error(x1, x2):
    return np.abs(x1 - x2) / x2


def reverse_EOS_table_X_Y(interpolatorX, tableX, interpolatorY, tableY, X, Y):

    # find the closest rho and T indexes
    table_error = np.sqrt(frac_error(tableX, X) ** 2 + frac_error(tableY, Y) ** 2)
    k = table_error.argmin()
    ncol = table_error.shape[1]
    i, j = int(k / ncol), int(k % ncol)
    rho_guess, T_guess = NewEOS_fst.rho[j], NewEOS_fst.T[i]

    # function to minimize
    X_func = lambda z: interpolatorX(z[0], z[1])
    Y_func = lambda z: interpolatorY(z[0], z[1])
    error = lambda z: frac_error(X_func(z), X) ** 2 + frac_error(Y_func(z), Y) ** 2

    res = minimize(error, np.array([rho_guess, T_guess]), method='Nelder-Mead')
    rho_res, T_res = res.x

    # calculates the error for checking
    X_check = interpolatorX(rho_res, T_res)
    Y_check = interpolatorY(rho_res, T_res)
    check_error = np.sqrt(frac_error(X_check, X) ** 2 + frac_error(Y_check, Y) ** 2)

    return rho_res, T_res, check_error


S_range, log_P_range = [1000, 20000], [-4, 13]


def generate_table_S_P(load_from_file=False, n=10):
    global rho_fst_interp, T_fst_interp

    if load_from_file:
        print('Loading SP EOS table...')
        rho_table = np.load(f'EOS_tables/rho_SP_table_n_{n}.npy', allow_pickle=True)
        T_table = np.load(f'EOS_tables/T_SP_table_n_{n}.npy', allow_pickle=True)

    # produces table points to be calculated
    S = np.linspace(S_range[0], S_range[1], num=n)  # in J/K/kg
    logP = np.linspace(log_P_range[0], log_P_range[1], num=n)  # in log10(Pa)
    x, y = np.meshgrid(S, logP)

    if not load_from_file:
        rho_table, T_table = np.zeros_like(x), np.zeros_like(x)
        error_table = np.zeros_like(x)

        S_woma = lambda rho, T: woma.s_rho_T(rho, T, 400)
        P_woma = lambda rho, T: woma.P_T_rho(T, rho, 400)

        @globalize
        def task(i):
            print(f'Start {i}')
            for j in range(x.shape[1]):
                rho_table[i, j], T_table[i, j], error_table[i, j] = \
                    reverse_EOS_table_X_Y(S_woma, NewEOS_fst.S, P_woma, NewEOS_fst.P, x[i, j], 10 ** y[i, j])
            print(f'Done {i}')
            return rho_table[i, :], T_table[i, :], error_table[i, :], i

        # fills table values
        print('Generating SP EOS table:')
        if __name__ == '__main__':
            pool = Pool(7)
            results = pool.map(task, range(x.shape[0]))

        for r in results:
            i = r[3]
            rho_table[i, :] = r[0]
            T_table[i, :] = r[1]
            error_table[i, :] = r[2]

        plt.contourf(x, y, np.log10(rho_table), 80, cmap='cubehelix')
        plt.colorbar()
        plt.show()

        np.save(f'EOS_tables/rho_SP_table_n_{n}.npy', rho_table)
        np.save(f'EOS_tables/T_SP_table_n_{n}.npy', T_table)

        plt.contourf(S, logP, np.log10(error_table), 80)
        plt.colorbar()
        plt.show()

    rho_fst_interp = RegularGridInterpolator((S, logP), rho_table.T, method=method, bounds_error=False, fill_value=np.NaN)
    T_fst_interp = RegularGridInterpolator((S, logP), T_table.T, method=method, bounds_error=False, fill_value=np.NaN)


def generate_table_u_rho(load_from_file=False, n=10, iron=False):
    global T2_fst_interp, T2_iron_interp

    if load_from_file:
        print('Loading u rho EOS table...')
        if iron:
            T_table = np.load(f'EOS_tables/T_uRho_iron_table_n_{n}.npy', allow_pickle=True)
        else:
            T_table = np.load(f'EOS_tables/T_uRho_forsterite_table_n_{n}.npy', allow_pickle=True)

    # produces table points to be calculated
    u = np.concatenate((np.linspace(0, 1e5, num=int(n/2)), np.logspace(5.1, 8, num=int(n/2))))
    log_rho = np.linspace(-8, 5, num=n)
    x, y = np.meshgrid(u, log_rho)

    if not load_from_file:
        T_table = np.zeros_like(x)
        error_table = np.zeros_like(x)

        @globalize
        def task(i):
            print(f'Start {i}')
            for j in range(x.shape[1]):
                if iron:
                    T_table[j, i] = woma.T_u_rho(x[i, j], 10 ** y[i, j], 401)
                else:
                    T_table[j, i] = woma.T_u_rho(x[i, j], 10 ** y[i, j], 401)
            print(f'Done {i}')
            return T_table[:, i], i

        # fills table values
        print('Generating u rho EOS table:')

        if __name__ == '__main__':
            pool = Pool(7)
            results = pool.map(task, range(x.shape[0]))

        for r in results:
            i = r[1]
            T_table[:, i] = r[0]

        # for i in tqdm(range(x.shape[0])):
        #     for j in range(x.shape[1]):
        #         T_table[j, i], error_table[j, i] = reverse_EOS_table_rho_X(u_EOS, NewEOS.U, 10 ** y[i, j], x[i, j])

        if iron:
            np.save(f'EOS_tables/T_uRho_iron_table_n_{n}.npy', T_table)
        else:
            np.save(f'EOS_tables/T_uRho_forsterite_table_n_{n}.npy', T_table)

        # plt.contourf(u, log_rho, np.log10(error_table), 80)
        # plt.xscale('log')
        # plt.colorbar()
        # plt.contour(u, log_rho, np.log10(error_table), [-1, 0], colors='black')
        # plt.show()

    if iron:
        T2_iron_interp = RegularGridInterpolator((u, log_rho), T_table, method=method, bounds_error=False, fill_value=np.NaN)
    else:
        T2_fst_interp = RegularGridInterpolator((u, log_rho), T_table, method=method, bounds_error=False, fill_value=np.NaN)


def make_into_pair_array(arr1, arr2):
    arr1, arr2 = np.nan_to_num(arr1), np.nan_to_num(arr2)

    if type(arr1) is np.ndarray and type(arr2) is np.ndarray:

        if arr1.ndim == 0:
            return np.array([arr1[()], arr2[0]])
        if arr2.ndim == 0:
            return np.array([arr1[0], arr2[()]])

        try:
            assert np.all(arr1.shape == arr2.shape)
        except AssertionError:
            print(f'arr1 = {arr1} \n arr1 shape = {arr1.shape}')
            print(f'arr2 = {arr2} \n arr2 shape = {arr2.shape}')
            assert np.all(arr1.shape == arr2.shape)

        assert arr1.ndim == 1 or arr1.ndim == 2

        arr = np.array([arr1, arr2])

        if arr1.ndim == 1:
            return np.transpose(arr, axes=(1, 0))
        elif arr1.ndim == 2:
            return np.transpose(arr, axes=(1, 2, 0))

    else:

        if type(arr1) is np.ndarray:
            if arr1.ndim == 1:
                arr1 = arr1[0]

        if type(arr2) is np.ndarray:
            if arr2.ndim == 1:
                arr2 = arr2[0]

        return np.array([arr1, arr2])


P_fst_EOS = lambda rho, T: P_fst_interp(make_into_pair_array(rho, T))
S_fst_EOS = lambda rho, T: S_fst_interp(make_into_pair_array(rho, T))
u_fst_EOS = lambda rho, T: u_fst_interp(make_into_pair_array(rho, T))
cs_fst_EOS = lambda rho, T: cs_fst_interp(make_into_pair_array(rho, T))

rho_fst_EOS = lambda S, P: rho_fst_interp(make_into_pair_array(S, np.log10(P)))
T1_fst_EOS = lambda S, P: T_fst_interp(make_into_pair_array(S, np.log10(P)))

P_iron_EOS = lambda rho, T: P_iron_interp(make_into_pair_array(rho, T))
S_iron_EOS = lambda rho, T: S_iron_interp(make_into_pair_array(rho, T))
u_iron_EOS = lambda rho, T: u_iron_interp(make_into_pair_array(rho, T))
cs_iron_EOS = lambda rho, T: cs_iron_interp(make_into_pair_array(rho, T))

T2_fst_EOS = lambda u, rho: T2_fst_interp(make_into_pair_array(u, np.log10(rho)))
T2_iron_EOS = lambda u, rho: T2_iron_interp(make_into_pair_array(u, np.log10(rho)))


def EOS(rho=None, T=None, P=None, S=None, u=None, check=False):

    if rho is not None:

        if u is not None:
            T = T2_fst_EOS(u, rho)
            P, S = P_fst_EOS(rho, T), S_fst_EOS(rho, T)

        elif T is not None:
            P, S = P_fst_EOS(rho, T), S_fst_EOS(rho, T)
            u = u_fst_EOS(rho, T)

        if check:
            rho_check = rho_fst_EOS(S, P)
            T_check = T1_fst_EOS(S, P)
            T_error = np.nan_to_num(np.abs(T_check - T) / T)
            rho_error = np.nan_to_num(np.abs(rho_check - rho) / rho)
            assert np.all(rho_error < 0.1)
            assert np.all(T_error < 0.1)

    elif P is not None and S is not None:
        rho = rho_fst_EOS(S, P)
        T = T1_fst_EOS(S, P)
        u = u_fst_EOS(rho, T)

        if check:
            u_check = u_fst_EOS(rho, T)
            u_error = np.nan_to_num(np.abs(u_check - u) / u)
            assert np.all(u_error < 0.1)

    else:
        return None

    return rho, T, P, S, u


if __name__ == '__main__':
    woma.load_eos_tables(['ANEOS_forsterite', 'ANEOS_iron'])
    generate_table_u_rho(load_from_file=False, n=200)
    generate_table_u_rho(load_from_file=False, n=200, iron=True)
    generate_table_S_P(load_from_file=False, n=200)
else:
    generate_table_u_rho(load_from_file=True, n=200)
    generate_table_u_rho(load_from_file=True, n=200, iron=True)
    generate_table_S_P(load_from_file=True, n=200)

# PHASE CALCULATIONS HERE #

S_vc = np.concatenate([[0], np.flip(NewEOS_fst.vc.Sl), NewEOS_fst.vc.Sv])
P_vc = np.concatenate([[1e-7], np.flip(NewEOS_fst.vc.Pl), NewEOS_fst.vc.Pv])
P_fst_vapor_curve = interp1d(S_vc, P_vc, bounds_error=False, fill_value=np.NaN)

S_vc = np.concatenate([[0], np.flip(NewEOS_iron.vc.Sl), NewEOS_iron.vc.Sv])
P_vc = np.concatenate([[1e-7], np.flip(NewEOS_iron.vc.Pl), NewEOS_iron.vc.Pv])
P_iron_vapor_curve = interp1d(S_vc, P_vc, bounds_error=False, fill_value=np.NaN)

S_vapor_curve_l = interp1d(NewEOS_fst.vc.Pl, NewEOS_fst.vc.Sl, bounds_error=False, fill_value=np.NaN)
S_vapor_curve_v = interp1d(NewEOS_fst.vc.Pv, NewEOS_fst.vc.Sv, bounds_error=False, fill_value=np.NaN)
rho_vapor_curve_l = interp1d(NewEOS_fst.vc.Pl, NewEOS_fst.vc.rl, bounds_error=False, fill_value=np.NaN)


def condensation_S(S, P):
    return np.where(P < NewEOS_fst.cp.P, S_vapor_curve_v(P), S)


# 0 : invalid region, 1 : liquid/solid, 2 : liquid vapor mix, 3 : vapor, 4 : supercritical
def phase(S, P, iron=False):
    min_P = 1e-5  # pressures below this are invalid

    if iron:
        cp_P, cp_S = NewEOS_iron.cp.P, NewEOS_iron.cp.S
        P_vc = P_iron_vapor_curve
    else:
        cp_P, cp_S = NewEOS_fst.cp.P, NewEOS_fst.cp.S
        P_vc = P_fst_vapor_curve

    result = np.zeros_like(P)
    result = np.where(P <= min_P, 0, result)
    result = np.where(np.logical_and(P < P_vc(S), P > min_P), 2, result)
    result = np.where(np.logical_and(P >= P_vc(S), S < cp_S), 1, result)
    result = np.where(np.logical_and(P >= P_vc(S), S >= cp_S), 3, result)
    result = np.where(np.logical_and(result == 3, P >= cp_P), 4, result)

    return result


def vapor_quality(S, P):

    Sl = S_vapor_curve_l(P)
    Sv = S_vapor_curve_v(P)

    vq = (S - Sl) / (Sv - Sl)
    p = phase(S, P)
    result = np.where(p == 2, vq, np.NaN)
    result = np.where(p == 1, 0, result)
    result = np.where(p == 3, 1, result)
    return result


def rho_liquid(P):
    return rho_vapor_curve_l(P)


def liquid_volume_fraction(rho, P, S):
    q = vapor_quality(S, P)
    rho_l = rho_vapor_curve_l(P)
    lvf = (1 - q) * (rho / rho_l)
    return lvf


def rho_vapor(rho, S, P):

    q = vapor_quality(S, P)
    rho_l = rho_vapor_curve_l(P)

    return q * ((1/rho) - ((1 - q)/rho_l)) ** -1


# ABSORPTION CALCULATIONS HERE #

# calculates the absorption of the liquid droplets
def alpha_l(rho, P, S, D0):
    # uses the lever rule to calculate the vapor quality
    q = vapor_quality(S, P)

    # calculates the liquid volume fraction from the vapor quality
    rho_l = rho_vapor_curve_l(P)
    lvf = (1 - q) * (rho / rho_l)
    return (6 / (4 * D0)) * lvf


# calculates the absorption of the vapor mix
def alpha_v(rho, T):
    B0 = 6e17  # m^-1
    B1, B2 = 37, -11.6
    rho_n, T_n = 1900, 4150  # kg/m^3, K
    r, t = rho / rho_n, T / T_n

    result = B0 * (r ** (1 / 3)) * t * np.exp(-B1 / t) * np.exp(-B2 * (r / t))

    return np.nan_to_num(result)


T3_interp = lambda x: None


# calculates the total absorption
def alpha(rho, T, P, S, D0=1e-3):

    ph = phase(S, P)

    result = np.zeros_like(rho)
    result = np.where(ph == 0, 0, result)
    result = np.where(ph == 1, 1e14, result)
    if D0 != 0:
        result = np.where(ph == 2, alpha_v(rho, T) + alpha_l(rho, P, S, D0), result)
    else:
        result = np.where(ph == 2, alpha_v(rho, T), result)
    result = np.where(ph >= 3, alpha_v(rho, T), result)

    return result


def generate_table_alpha_v():
    global T3_interp

    log_alpha = np.linspace(-20, 10, num=50)
    log_rho = np.linspace(-5, 1, num=50)
    x, y = np.meshgrid(log_alpha, log_rho)
    T_table = np.zeros_like(x)

    for i in range(50):
        for j in range(50):
            r = 10 ** y[i, j]
            a = 10 ** x[i, j]
            res = root(lambda T: alpha_v(r, T) - a, 3000)
            if res.success:
                T_table[i, j] = res.x
            else:
                T_table[i, j] = 0

    T3_interp = RegularGridInterpolator((log_alpha, log_rho), T_table, method=method, bounds_error=False, fill_value=np.NaN)


generate_table_alpha_v()


def T_alpha_v(rho, alpha_v):
    rho_alpha = make_into_pair_array(np.log10(alpha_v), np.log10(rho))
    return T3_interp(rho_alpha)


# COOLING CALCULATIONS HERE #

def cool(P, S, du, remove_droplets=True):

    rho_1, T_1, P_1, S_1, u_1 = EOS(P=P, S=S, check=False)

    # cool with constant density
    u_2 = u_1 - du
    rho_2 = rho_1
    rho_2, T_2, P_2, S_2, u_2 = EOS(u=u_2, rho=rho_2, check=False)

    # remove droplets
    P_3 = P_2
    S_3 = S_vapor_curve_v(P_2)
    rho_3, T_3, P_3, S_3, u_3 = EOS(S=S_3, P=P_3, check=False)

    if remove_droplets:
        rho_3 = np.where(phase == 2, rho_3, rho_2)
        T_3 = np.where(phase == 2, T_3, T_2)
        P_3 = np.where(phase == 2, P_3, P_2)
        S_3 = np.where(phase == 2, S_3, S_2)
        u_3 = np.where(phase == 2, u_3, u_2)
        return rho_3, T_3, P_3, S_3, u_3
    else:
        return rho_2, T_2, P_2, S_2, u_2


def cooling_plot(P_1, S_1, du):
    rho_1, T_1, P_1, S_1, u_1 = EOS(P=P_1, S=S_1, check=True)

    # cool with constant density
    u_2 = u_1 - du
    rho_2 = rho_1
    rho_2, T_2, P_2, S_2, u_2 = EOS(u=u_2, rho=rho_2, check=False)

    # remove droplets
    P_3 = P_2
    S_3 = S_vapor_curve_v(P_2)
    rho_3, T_3, P_3, S_3, u_3 = EOS(S=S_3, P=P_3, check=False)

    print(f'u_1={u_1}, u_2={u_2}, u_3={u_3}')
    print(f'rho_1={rho_1}, rho_2={rho_2}, rho_3={rho_3}')
    print(f'E_rho_1={u_1*rho_1}, E_rho_2={u_2*rho_2}, E_rho_3={u_3*rho_3}')

    print(frac_error(T_1, T2_fst_EOS(u_1, rho_1)))
    print(frac_error(P_fst_EOS(rho_1, T2_fst_EOS(u_1, rho_1)), P_1))
    print(frac_error(S_fst_EOS(rho_1, T2_fst_EOS(u_1, rho_1)), S_1))

    # plot cooling track
    u_cool = np.linspace(u_1, u_2)
    rho_cool = np.full_like(u_cool, rho_1)
    rho_cool, T_cool, P_cool, S_cool, u_cool = EOS(u=u_cool, rho=rho_cool, check=False)

    S_cond = np.linspace(S_2, S_3)
    P_cond = np.full_like(S_cond, P_2)

    plt.plot(S_cool, P_cool, 'b--', label='Cool at constant volume')
    plt.plot(S_cond, P_cond, 'b--', label='Loss of droplets')
    plt.plot(NewEOS_fst.vc.Sl, NewEOS_fst.vc.Pl, 'k--')
    plt.plot(NewEOS_fst.vc.Sv, NewEOS_fst.vc.Pv, 'k--')
    plt.scatter(S_1, P_1, marker='x')
    plt.legend()
    plt.yscale('log')
    plt.show()

