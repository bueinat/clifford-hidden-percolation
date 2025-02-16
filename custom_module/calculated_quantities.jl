using ITensors
using QuantumClifford
using LinearAlgebra
using ..StandardGates: State

function entanglement_entropy(ψ::MPS, partite_index::Int, n::Int = 1)
	orthogonalize!(ψ, partite_index)
	u, s, v = svd(ψ[partite_index], (linkind(ψ, partite_index - 1), siteind(ψ, partite_index)))
	arr_s = ITensors.Array(s, inds(s)[1], inds(s)[2])
	arr_p = diag(arr_s .^ 2)
	arr_p = arr_p[arr_p.!=0] # is this right?
	if n == 1
		return -sum(arr_p .* log2.(arr_p))
	else
		return log2(sum(arr_p .^ n)) / (1.0 - n)
	end
end

function entanglement_entropy(ψ::MPS)
	return entanglement_entropy(ψ, length(ψ) ÷ 2)
end;

function last_site_entanglement(ψ::MPS)
	return entanglement_entropy(ψ, length(ψ) - 1)
end;

function entanglement_entropy(ψ::MixedDestabilizer, subsystem::AbstractArray{Int64})
	nb_of_qubits = nqubits(ψ)
	nb_of_deletions = length(subsystem)
	ψ, rank_after_deletion = canonicalize_rref!(ψ, subsystem)
	return nb_of_qubits - rank_after_deletion - nb_of_deletions
end;

function entanglement_entropy(ψ::MixedDestabilizer, partite_index::Int64)
	return entanglement_entropy(ψ, 1:partite_index)
end;

function entanglement_entropy(ψ::MixedDestabilizer)
	return entanglement_entropy(ψ, 1:(length(ψ)÷2))
end;

function last_site_entanglement(ψ::MixedDestabilizer)
	return entanglement_entropy(ψ, length(ψ) - 1)
end;


function _cea(ψ::MixedDestabilizer, subsystem::AbstractArray{Int64})
	return entanglement_entropy(ψ, subsystem)
end;

function tmi(ψ::MixedDestabilizer)
	N = length(ψ)
	n = N ÷ 4
	A = 1:n
	B = (n+1):2n
	C = (2n+1):3n
	return _cea(ψ, A) + _cea(ψ, B) + _cea(ψ, C) - (_cea(ψ, hcat(A, B)) + _cea(ψ, hcat(A, C)) + _cea(ψ, hcat(B, C))) + _cea(ψ, hcat(A, B, C))
end;

function tmi(ψ::MPS)
	throw(MethodError(tmi, (typeof(ψ),), "Function not implemented."))
end;


function mutual_information(ψ::MixedDestabilizer)
	N = length(ψ)
	n = N ÷ 3
	A = 1:n
	# B = (n+1):2n
	C = (2n+1):3n
	return _cea(ψ, A) + _cea(ψ, C) - _cea(ψ, hcat(A, C))
end;

eig_v(ψ::State) = eig_v(ψ.V)
eig_v(V::Array{ComplexF64}) = eigen(V).values

function mutual_information(ψ::MPS)
	throw(MethodError(mutual_information, (typeof(ψ),), "Function not implemented."))
end

dσ = Dict("X" => (true, false), "Y" => (true, true), "Z" => (false, true))

function get_projection_string(N, i, j, σ)
	p = QuantumClifford.zero(PauliOperator, N)
	p[i] = dσ[σ]
	p[j] = dσ[σ]
	return p
end

corr_length(state::State) = _corr_length(state.ψ)

function _corr_length(ψ::MixedDestabilizer)
	N = length(ψ)
	nc = N ÷ 2 - 1
	corr = zeros(Float64, nc)
	for i in 1:nc
		corr[i] = QuantumClifford.expect(get_projection_string(N, 1, i + 1, "Z"), ψ)
	end
	return corr
end

function _corr_length(ψ::MPS)
	throw(MethodError(_corr_length, (typeof(ψ),), "Function not implemented."))
end

function entropy(p, n)
    if n != 1
        return log(sum(p .^ n)) / (1 - n)
    else
        return -sum(p .* log.(p))
    end
end

function getps(vals; cutoff=1e-12)
    vals = vals[abs.(vals) .> cutoff]
    ps = abs.(vals) .^ 2
	ps = ps ./ sum(ps)
	return ps
end

function Qn(V, n)   # eigenvalues λ
	if size(V) == (0,)
		return 0
	else
		λ = LinearAlgebra.eigvals(V);
		return entropy(getps(λ), n)
	end
end

function Sn(V, n)   # singular values σ
    σ = svdvals(V);
    return entropy(getps(σ), n)
end

Qn(state::State) = Qn(state.V, 1)
Sn(state::State) = Sn(state.V, 1)

const allquants = Dict("entropy" => (func = entanglement_entropy, dsize = (N) -> 1, dtype = Float64, V = false, last = false),
						"tmi" => (func = tmi, dsize = (N) -> 1, dtype = Float64, V = false, last = false),
						"mi" => (func = mutual_information, dsize = (N) -> 1, dtype = Float64, V = false, last = false),
						"V_eig" => (func = eig_v, dsize = (N) -> 2^N, dtype = ComplexF64, V = true, last = true),
						"correlation" => (func = corr_length, dsize = (N) -> N ÷ 2 - 1, dtype = Float64, V = false, last = false),
						"ancilla_entropy" => (func = last_site_entanglement, dsize = (N) -> 1, dtype = Float64, V = false, last = false),
						"opEE" => (func = Qn, dsize = (N) -> 1, dtype = Float64, V = true, last = false),
						"opSVD" => (func = Sn, dsize = (N) -> 1, dtype = Float64, V = true, last = false))

entanglement_entropy(state::State) = entanglement_entropy(state.ψ)
tmi(state::State) = tmi(state.ψ)
mutual_information(state::State) = mutual_information(state.ψ)
last_site_entanglement(state::State) = last_site_entanglement(state.ψ)