using LinearAlgebra
using QuantumClifford
using ProgressBars
using JLD2
using Dates

using ITensors
using StatsBase
using Distributions
using OrderedCollections

using ..StandardGates: State, Gate, bell_meas_gate, ggen_unitaries, ggen_measurements, ggen_ata_unitaries, ggen_ata_measurements, nqubits
using ..CalculatedQuantities: allquants, mutual_information
import ..StandardGates
# this is a dictionary of function names and methods

PATH_SPLITTER = Sys.iswindows() ? "\\" : "/"

function get_iterator(iter_over, progress_bar, description = nothing; kwargs...)
	if progress_bar && length(iter_over) > 1
		iterator = tqdm(iter_over; kwargs...)
		if !(description === nothing)
			iterator.description = description
		end
	else
		iterator = iter_over
	end
	return iterator
end

function apply_gate(state::MixedDestabilizer, gate::Gate)::MixedDestabilizer
	for c in gate
		apply!(state, c)
	end
	return state
end;

function apply_gate(state::MPS, gate::Gate)::MPS
	state = apply(gate, state)
	normalize!(state)
	return state
end;

function apply_gate(state::State, gate::Gate)::State
	state.ψ = apply_gate(state.ψ, gate)
	return state
end;

function apply_gate(state::State, gate::Gate, q1::Int, q2::Int, V_flag::Bool = false)::State
	# TODO: deal also with Clifford
	if V_flag
		throw(ArgumentError("V_flag not carefully handled"))
		if length(state.sites) > 0
			state.V = update_op!(state.V, state.sites[q1], state.sites[q2], nqubits(state), q1, q2, gate::ITensor)
		else
			state.V = update_op!(state.V, 0, 0, nqubits(state), q1, q2, gate)
		end
	end
	state.ψ = apply_gate(state.ψ, gate)
	return state
end;

function apply_gates(state::State, gates::Vector, q1::Vector{Int}, q2::Vector{Int}, V_flag::Bool = false)::State
	for (gate, qi1, qi2) in zip(gates, q1, q2)
		state = apply_gate(state, gate, qi1, qi2, V_flag)
	end
	return state
end;

# function apply_gates(state::State, gates::Vector{Gate})::State
function apply_gates(state::State, gates::Vector)::State
	for gate in gates
		# println(gate)
		state = apply_gate(state, gate)
	end
	return state
end;


function gates(state::State, qubits, cum_prob, catg, kwargs; V_flag = false, return_string = false)#::Array{Gate}
	fqubits, squbits = qubits()
	ngates = length(fqubits)
	if return_string
		gates_list = Array{String}(undef, ngates)
	else
		gates_list = Array{Gate}(undef, ngates)
	end

	gates_pool = cum_prob[rand(catg, ngates), 2]
	for (i, (g, q1, q2)) in enumerate(zip(gates_pool, fqubits, squbits))
		if return_string
			gates_list[i] = g
		else
			gates_list[i] = state.gate_func(getfield(StandardGates, Symbol(g)), q1, q2, state.sites)
		end
	end
	if V_flag
		return gates_list, fqubits, squbits
	else
		return gates_list
	end
end

function bell_pairs(s)::MPS
	N = length(s)
	states = ["↑" for i in 1:N]
	ψ = MPS(s, states)

	hlist, clist = ITensor[], ITensor[]
	for i in 1:2:N
		push!(hlist, op(("H", i), s))
		if i < N
			push!(clist, op(("CNOT", i, i + 1), s))
		end
	end

	ψ = apply(hlist, ψ)
	normalize!(ψ)
	ψ = apply(clist, ψ)
	normalize!(ψ)

	return ψ
end


function _get_params_iterator(params_dict; combine_as, progress_bar)
	piter = enumerate.(params_dict |> values |> collect)
	if combine_as == "product"
		params_iter = Iterators.product(piter...)
	elseif combine_as == "zip"
		params_iter = Iterators.zip(piter...)
	else
		throw(ArgumentError("params_dict should be one of the options: ['zip', 'product']"))
	end
	if !progress_bar
		params_iter = tqdm(params_iter)
	end
	return params_iter
