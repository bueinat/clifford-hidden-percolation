import percolation.util_functions as uf
import numpy as np
from tqdm import trange, tqdm
import argparse
from itertools import product
import os
from pyzx import full_reduce
import pandas
rng = np.random.default_rng()


def parse_args():
    parser = argparse.ArgumentParser(description="Your script description.")
    parser.add_argument("-N", type=int, default=40, help="Value for N")
    parser.add_argument("--t_factor", type=int, default=4,
                        help="Value for t_factor")
    parser.add_argument("--ncores", type=int, default=5,
                        help="Value for t_factor")
    parser.add_argument("--niterations", type=int,
                        default=50, help="Number of iterations")
    parser.add_argument("-p", nargs='*', type=float,
                        default=[0.1], help="Value for p")
    parser.add_argument("-q", nargs='*', type=float,
                        default=[0.5], help="Value for q")
    parser.add_argument("-r", nargs='*', type=float,
                        default=[0.1], help="List of r values")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress output messages")
    parser.add_argument(
        "--save_path", help="path in which to save the data", default="data/test")
    parser.add_argument("--periodic", action='store_true')

    return parser.parse_args()


def single_iteration(params):
    N, t_factor, p, q, r, it, quiet, output_data, save_path, periodic, data_path = params
    output_dict = uf.general_single_iteration(
        N, t_factor, run_all_hfunction, quiet=quiet, p=p, q=q, r=r, simp_method=full_reduce, periodic=periodic)

    for key in output_dict:
        output_data[(p, q, r, key)][it] = output_dict[key]

    # try:
    to_save = output_data.copy()
    df = pandas.DataFrame({key: list(to_save[key]) for key in to_save})
    df.to_csv(f"{save_path}/{data_path}")

    return it, output_dict


def add_cnots(string_circuit, p, q, r):
    ngates = np.sum(string_circuit != '')
    ncnots = np.sum(string_circuit == 'cnot')
    swap_N, swap_t = np.where(string_circuit == 'swap')
    pcnots = (1 - p) * r

    cnots_to_add = int(ngates * pcnots - ncnots)
    if cnots_to_add > 0:
        replace_idx = rng.choice(
            np.arange(len(swap_N)), cnots_to_add, replace=False)
        string_circuit[swap_N[replace_idx], swap_t[replace_idx]] = 'cnot'

    return string_circuit


def add_measurements(string_circuit, p, q, r):
    ngates = np.sum(string_circuit != '')
    nbells = np.sum(string_circuit == 'bell_projection')
    nids = np.sum(string_circuit == 'id_projection')
    pids = p * (1-q)
    pbells = p * q
    unitary_N, unitary_t = np.where(
        (string_circuit == 'swap') | (string_circuit == 'cnot'))
    ids_to_add = int(pids * ngates - nids)
    bells_to_add = int(pbells * ngates - nbells)

    m_to_add = max(0, ids_to_add) + max(0, bells_to_add)
    # print(nbells, pbells, ngates, pbells * ngates)
    # print("swap:", np.sum(string_circuit == 'swap'), "cnot:", np.sum(string_circuit == "cnot"), "bell:", nbells, "id:", nids)
    # print(bells_to_add, ids_to_add, m_to_add, unitary_N)
    if m_to_add > 0:
        replace_idx = rng.choice(
            np.arange(len(unitary_N)), min(m_to_add, len(unitary_N)), replace=False)
        string_circuit[unitary_N[replace_idx],
                       unitary_t[replace_idx]] = 'id_projection'

        if bells_to_add > 0:
            bell_idx = rng.choice(replace_idx, int(
                bells_to_add), replace=False)
            string_circuit[unitary_N[bell_idx],
                           unitary_t[bell_idx]] = 'bell_projection'

    return string_circuit


def run_all_hfunction(G, g, **kwargs):
    lc, slc = uf.percolation_hfunction(G, g, **kwargs)
    is_path = uf.find_path_hfunction(G, g, **kwargs)
    min_cut_if = uf.min_cut_hfunction(G, g, **kwargs)
    min_cut_ff = uf.min_cut_hfunction(G, g, **kwargs)
    min_cut_X = uf.min_cut_hfunction(G, g, **kwargs)
    # min_cut_if -> min_cut for backwards compitability
    return {'lc': lc, 'slc': slc, 'is_path': is_path, 'min_cut': min_cut_if, 'min_cut_ff': min_cut_ff, 'min_cut_X': min_cut_X}


def get_data_name(path):
    # Check if 'data.csv' exists
    if not os.path.isfile(f'{path}/data.csv'):
        filename = "data.csv"
    else:
        # Find the next available 'dataX.csv'
        i = 1
        while os.path.isfile(f'{path}/data{i}.csv'):
            i += 1
        filename = f"data{i}.csv"

    # Create an empty file with that name to reserve it
    with open(f'{path}/{filename}', 'w') as file:
        pass  # This creates an empty file

    return filename


def run_percolation(args):
    output_data = {}
    data_name = get_data_name(args.save_path)

    lp, lq, lr = len(args.p), len(args.q), len(args.r)
    icombinations = product(range(lp), range(
        lq), range(lr))

    for ip, iq, ir in icombinations:
        p, q, r = args.p[ip], args.q[iq], args.r[ir]
        for key in ['lc', 'slc', 'is_path', 'min_cut', 'min_cut_ff', 'min_cut_X']:
            output_data[(p, q, r, key)] = [
                np.nan for _ in range(args.niterations)]

    for it in trange(args.niterations):
        icombinations = product(range(lp), range(
            lq), range(lr))

        for ip, iq, ir in tqdm(icombinations, leave=False, total=lp * lq * lr):
            p, q, r = args.p[ip], args.q[iq], args.r[ir]

            output_dict = uf.general_single_iteration(
                args.N, args.t_factor, run_all_hfunction, quiet=args.quiet, p=p, q=q, r=r, simp_method=full_reduce, periodic=args.periodic)
            for key in output_dict:
                output_data[(p, q, r, key)][it] = output_dict[key]

        df = pandas.DataFrame(
            {key: list(output_data[key]) for key in output_data})
        df.to_csv(f"{args.save_path}/{data_name}")


args = parse_args()
args.p.sort()
args.q.sort()
args.r.sort()

os.makedirs(args.save_path, exist_ok=True)
run_percolation(args)
print(f"run is done. args were: {args}")
