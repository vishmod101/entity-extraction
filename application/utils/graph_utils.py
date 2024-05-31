import pandas as pd
import networkx as nx
from pyvis.network import Network


def create_graph(gdf: pd.DataFrame):
    G = nx.Graph()

    ## Add nodes to the graph
    #for node in un_ent_lst:
    #    G.add_node(
    #        str(node)
    #    )

    ## Add edges to the graph
    for index, row in gdf.iterrows():
        G.add_edge(
            str(row["node_1"]),
            str(row["node_2"]),
            title=row["edge"],
        )

    return G


def create_vis(g, title):
    net = Network(
        notebook=True,
        bgcolor="#FFFFF",
        cdn_resources="remote",
        height="800px",
        width="100%",
        select_menu=True,
        font_color="#6a6b6f",
        filter_menu=False,
    )

    net.from_nx(g)
    # net.repulsion(node_distance=150, spring_length=400)
    # net.force_atlas_2based(central_gravity=0.015, gravity=-31)
    net.barnes_hut(gravity=-18100, central_gravity=5.05, spring_length=380)

    # net.show(graph_output_directory)
    #net.show_buttons(filter_=['physics'])
    net.show(f"{title}.html")


def export_graph(g, title):
    nx.write_gexf(g, f'{title}.gexf')
    # todo - save outside container