end

function new_state(N::Int, state_type::String; initial_mps_type::String = "product", ancillas = [])::State
	if state_type == "Stabilizer"
		return stab_state(N; initial_mps_type, ancillas)
	elseif state_type == "MPS"
		return mps_state(N; initial_mps_type, ancillas)
	else
		throw(ArgumentError("state_type should be one of the options: [:Stabilizer, :MPS]"))
	end
end

function stab_state(N::Int; initial_mps_type::String = "product", ancillas = [])::State
	# initiate states
	if initial_mps_type == "product"
		state = QuantumClifford.one(Stabilizer, N) |> MixedDestabilizer
	elseif initial_mps_type == "bell"
		state = bell(N ÷ 2) |> MixedDestabilizer
	else
		throw(ArgumentError("initial_mps_type should be one of the options: ['bell', 'product']"))
	end
	return State([], state, (g, q1, q2, s, kw::Dict = Dict()) -> g(q1, q2), (state::MixedDestabilizer) -> state, [], ancillas)
end


function mps_state(N::Int; initial_mps_type::String = "product", ancillas = [])::State
	sites = siteinds("S=1/2", N)
	# initiate states
	if initial_mps_type == "product"
		state = MPS(sites, ["↑" for i in 1:N])
	elseif initial_mps_type == "x-product"
		state = MPS(sites, ["+" for i in 1:N])
	elseif initial_mps_type == "random"
		state = MPS(sites, ifelse.(rand(N) .> 0.5, "↑", "↓"))
	elseif initial_mps_type == "bell"
		state = bell_pairs(sites)
	else
		throw(ArgumentError("initial_mps_type should be one of the options: ['bell', 'product', 'random', 'x-product']"))
	end
	return State(sites, state, (g::Function, q1::Int, q2::Int, s::Vector, kw::Dict = Dict()) -> op(g()::String, s[q1], s[q2]; kw...), mps_process, [], ancillas)
end;


function mps_process(ψ::MPS)
	if norm(ψ) == 0
		return nothing
	end
	normalize!(ψ)
	return ψ
end


function write_info(info, params_dict, filename)
	merge!(info, params_dict)
	key = now() |> string
	# TODO: add an override option which decides if you should use "a+" or "a"
	# TODO: filter the parameters (not all of them should be added)
	mkpath(dirname(filename))
	jldopen(filename, "a+") do fjld
		if !haskey(fjld, key)
			JLD2.Group(fjld, key)
		end
		if !haskey(fjld[key], "info")
			fjld["$key/info"] = info
		end
	end
	return key
end

# NOTE: this function currently works only for cases when the ancillas are last

function prepare_even(relq, periodic)
	fqubits = relq[2:2:end]
	inds = (fqubits .+ 1)
	if inds[end] > relq[end]
		inds[end] = relq[1]
	end
	squbits = unique(inds)
	if (!periodic) & (fqubits[end] > squbits[end])
		pop!(fqubits)
		pop!(squbits)
	end
	return fqubits, squbits
end

function prepare_odd(relq, periodic)
	fqubits = relq[1:2:end]
	inds = (fqubits .+ 1)
	if inds[end] > relq[end]
		inds[end] = relq[1]
	end
	squbits = unique(inds)
	if (!periodic) & (fqubits[end] > squbits[end]) # allow odd number qubits
		pop!(fqubits)
		pop!(squbits)
	end
	return fqubits, squbits
end

function prepare_random(relq, N)
	allq = hcat([StatsBase.sample(relq, 2, replace = false) for i in 1:N]...)
	return allq[1, :], allq[2, :]
end

function prepare_single(relq)
	fqubits = relq
	squbits = circshift(fqubits, -1)
	return fqubits, squbits
end


