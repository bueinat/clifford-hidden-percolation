include("../custom_module/util_code.jl")
using Glob
using Statistics
using ArgParse
using JLD2
using ProgressBars

function parse_commandline()
	s = ArgParseSettings()

	@add_arg_table! s begin
		"data_path"
		required = true
		help = "path of the data. positional"
		"--process_type"
		default = "full"
		help = "full gives you a current dataset ready for use, and combinable gives you a set you can read with other"
		range_tester = (x -> x ∈ ["full", "combinable"])
		help = "process_type must be one of ['full', 'combinable']"
		"--threshold"
		default = 1e-5

	end

	return parse_args(s)
end


function get_Ns(path)
	Ns = []
	for filename in glob("$path/N*.jld2")
		if !occursin("copy", split(filename, "/")[end])
			append!(Ns, getN(filename))
		end
	end

	return sort(Ns)
end;

function get_copyname(filename)
	i = findfirst('.', filename)
	return "$(filename[1:i-1])_copy$(filename[i:end])"
end

function getN(filename)
	s = split(filename, Sys.iswindows() ? "\\" : "/")[end]
	N = parse(Int, split(s, ".")[1][2:end])
	return N
end


function get_keys(path, min_key)
	filename = "$path/N$min_key.jld2"
	jldopen(filename, "r") do fjld
		key = keys(fjld)[end]
		keys_list = fjld[key] |> keys |> collect
		keys_list = [x for x in keys_list if x != "info"]

		if length(keys_list) < 1
			print("error in processing - no data found")
			return
		end
		return keys_list
	end
end


function read_data_q(path, keyname)
	data, info = Dict(), Dict()
	for filename in ProgressBar(glob("$path/N*.jld2"))
		N = getN(filename)

		# you get here only if you actually want to do the analysis
		copyname = get_copyname(filename)
		cp(filename, copyname, force=true)
		jldopen(copyname, "r") do fjld
			key = keys(fjld)[end]
			if keyname in keys(fjld[key])
				data[N] = []
				for j in keys(fjld[key][keyname])
					push!(data[N], fjld[key][keyname][j])
				end
			end
			info[N] = fjld[key]["info"]

		end
		rm(copyname)
	end
	return data, info
end;

function full_process(path, save_file_name, process_keys, threshold)
	# threshold = 1e-5
	Ns = get_Ns(path)
	for keyname in process_keys
		data, info = read_data_q(path, keyname)
		Ns = data |> keys |> collect |> sort

		# info dictionary which contains current data size
		nit = [length(data[N]) for N in Ns]
		println(Dict(N => length(data[N]) for N in Ns))

		jldopen(save_file_name, "a+") do f
			if !("info" in f |> keys)
				f["info"] = info
			end
			key_group = JLD2.Group(f, keyname)
			mean_group = JLD2.Group(key_group, "mean")
			[mean_group[string(N)] = mean(data[N]) for N in Ns]
			std_group = JLD2.Group(key_group, "std")
			[std_group[string(N)] = std(data[N]) ./ sqrt(length(data[N])) for N in Ns]
			p_group = JLD2.Group(key_group, "P")
			[p_group[string(N)] = sum([m .>= threshold for m in data[N]]) / size(data[N], 1) for N in Ns]
			key_group["Ns"] = Ns
			key_group["iteraions"] = nit
		end
	end

	println("processing $path complete.")
end

function partial_process(path, save_file_name, process_keys)
	# TODO: check for full_time
	Ns = get_Ns(path)
	for keyname in process_keys
		data, info = read_data_q(path, keyname)
		Ns = data |> keys |> collect |> sort

		jldopen(save_file_name, "a+") do f
			if !("info" in f |> keys)
				f["info"] = info
			end
			key_group = JLD2.Group(f, keyname)

			try
				# this would only work for full data
				key_group["data"] = cat([hcat(data[N]...) for N in Ns]..., dims=4)
			catch err
				pd_group = JLD2.Group(key_group, "partial_data")
				for N in Ns
					pd_group[string(N)] = hcat(data[N]...)
				end
			end
		end
	end

	println("processing $path complete.")
end


args = parse_commandline()
path = args["data_path"]

if args["process_type"] == "full"
	save_name = "current_data.jld2"
else
	save_name = "full_data.jld2"
end


save_file_name = "$path/$save_name"
if isfile(save_file_name)
	rm(save_file_name)
end

Ns = get_Ns(path)
process_keys = get_keys(path, Ns[1])

if args["process_type"] == "full"
	full_process(path, save_file_name, process_keys, args["threshold"])
else
	partial_process(path, save_file_name, process_keys)
end