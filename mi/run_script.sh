#!/bin/bash

script_dir="$(dirname "$(readlink -f "$0")")"
run_path="data/cnot_gate_diagram_small_r"
mkdir -p "${script_dir}/${run_path}/."
cp $0 "${script_dir}/${run_path}/."

for N in $(julia -e 'println(join(convert.(Int, 10.0 .^ (2.05:(3-2.05)/8:3) .÷ 12 .* 12) |> unique, " "))'); do
        julia -p 4 mi_script.jl -N ${N} --description "find the transition from AL to VL" --filename "${run_path}/N${N}.jld2" \
                -r $(julia -e 'println(join(round.(0.0:0.001:0.1, sigdigits=10), " "))') \
                -p $(julia -e 'println(join(round.(0.0:0.01:0.5, sigdigits=10), " "))') \
                --niterations 1000 --time_factor 4 --mi --non_periodic &
done