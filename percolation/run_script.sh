#!/bin/bash

script_dir="$(dirname "$(readlink -f "$0")")"

# run a few r values to see which is better
run_path="data/log_Ns_periodic_min_cut_fixed"
mkdir -p "${script_dir}/${run_path}/."
cp $0 "${script_dir}/${run_path}/."

for N in $(julia -e 'println(join(unique(convert.(Int, 10.0 .^ (1.1:(3.5-1.1)/20:3.5) .÷ 12 .* 12))," "))')
do
    ./percolation_script.py -N ${N} --t_factor 4 --niterations 500 --save_path "${run_path}/N${N}" --quiet --periodic -q 0.5 \
            -r 0.1 0.5 0.8 \
            -p $(julia -e 'println(join(round.(0.15:(0.4-0.15)/20:0.4, sigdigits=10), " "))') &
done