function prepare_qubits_for_gates!(dgp; N, periodic, ancillas)
	relq = setdiff(1:N, ancillas)
	# n = length(relq)
	if dgp[:type] == "even"
		dgp[:qubits] = () -> prepare_even(relq, periodic)
	elseif dgp[:type] == "odd"
		dgp[:qubits] = () -> prepare_odd(relq, periodic)
	elseif dgp[:type] == "random"
		dgp[:qubits] = () -> prepare_random(relq, N)
	elseif dgp[:type] == "mixed"
		dgp[:qubits] = () -> prepare_random(relq, N)
	elseif dgp[:type] == "single"
		dgp[:qubits] = () -> prepare_single(relq)
	else
		throw(ArgumentError("currently only ['even', 'odd', 'single', 'random', 'mixed'] are valid types"))
	end
end

function prepare_qubits_probabilities!(dgp; di)
	dgp[:probs] = dgp[:glist].(; di...)
	pvals = collect(values(dgp[:probs]))	# probabilities
	pkeys = collect(keys(dgp[:probs]))		# names (rather than functions)
	dgp[:cumg] = hcat([pvals |> cumsum, pkeys]...)
	dgp[:catg] = Categorical(pvals)
end


function reset_quantities!(qts, state, calculate_quantities, times)
	for name in calculate_quantities
		qts[name] = zeros(allquants[name].dtype, (length(times), allquants[name].dsize(nqubits(state))))
		qts[name][1, :] .= allquants[name].func(state)
	end
end

function process_gates!(state, row, dgp, V_flag, measure_at_unitary)
	processed_state = nothing
	flag = true
	while flag
		if V_flag
			throw(ArgumentError("V_flag not carefully handled"))
			gates_list, fqubits, squbits = gates(state, dgp[:qubits], dgp[:cumg], dgp[:catg], dgp[:kwargs]; V_flag)
			state = apply_gates(state, gates_list, fqubits, squbits, V_flag)
		else
			gates_list = [(getfield(StandardGates, Symbol(gate)))(q1, q2)::Gate for (gate, q1, q2) in zip(row, dgp[:qubits]()...)]
			state = apply_gates(state, gates_list)
		end

		processed_state = state.process_func(state.ψ)
		if isnothing(processed_state)
			return nothing
		end

		if measure_at_unitary
			flag = state.ψ == processed_state
		else
			flag = false
		end
	end

	state.ψ = processed_state
	return state
end

function update_quantities!(vq, state, calculate_quantities)
	for name in calculate_quantities
		push!(vq[name], allquants[name].func(state))
		if isnan(vq[name][end])
			println("ERROR!!!")
		end
	end
end

function collect_quantities!(qts, vq, t, calculate_quantities)
	for (name, value) in vq
		if allquants[name].last
			qts[name][t+1, :] .= value[end]
		else
			qts[name][t+1, :] .= mean(value)
		end
	end
end

function single_sim_full_time!(state::State, circuit, gdict_generators::AbstractArray{Dict{Symbol, Any}}, times::AbstractArray{Int64},
	calculate_quantities::Vector{<:AbstractString}; progress_bar::Bool = false,
	measure_at_unitary::Bool = false, ignore_V::Bool = false, ancilla = [])
	Ng = length(gdict_generators)
	V_flag = any(allquants[name][:V] for name in calculate_quantities) && !ignore_V
	qts = Dict()
	reset_quantities!(qts, state, calculate_quantities, times)

	for ((t, i), row) in tqdm(circuit)
		dgp = gdict_generators[i]
		state = process_gates!(state, row, dgp, V_flag, measure_at_unitary)
		if isnothing(state)
			return nothing
		end
		
		if dgp[:calculate]
			update_quantities!(vq, state, calculate_quantities)
		end

		if i == Ng
			collect_quantities!(qts, vq, t, calculate_quantities)
		end
	end
	return qts
end

