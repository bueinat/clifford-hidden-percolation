# imports
import numpy as np
import matplotlib.pyplot as plt
import pandas
import pyzx as zx
import networkx as nx
from tqdm.notebook import tqdm, trange

rng = np.random.default_rng()


def empty_circuit(N, total_t, apply_state=True):
    g = zx.Graph()
    qubits = np.zeros((2 * total_t + 1, N), int)
    for t in range(2 * total_t + 1):
        for i in range(N):
            qubits[t, i] = g.add_vertex(zx.VertexType.BOUNDARY, qubit=i, row=t)

    # set input & output
    g.set_inputs(qubits[0, :])
    g.set_outputs(qubits[-1, :])
    if apply_state:
        g.apply_state("0" * N)  # z

    return g, qubits


def one_layer(N, g, qubits, t, sgates, iter_list, periodic=False):
    for sgate, q1 in zip(sgates, iter_list):
        q2 = q1 + 1
        if q2 > N or sgate == '':
            break
        if q2 == N:
            if periodic:
                q2 = 0
            else:
                break
        eval(sgate)(g, qubits, q1, q2, t=t)


def remove_excess_nodes(g):
    vrlist = list(g.vertices())
    # iterate over all nodes
    for v in vrlist:
        # which are note edge nodes
        if g.type(v) == zx.VertexType.BOUNDARY and v not in g.outputs() and v not in g.inputs():
            neighbors = list(g.neighbors(v))
            if len(neighbors) == 0:     # remove nodes with no neighbors
                g.remove_vertex(v)
            elif len(neighbors) == 1:
                nn = list(g.neighbors(neighbors[0]))
                if len(nn) == 1 and g.type(neighbors[0]) == zx.VertexType.BOUNDARY and neighbors[0] not in g.outputs() and neighbors[0] not in g.inputs():
                    g.remove_vertices([v, neighbors[0]])
                    vrlist.remove(neighbors[0])
                elif len(nn) == 2 and g.type(neighbors[0]) in [zx.VertexType.X, zx.VertexType.Z]:
                    g.remove_vertex(v)
                else:
                    print(v, neighbors, nn)
                    zx.draw(g, labels=True)
                    raise Exception("Error with neighbors")
            else:
                try:
                    g.add_edge(list(g.neighbors(v)),
                                edgetype=zx.EdgeType.SIMPLE)
                except ValueError:
                    print("--- ERROR ---")
                    print(g.neighbors(v))
                    zx.draw(g, labels=True)
                g.remove_vertex(v)


