include("../custom_module/util_code.jl")
using ArgParse
using JLD2
using QuantumClifford


function parse_commandline()
	s = ArgParseSettings()

	@add_arg_table! s begin
		"-N"
		help = "number of qubits"
		arg_type = Int
		default = 12
		"--description"
		default = ""
		"--state_type"
		default = "Stabilizer"
		range_tester = (x -> x ∈ ["Stabilizer", "MPS"])
		"--time_factor"
		arg_type = Int
		default = 4
		"--niterations"
		arg_type = Int
		default = 500
		"--filename"
		required = true
		"--full_time"
		action = :store_true
		help = "flag which indicates to save the full time evolution"
		"-p"
		nargs = '*'
		arg_type = Float64
		default = Float64[1.0]
		"-q"
		nargs = '*'
		arg_type = Float64
		default = Float64[0.5]
		"-r"
		nargs = '*'
		arg_type = Float64
		default = Float64[0.0]
		"--pmin"
		arg_type = Float64
		"--pmax"
		arg_type = Float64
		"--pstep"
		arg_type = Float64
		default = 1.0
		"--qmin"
		arg_type = Float64
		"--qmax"
		arg_type = Float64
		"--qstep"
		arg_type = Float64
		default = 1.0
		"--rmin"
		arg_type = Float64
		"--rmax"
		arg_type = Float64
		"--rstep"
		arg_type = Float64
		default = 1.0
		"--initial_mps_type"
		default = "product"
		range_tester = (x -> x ∈ ["bell", "product"])
		help = "initial_mps_type must be one of ['bell', 'product']"
		"--non_periodic"
		action = :store_true
	end
	return parse_args(s)
end

function ggen_even(; p, q, r)
	return Dict{String, Float64}("swap_gate" => (1 - p) * (1 - r),
		"lcnot_gate" => (1 - p)r / 2,
		"rcnot_gate" => (1 - p)r / 2,
		"id_meas_gate" => p * q,
		"bell_meas_gate" => p * (1 - q))
end;



args = parse_commandline()
mkpath(dirname(args["filename"]))

function format_args!(args)
	if (args["pmin"] !== nothing && args["pmax"] !== nothing)
		args["p"] = args["pmin"]:args["pstep"]:args["pmax"]
	end
	if (args["qmin"] !== nothing && args["qmax"] !== nothing)
		args["q"] = args["qmin"]:args["qstep"]:args["qmax"]
	end
	if (args["rmin"] !== nothing && args["rmax"] !== nothing)
		args["r"] = args["rmin"]:args["rstep"]:args["rmax"]
	end

	args["ggenerators"] = [Dict(:glist => ggen_even, :type => "even", :calculate => false, :kwargs => Dict()),
		Dict(:glist => ggen_even, :type => "odd", :calculate => true, :kwargs => Dict())]

	args["calculate_quantities"] = ["entropy", "mi"]

	args["pdict"] = Dict{Symbol, AbstractArray}(:p => args["p"], :q => args["q"], :r => args["r"])
	args["progress_bar"] = args["N"] > 2000
end

format_args!(args)
args["key"] = nothing

N = args["N"]
s = run_parameterized_simulation(args["N"], args["state_type"], args["time_factor"], args["niterations"], args["pdict"],
	args["filename"], args["ggenerators"], args["calculate_quantities"]; periodic = !args["non_periodic"],
	initial_mps_type = args["initial_mps_type"], progress_bar = args["progress_bar"], full_time = args["full_time"])
println("done N = $N")