function single_sim_final_time!(state::State, circuit, gdict_generators::AbstractArray{Dict{Symbol, Any}}, times::AbstractArray{Int64},
	calculate_quantities::Vector{<:AbstractString}; progress_bar::Bool = false,
	measure_at_unitary::Bool = false, ignore_V::Bool = false, ancilla = [])
	N = nqubits(state)
	V_flag = any(allquants[name][:V] for name in calculate_quantities) && !ignore_V
	split_time = times[length(times) - (N ÷ 8)]
	vq = Dict(name => [allquants[name].func(state)] for name in calculate_quantities)

	for ((t, i), row) in tqdm(circuit)
		dgp = gdict_generators[i]
		state = process_gates!(state, row, dgp, V_flag, measure_at_unitary)
		if isnothing(state)
			return nothing
		end
		
		if t > split_time && dgp[:calculate]
			update_quantities!(vq, state, calculate_quantities)
		end
	end

	return Dict(name => mean(vq[name]) for name in calculate_quantities)
end

function single_sim!(state::State, circuit, gdict_generators::AbstractArray{Dict{Symbol, Any}}, times::AbstractArray{Int64},
	calculate_quantities::Vector{<:AbstractString}; progress_bar::Bool = false, full_time::Bool = true,
	measure_at_unitary::Bool = false, ignore_V::Bool = false, ancilla = [])
	if full_time
		return single_sim_full_time!(state, circuit, gdict_generators, times, calculate_quantities; progress_bar = progress_bar,
			measure_at_unitary = measure_at_unitary, ignore_V = ignore_V, ancilla = ancilla)
	else
		return single_sim_final_time!(state, circuit, gdict_generators, times, calculate_quantities; progress_bar = progress_bar,
			measure_at_unitary = measure_at_unitary, ignore_V = ignore_V, ancilla = ancilla)
	end
end

function random_circuit(state::State, gdict_generators::AbstractArray{Dict{Symbol, Any}}, times::AbstractArray{Int64})
	circuit = OrderedDict{Tuple{Int64, Int64}, Vector{String}}()
	for t in times
		for (i, dgp) in enumerate(gdict_generators)
			circuit[(t, i)] = gates(state, dgp[:qubits], dgp[:cumg], dgp[:catg], dgp[:kwargs]; return_string=true)
		end
	end
	return circuit
end;



function run_parameterized_simulation(N::Integer, state_type::String, tfactor::Integer, niterations::Integer,
	params_dict::Dict{Symbol, AbstractArray}, filename::String, gdict_generators::AbstractArray{Dict{Symbol, Any}},
	calculate_quantities::Vector{<:AbstractString}; initial_mps_type::String = "product", periodic::Bool = false,
	progress_bar::Bool = false, full_time::Bool = true, combine_as::String = "product", first_iter_index::Int = 1, infokey = nothing)
	return run_parameterized_simulation_wrapped(N, state_type, tfactor, niterations, params_dict, filename, gdict_generators, calculate_quantities, random_circuit; initial_mps_type, periodic, progress_bar, full_time,
				combine_as, first_iter_index, infokey);
end

