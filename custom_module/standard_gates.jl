using QuantumClifford
using ITensors
using LinearAlgebra: diagm

# mutable struct Gate
# 	name::string
# 	operator::Union{ITensor, AbstractArray{<:QuantumClifford.AbstractOperation}}
# end
const Gate = Union{ITensor, AbstractArray{<:QuantumClifford.AbstractOperation}}

mutable struct State
	sites::Vector{Index{Int64}}
	ψ::Union{MPS, MixedDestabilizer}
	gate_func::Function
	process_func::Function
	V::Array{ComplexF64}
	ancillas::Array{Int}
end

function nqubits(state::State)
	if typeof(state.ψ) == ITensors.MPS
		return length(state.sites) - length(state.ancillas)
	else
		return QuantumClifford.nqubits(state.ψ) - length(state.ancillas)
	end
end

dσ = Dict("X" => (true, false), "Y" => (true, true), "Z" => (false, true))

function get_projection_string(N, i, j, σ)
	p = QuantumClifford.zero(PauliOperator, N)
	p[i] = dσ[σ]
	p[j] = dσ[σ]
	return p
end

# this is, for example, an Haar gate
function haar_matrix(n::Int = 4)
    # Step 1: Create a matrix with complex Gaussian random entries
    A = randn(ComplexF64, n, n)
    
    # Step 2: Perform QR decomposition
    Q, R = qr(A)
    
    # Step 3: Extract the unitary matrix Q
    # Ensure the diagonal elements of R are positive real numbers
    d = diag(R)
    ph = d ./ abs.(d)
    Q = Q * Diagonal(ph) * Q
    
    return Q
end

# @qubitop2 CNOT   (x1 , z1⊻z2 , x2⊻x1 , z2    , ~iszero( (x1 & z1 & x2 & z2)  | (x1 & z2 &~(z1|x2)) )
z_meas_gate(q1::Int, q2::Int)::Gate = [sMZ(q1)]::Gate;
id_meas_gate(q1::Int, q2::Int)::Gate = Vector{QuantumClifford.AbstractOperation}(undef, 0)::Gate;
random_gate(q1::Int, q2::Int)::Gate = [SparseGate(random_clifford(2), [q1, q2])]::Gate;

bell_meas_gate(q1::Int, q2::Int)::Gate = [sCNOT(q1, q2), sHadamard(q1), sMZ(q1), sMZ(q2), sHadamard(q1), sCNOT(q1, q2)]::Gate;
swap_gate(q1::Int, q2::Int)::Gate = [sSWAP(q1, q2)]::Gate;
lcnot_gate(q1::Int, q2::Int)::Gate = [sCNOT(q1, q2)]::Gate;
rcnot_gate(q1::Int, q2::Int)::Gate = [sCNOT(q2, q1)]::Gate;


_RCNOT = [1 0 0 0
	0 0 0 1
	0 0 1 0
	0 1 0 0]

_ID = [1 0 0 0
	0 1 0 0
	0 0 1 0
	0 0 0 1]

_Bell = [1 0 0 1
	0 0 0 0
	0 0 0 0
	1 0 0 1] .* 0.5

u2() = ITensors.kron(haar_matrix(2), haar_matrix(2))

Sx = [0 1; 1  0] ./ 2
Sz = [1 0; 0 -1] ./ 2
Hx = 0.3 * ITensors.kron(Sx, Sx) + 0.2 * (ITensors.kron(Sx, ITensors.I(2)) + ITensors.kron(ITensors.I(2), Sx))
Hz = 0.4 * ITensors.kron(Sz, Sz) + 0.5 * (ITensors.kron(Sz, ITensors.I(2)) + ITensors.kron(ITensors.I(2), Sz))
_U(Δt) = exp(-im * Δt * (Hx + Hz))

_SZM = 2 * ITensors.kron(Sz, ITensors.I(2))

function ITensors.op(::OpName"Random", ::SiteType"S=1/2", s1::Index, s2::Index; Δt::Float64 = 0.0)
	if Δt == 0
		V = haar_matrix(4)
	else
		V = u2() * _U(Δt) * u2()
	end
	return itensor(V, s2', s1', s2, s1)
end


function ITensors.op(::OpName"RCNOT", ::SiteType"S=1/2", s1::Index, s2::Index; Δt::Float64 = 0.0)
	return itensor(_RCNOT, s2', s1', s2, s1)
end

function ITensors.op(::OpName"ID", ::SiteType"S=1/2", s1::Index, s2::Index; Δt::Float64 = 0.0)
	return itensor(_ID, s2', s1', s2, s1)
end

function ITensors.op(::OpName"Bell", ::SiteType"S=1/2", s1::Index, s2::Index; Δt::Float64 = 0.0)
	return itensor(_Bell, s2', s1', s2, s1)
end

szup = 2 * ITensors.kron([1 0; 0 0], ITensors.I(2))
szdn = 2 * ITensors.kron([0 0; 0 -1], ITensors.I(2))

function ITensors.op(::OpName"SZM", ::SiteType"S=1/2", s1::Index, s2::Index; Δt::Float64 = 1.0)
	# Δt is a multiplication factor
	return itensor(Δt * szup, s2', s1', s2, s1)
end


bell_meas_gate()::String = "Bell";
id_meas_gate()::String = "ID";
z_meas_gate()::String = "SZM";

swap_gate()::String = "Swap";
lcnot_gate()::String = "CNOT";
rcnot_gate()::String = "RCNOT";
random_gate()::String = "Random";

function ggen_unitaries(; p)
	return Dict{String, Float64}("random_gate" => 1)
end;

function ggen_measurements(; p)
	return Dict{String, Float64}("id_meas_gate" => (1 - p),
		"z_meas_gate" => p)
end;


function ggen_ata_unitaries(; p)
	return Dict{String, Float64}("random_gate" => (1 - p),
		"id_meas_gate" => p)
end;

function ggen_ata_measurements(; p)
	return Dict{String, Float64}("id_meas_gate" => (1 - p),
		"z_meas_gate" => p)
end;