# -> list:
def sample_string_circuit(N, t_factor, p, q, r, periodic=False, **kwargs):
    # generate a row
    # print(p, q, r)
    total_t = int(N * t_factor) // 2 * 2
    lgates = ["swap", "cnot", "id_projection", "bell_projection"]
    lprobs = [(1-p) * (1-r), (1-p) * r, p * (1 - q), p * q]
    circuit = np.full((total_t, N//2), '*' * 15)
    for i in range(0, total_t, 2):
        circuit[i, :] = rng.choice(lgates, size=N//2, p=lprobs)
        circuit[i+1, :] = rng.choice(lgates, size=N//2, p=lprobs)
        if not periodic:
            circuit[i+1, -1] = ""
    return circuit


# -> BaseGraph:
def sample_circuit(N, t_factor, p=None, q=None, r=None, string_circuit=None, apply_state=False, periodic=False):
    # generating stuff
    total_t = int(N * t_factor) // 2 * 2
    if total_t != N * t_factor:
        print(f"total_t = {N * t_factor} was rounded to {total_t}")
    g, qubits = empty_circuit(N, total_t, apply_state)
    if string_circuit is None:
        if p is None or q is None or r is None:
            raise Exception(
                "if no string_circuit was given, (p, q, r) should be given")
        else:
            string_circuit = sample_string_circuit(
                N, t_factor, p, q, r, periodic)
    q1, qN = 0, N-1
    for t in range(0, total_t, 2):
        one_layer(N, g, qubits, t, string_circuit[t],
                    np.arange(0, N, 2), periodic)
        one_layer(N, g, qubits, t+1, string_circuit[t+1],
                    np.arange(0, N, 2)+1, periodic)

        # remove the excess node and connect the two far ones
        if not periodic and t != 0:
            g.remove_vertices(qubits[2*t-1, [q1, qN]])
            g.add_edge(qubits[[2*t-2, 2*t], q1])
            g.add_edge(qubits[[2*t-2, 2*t], qN])

    # this is for the last pair
    if not periodic:
        t += 2
        g.remove_vertices(qubits[2*t-1, [q1, qN]])
        g.add_edge(qubits[[2*t-2, 2*t], q1])
        g.add_edge(qubits[[2*t-2, 2*t], qN])
    # zx.draw(g, labels=True)

    return g


def custom_simp(g, quiet):
    a = 10
    while a > 0:
        a = 0
        a += zx.simplify.simp(g, 'spider_simp',
                                zx.rules.match_spider_parallel, zx.rules.spider, quiet=quiet)
        a += zx.simplify.simp(g, 'id_simp', zx.rules.match_ids_parallel,
                                zx.rules.remove_ids, quiet=quiet)
    return g


def simplify_circuit(g, quiet=False, simp_method=custom_simp, **kwargs):
    remove_excess_nodes(g)
    return simp_method(g, quiet, **kwargs)

# Convert pyzx graph to networkx graph with node types


def pyzx_to_networkx(zx_graph):
    types = {0: "boundary", 1: "Z", 2: "X", 3: "input", 4: "output"}
    nx_graph = nx.Graph()

    # Add vertices with types as attributes
    for v in zx_graph.vertices():
        node_type = types[zx_graph.type(v)]
        if v in zx_graph.inputs():
            node_type = 'input'
        if v in zx_graph.outputs():
            node_type = 'output'
        nx_graph.add_node(v, type=node_type)

    # Add edges
    for e in zx_graph.edges():
        nx_graph.add_edge(e[0], e[1])

    return nx_graph


def networkx_to_pyzx(nx_graph):
    pyzx_graph = zx.Graph()
    inputs, outputs = [], []
    node_types = {'Z': zx.VertexType.Z, 'X': zx.VertexType.X,
                    'input': zx.VertexType.BOUNDARY, 'output': zx.VertexType.BOUNDARY}

    # Add vertices
    for node, data in nx_graph.nodes(data=True):
        # Default to 'Z' type if 'type' attribute is not present
        node_type = data.get('type', 'Z')
        if node_type == 'input':
            inputs.append(node)
        elif node_type == 'output':
            outputs.append(node)

        pyzx_graph.add_vertex_indexed(node)
        pyzx_graph.set_type(node, node_types[node_type])

    pyzx_graph.set_inputs(inputs)
    pyzx_graph.set_outputs(outputs)
    pyzx_graph.add_edges(nx_graph.edges())

    return pyzx_graph


def swap(g, qubits, q1, q2, t):
    g.remove_vertices(qubits[2*t + 1, [q1, q2]])
    g.add_edge(
        g.edge(qubits[2*t, q1], qubits[2*t + 2, q2]), zx.EdgeType.SIMPLE)
    g.add_edge(
        g.edge(qubits[2*t, q2], qubits[2*t + 2, q1]), zx.EdgeType.SIMPLE)


def cnot(g, qubits, q1, q2, t):
    if rng.random() > 0.5:
        q1, q2 = q2, q1
    g.set_type(qubits[2*t + 1, q1], zx.VertexType.Z)
    g.set_type(qubits[2*t + 1, q2], zx.VertexType.X)

    g.add_edge(
        g.edge(qubits[2*t, q1], qubits[2*t + 1, q1]), zx.EdgeType.SIMPLE)
    g.add_edge(g.edge(qubits[2*t + 1, q1],
                        qubits[2*t + 2, q1]), zx.EdgeType.SIMPLE)
    g.add_edge(
        g.edge(qubits[2*t, q2], qubits[2*t + 1, q2]), zx.EdgeType.SIMPLE)
    g.add_edge(g.edge(qubits[2*t + 1, q2],
                        qubits[2*t + 2, q2]), zx.EdgeType.SIMPLE)
    g.add_edge(g.edge(*qubits[2*t + 1, [q1, q2]]), zx.EdgeType.SIMPLE)


def id_projection(g, qubits, q1, q2, t):
    g.remove_vertices(qubits[2*t+1, [q1, q2]])
    g.add_edge(g.edge(*qubits[[2*t, 2*t + 2], q1]), zx.EdgeType.SIMPLE)
    g.add_edge(g.edge(*qubits[[2*t, 2*t + 2], q2]), zx.EdgeType.SIMPLE)


def bell_projection(g, qubits, q1, q2, t):
    g.add_edge(g.edge(*qubits[2*t, [q1, q2]]), zx.EdgeType.SIMPLE)
    g.add_edge(g.edge(*qubits[2*t + 1, [q1, q2]]), zx.EdgeType.SIMPLE)
    g.add_edge(g.edge(*qubits[[2*t + 1, 2*t + 2], q1]), zx.EdgeType.SIMPLE)
    g.add_edge(g.edge(*qubits[[2*t + 1, 2*t + 2], q2]), zx.EdgeType.SIMPLE)


def plot_network(g, **kwargs):
    val_counts = pandas.Series(
        {node: g.nodes[node]['type'] for node in g.nodes}).value_counts()
    type_to_color = {'boundary': 0, 'Z': 'lightgreen',
                        'X': 'indianred', 'input': 'lightgray', 'output': 'gray'}

    new_pos = {}
    dp = {'input': -1, 'X': -0.5, 'Z': 0.5, 'output': 1}
    counts = {'input': 0, 'X': 0, 'Z': 0, 'output': 0}
    for p in g.nodes:
        t = g.nodes[p]['type']
        new_pos[p] = np.array(
            [dp[t], -0.75 + counts[t] / val_counts[t] * 0.75])
        counts[t] += 1

    node_colors = [type_to_color[g.nodes[node]['type']]
                    for node in g.nodes]
    nx.draw(g, new_pos, node_color=node_colors, **kwargs)


def test_circuit(string_circuit, p, q, r, **kwargs):
    expected = pandas.Series({'swap': (1-r) * (1-p), 'cnot': r *
                             (1-p), 'bell_projection': p * q, 'id_projection': p * (1-q)})
    unique, counts = np.unique(string_circuit, return_counts=True)

    sc = pandas.Series(counts, unique)
    sc /= sc.sum()

    return pandas.DataFrame({'expected': expected, 'observed': sc, 'error': abs(sc - expected) / expected})



def general_single_iteration(N, t_factor, function, quiet=False, periodic=False, **kwargs):# -> Any:
    if 'simp_method' not in kwargs:
        kwargs['simp_method'] = zx.full_reduce
    if 'string_circuit' not in kwargs:
        if 'p' not in kwargs or 'q' not in kwargs or 'r' not in kwargs:
            raise Exception(
                "if no string_circuit was given, (p, q, r) should be given")
        else:
            # print(
            #     f"N = {N}, t_factor = {t_factor}, periodic = {periodic}, kwargs = {kwargs}")
            kwargs['string_circuit'] = sample_string_circuit(
                N, t_factor, periodic=periodic, **kwargs)
            if not quiet:
                test_circuit(**kwargs)
    # d = {}
    g = sample_circuit(
        N, t_factor, string_circuit=kwargs['string_circuit'], apply_state=False, periodic=periodic)
    # d['raw'] = g.num_vertices()
    simplify_circuit(g, quiet, simp_method=kwargs['simp_method'])
    # d['simp'] = g.num_vertices()
    if not quiet:
        gc = g.copy()
        gc.normalize()
        zx.draw(gc, labels=True)
    G = pyzx_to_networkx(g)
    # d['nx'] = G.number_of_nodes()
    # return d

    kwargs['N'] = N
    kwargs['t_factor'] = t_factor

    kwargs['quiet'] = quiet
    output = function(G, g, **kwargs)
    if not quiet:
        print(output)
    return output


def percolation_hfunction(G, g, **kwargs):
    # print(g.num_vertices(), G.number_of_nodes())
    gcc = sorted(nx.connected_components(G), key=len, reverse=True)
    lc = len(gcc[0]) / g.num_vertices()
    if len(gcc) > 1:
        slc = len(gcc[1]) / g.num_vertices()
    else:
        slc = 0
    return lc, slc


def find_path_hfunction(G, g, **kwargs):
    source_nodes = {
        node for node in G.nodes if G.nodes[node]['type'] == 'input'}
    target_nodes = {
        node for node in G.nodes if G.nodes[node]['type'] == 'output'}

    for node in source_nodes:
        paths = nx.shortest_path(G, source=node)
        npaths = len(target_nodes.intersection(set(paths.keys())))
        if npaths > 0:
            return True

    return False

### MIN CUT

def capacity_graph(G):
    H = G.copy()
    for edge in H.edges:
        H.edges[edge]['capacity'] = 1
    return H

def input_to_X(G, g, **kwargs):
    for v in g.vertices():
        if v in g.inputs():
            g.set_type(v, zx.VertexType.X)
    simplify_circuit(g, kwargs['quiet'], simp_method=kwargs['simp_method'])
    G = pyzx_to_networkx(g)
    return G, g

def do_nothing(G, g, **kwargs):
    return G, g

def min_cut_wrapped(G, g, st_func, act_func, **kwargs):
    G, g = act_func(G, g, **kwargs)
    H = capacity_graph(G)
    
    source_nodes, target_nodes = st_func(H)
    last_node = max(H.nodes)
    super_source, super_target = last_node + 1, last_node + 2

    H.add_node(super_source)
    H.add_edges_from(
        [(super_source, source, {'capacity': np.inf}) for source in source_nodes])

    H.add_node(super_target)
    H.add_edges_from(
        [(target, super_target, {'capacity': np.inf}) for target in target_nodes])

    return nx.minimum_cut_value(H, super_source, super_target)

def st_initial_to_final(H):
    source_nodes = [n for n in H.nodes if H.nodes[n]['type'] == 'input']
    target_nodes = [n for n in H.nodes if H.nodes[n]['type'] == 'output']
    return source_nodes, target_nodes
    
def st_final_time(H):
    output_nodes = [n for n in H.nodes if H.nodes[n]['type'] == 'output']
    N = len(output_nodes)
    source_nodes = output_nodes[:N//2]
    target_nodes = output_nodes[N//2:]
    return source_nodes, target_nodes

def min_cut_first(G, g, **kwargs):
    return min_cut_wrapped(G, g, st_initial_to_final, do_nothing, **kwargs)

def min_cut_two_halves(G, g, **kwargs):
    return min_cut_wrapped(G, g, st_final_time, do_nothing, **kwargs)

def min_cut_X(G, g, **kwargs):
    return min_cut_wrapped(G, g, st_final_time, input_to_X, **kwargs)

# min_cut_hfunctions = {'first': min_cut_first, 'two_halves': min_cut_two_halves, 'X': min_cut_X}



def min_cut_hfunction(G, g, **kwargs):
    H = G.copy()
    for edge in H.edges:
        H.edges[edge]['capacity'] = 1

    source_nodes = [n for n in H.nodes if H.nodes[n]['type'] == 'input']
    target_nodes = [n for n in H.nodes if H.nodes[n]['type'] == 'output']

    last_node = max(H.nodes)
    super_source, super_target = last_node + 1, last_node + 2

    H.add_node(super_source)
    H.add_edges_from(
        [(super_source, source, {'capacity': np.inf}) for source in source_nodes])

    H.add_node(super_target)
    H.add_edges_from(
        [(target, super_target, {'capacity': np.inf}) for target in target_nodes])

    return nx.minimum_cut_value(H, super_source, super_target)