function run_parameterized_simulation_wrapped(N::Integer, state_type::String, tfactor::Integer, niterations::Integer,
	params_dict::Dict{Symbol, AbstractArray}, filename::String, gdict_generators::AbstractArray{Dict{Symbol, Any}},
	calculate_quantities::Vector{<:AbstractString}, circuit_function::Function; initial_mps_type::String = "product", periodic::Bool = false,
	progress_bar::Bool = false, full_time::Bool = true, combine_as::String = "product", first_iter_index::Int = 1, infokey = nothing)
	times = 0:(N*tfactor)
	calculate_quantities = calculate_quantities_validation(calculate_quantities, state_type)
	if full_time
		qts_array = Dict{String, Array}(name => zeros(allquants[name].dtype, (length.(params_dict |> values)..., length(times), allquants[name].dsize(N))) for name in calculate_quantities)
	else
		qts_array = Dict{String, Array}(name => zeros(allquants[name].dtype, (length.(params_dict |> values)..., allquants[name].dsize(N))) for name in calculate_quantities)
	end

	# write info to file
	if isnothing(infokey)
		info = Dict{Symbol, Any}(:N => N, :tfactor => tfactor, :niterations => niterations,
			:full_time => full_time, :measured => calculate_quantities)
		infokey = write_info(info, params_dict, filename)
	end

	prepare_qubits_for_gates!.(gdict_generators; N, periodic, ancillas = [])
	params_iter = _get_params_iterator(params_dict; combine_as, progress_bar)

	for i in get_iterator(first_iter_index:niterations, progress_bar, "iteration, N = $N: ")
		for (j, it) in enumerate(params_iter)
			v = hcat(collect.(it)...)
			if progress_bar
				println("N = $N: $(params_dict |> keys) = $(v[2, :]), $j/$(length(params_iter))")
			else
				set_description(params_iter, "N = $N: $(params_dict |> keys) = $(v[2, :])")
			end
			di = Dict(key => v[2, i] for (i, key) in params_dict |> keys |> enumerate) # dictionary parameters: values
			prepare_qubits_probabilities!.(gdict_generators; di)

			u = nothing
			k = 0
			while isnothing(u)
				if k > 0
					println(k)
				end
				k += 1
				state = new_state(N, state_type; initial_mps_type, ancillas = [])
				circuit = circuit_function(state, gdict_generators, times)
				u = single_sim!(state, circuit, gdict_generators, times, calculate_quantities; full_time, progress_bar)
			end
			if full_time
				for name in calculate_quantities
					qts_array[name][v[1, :]..., :] .= u[name]
				end
			else
				for name in calculate_quantities
					qts_array[name][v[1, :]..., :] .= u[name]
				end
			end
		end
		jldopen(filename, "a+") do fjld
			for name in calculate_quantities
				if !(infokey in fjld |> keys)
					JLD2.Group(fjld, infokey)
				end
				if !(name in fjld[infokey] |> keys)
					JLD2.Group(fjld[infokey], name)
				end
				fjld["$infokey/$name/$i"] = qts_array[name]
			end
		end
	end
	return qts_array
end


function update_op!(V::AbstractArray, s1::Index, s2::Index, N::Int64, i::Int64, j::Int64, rand_op::ITensor; swap = true)
	# operators layer
	# s1, s2 = i > j ? (s2, s1) : (s1, s2)	# swap s1, s2 if i > j
	i, j = i > j ? (j, i) : (i, j)# swap i, j if i > j
	Mswap = 1
	swap_mat = [1 0 0 0
		0 0 1 0
		0 1 0 0
		0 0 0 1]

	# swap the gates
	if swap
		for k in j-1:-1:i+1
			m0 = LinearAlgebra.I(2^(k - 1))
			m0 = ITensors.kron(m0, swap_mat)
			m0 = ITensors.kron(m0, LinearAlgebra.I(2^(N - k - 1)))
			Mswap *= m0
		end
	end

	# apply gate
	# println(rand_op)
	rand_mat = ITensors.Array(rand_op, s2', s1', s2, s1)
	rand_reshaped = reshape(rand_mat, 4, 4)

	m0 = LinearAlgebra.I(2^(i - 1))
	m0 = ITensors.kron(m0, rand_reshaped)
	if i < N
		m0 = ITensors.kron(m0, LinearAlgebra.I(2^(N - i - 1)))
	end
	Mswap *= m0

	# swap the gates
	if swap
		for k in i+1:j-1
			m0 = LinearAlgebra.I(2^(k - 1))
			m0 = ITensors.kron(m0, swap_mat)
			m0 = ITensors.kron(m0, LinearAlgebra.I(2^(N - k - 1)))
			Mswap *= m0
		end
	end

	V = Mswap * V
	return V
end



function calculate_quantities_validation(calculate_quantities::Vector{<:AbstractString}, state_type::String)::Vector{<:AbstractString}
	# filter non-existing keys
	to_remove = collect(filter(x -> !(x in allquants |> keys |> collect), calculate_quantities))
	if state_type == "Stabilizer"
		append!(to_remove, ["opEE", "opSVD"])
	end
	if length(to_remove) > 0
		println("the following quantities are not supported: $to_remove")
	end
	calculate_quantities = filter(x -> x in allquants |> keys |> collect, calculate_quantities)
	if length(calculate_quantities) == 0
		throw(ArgumentError("none of the passed quantities are valid"))
	end
	return calculate_quantities
end
