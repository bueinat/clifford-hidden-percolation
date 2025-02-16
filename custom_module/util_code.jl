# Define the inner module
module StandardGates

export State
export Gate #, bell_measurement
export z_meas_gate, id_meas_gate, bell_meas_gate
export random_gate, swap_gate, lcnot_gate, rcnot_gate
export op, nqubits
export ggen_unitaries, ggen_measurements, ggen_all_to_all

include("standard_gates.jl")

end # StandardGates

# Define the inner module
module PlotAssistant

export dparams_plot

dparams_plot = Dict()
dparams_plot["line"] = Dict(:marker => :circle, :ms => 3, :msw => 0)
dparams_plot["errorline"] = Dict(:marker => :circle, :ms => 3, :msc => :auto)

end # PlotAssistant

# Define the inner module
module CalculatedQuantities

export entanglement_entropy, tmi, last_site_entanglement, corr_length, allquants

include("calculated_quantities.jl")

end # CalculatedQuantities

module CustomSimulations
# way of use:
# include("~/Thesis/custom_module/run_simulations.jl")
# using .CustomSimulations

export apply_gate, apply_gates, gates, prepare_qubits_for_gates!, prepare_qubits_probabilities!
export single_sim!, new_state
export write_info, get_iterator
export run_parameterized_simulation, codependence_simulation
export full_purification_simulation, purification, new_purification

include("utility_functions.jl")

end # CustomSimulations

using .CustomSimulations
using .StandardGates
using .PlotAssistant
using .CalculatedQuantities
