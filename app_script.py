import streamlit as st

import pandas as pd
import altair as alt
import time

# import re
# from sklearn.linear_model import LinearRegression


st.set_page_config(page_title="Phillips2025", page_icon=":test_tube:", layout="wide")


@st.cache_data
def load_data(data_url):
    df = pd.read_csv(data_url)
    # df.index = df["design"]
    return df


fold_data_url = "https://raw.githubusercontent.com/aphren/Phillips2025/refs/heads/main/streamlit_dataset.csv"
fold_data = load_data(fold_data_url)
fold_data["abs_start"] = fold_data[["start", "end"]].min(axis=1)

## extract a dictionary to retrieve gene descriptions

gene_data_url = "https://raw.githubusercontent.com/aphren/Phillips2025/refs/heads/main/gene_data.csv"
gene_data = load_data(gene_data_url)
gene_data["gene_name_lower"] = gene_data["gene_name"].str.lower()


st.sidebar.markdown(
    """<center>
    <h2>Welcome to our gRNA data visualization tool! <br> <a href="https://www.biorxiv.org/content/10.1101/2025.05.23.651106v3.abstract">Phillips et al. 2025</a> <h2>
    <br>
    """,
    unsafe_allow_html=True,
)

# Dropdown for gene selection
gene_input_dropdown = st.sidebar.selectbox(
    "Select a gene from the dropdown:",
    gene_data["gene_name"],
    index=None,
    placeholder="Choose a gene...",
)

if not gene_input_dropdown:
    st.markdown(
        """
            ### This tool allows you to:
            - Select a gene and view all gRNAs targeting the corresponding chromosomal region.
            High A-score indicates effective guides. 
            - View and download gRNA-specific data (A-score, sequence, position, etc.)
            ### Getting started:
            - Select a gene from the sidebar dropdown menu, or manually enter a gene name in the text box
            - View all guides targeting said gene and view corresponding data below
            - Chromosome positions are auto-populated for the selected gene, but custom values can be entered
            to view a specific region 
            ### Tip:
            - Charts sometimes take a while to load. To speed things up, clear one of the sidebar inputs
            to reset the page, reselect your gene/regions, then click Load Chart
            """
    )
    gene_start = None
    gene_end = None


if gene_input_dropdown:
    gene_input = gene_input_dropdown.lower()
    gene_start = (
        gene_data[gene_data["gene_name_lower"] == gene_input]["start"]
        .values[0]
        .astype(int)
    )
    gene_end = (
        gene_data[gene_data["gene_name_lower"] == gene_input]["end"]
        .values[0]
        .astype(int)
    )

chrom_pos_start = st.sidebar.text_input(
    "Starting chromosomal position:",
    value=int(gene_start) if gene_start is not None else "",
    key="chrom_start",
)

chrom_pos_end = st.sidebar.text_input(
    "Ending chromosomal position:",
    value=int(gene_end) if gene_end is not None else "",
    key="chrom_end",
)


## add checkbox for guides outside of genes
## add boxes for entering manual chromosomal positions
## graph all genes in that area
## expand view button? for easy expansion?

if chrom_pos_start and chrom_pos_end and st.sidebar.button("Load Chart"):

    chart_start = int(chrom_pos_start) - 20
    chart_end = int(chrom_pos_end) + 20

    relevant_guides = fold_data[
        (fold_data["abs_start"] >= chart_start)
        & (fold_data["abs_start"] <= chart_end - 20)
    ]

    relevant_genes = gene_data[
        (gene_data["end"] >= chart_start) & (gene_data["start"] <= chart_end)
    ]
    relevant_genes["chart_start"] = relevant_genes["start"].clip(lower=chart_start)
    relevant_genes["chart_end"] = relevant_genes["end"].clip(upper=chart_end)

    relevant_genes["arrow_pos"] = relevant_genes.apply(
        lambda row: row["chart_start"] if row["strand"] == "+" else row["chart_end"],
        axis=1,
    )

    relevant_genes["triangle_shape"] = relevant_genes["strand"].map(
        {"+": "triangle-right", "-": "triangle-left"}
    )
    relevant_genes["midpoint"] = (
        relevant_genes["chart_start"]
        + (relevant_genes["chart_end"] - relevant_genes["chart_start"]) / 2
    )
    relevant_genes["y"] = min(relevant_guides["A-score"]) - 1

    if not relevant_guides.empty:

        # Define shared x-scale with domain from gene_start to gene_end
        x_scale = alt.Scale(domain=[chart_start, chart_end])

        # Chart for relevant guides (floating horizontal bars)
        chart_guides = (
            alt.Chart(relevant_guides)
            .mark_bar(size=10)
            .encode(
                x=alt.X("start:Q", scale=x_scale, title=["Chromosomal Position"]),
                x2="end:Q",
                y=alt.Y("A-score:Q", title=["A-score"]),
                color=alt.Color(
                    "A-score:Q",
                    scale=alt.Scale(scheme="blues"),
                    legend=alt.Legend(title="A-score"),
                ),
                tooltip=["design", "A-score", "start"],
            )
        )

        chart_genes = (
            alt.Chart(relevant_genes)
            .mark_bar(size=10, color="green", opacity=1.0)
            .encode(
                x=alt.X("chart_start:Q", scale=x_scale),
                x2="chart_end:Q",
                y=alt.Y("y:Q"),  # fixed Y
                tooltip=["gene_name", "start", "end", "strand"],
                color=alt.Color(
                    "gene_name:N", scale=alt.Scale(scheme="category10"), legend=None
                ),
            )
        )

        chart_arrows = (
            alt.Chart(relevant_genes)
            .mark_point(
                shape="diamond",
                size=350,
                filled=True,
                opacity=1.0,
            )
            .encode(
                x=alt.X("arrow_pos", type="quantitative", scale=x_scale),
                y=alt.Y("y:Q"),
                color=alt.Color(
                    "gene_name:N", scale=alt.Scale(scheme="category10"), legend=None
                ),
            )
        )

        chart_text = (
            alt.Chart(relevant_genes)
            .mark_text(
                color="white",
                fontWeight="bold",
                fontSize=15,
                align="center",
                baseline="middle",
                dy=-1.5,
            )
            .encode(
                text="gene_name",
                x=alt.X("midpoint:Q", scale=x_scale),
                y=alt.Y("y:Q"),
                tooltip=alt.TooltipValue(""),
            )
        )

        chart_lines = (
            alt.Chart(pd.DataFrame({"y": [2]}))
            .mark_rule(strokeDash=[5, 5], color="red")
            .encode(y="y:Q")
        )
        combined_chart = (
            alt.layer(chart_guides, chart_lines, chart_genes, chart_arrows, chart_text)
            # .properties(title=f"gRNAs targeting {gene_input_dropdown}")
            .configure_title(anchor="middle", fontSize=16)
        )
        st.altair_chart(combined_chart, use_container_width=True)
        st.write(
            "gRNA data:", relevant_guides[["design", "A-score", "start", "sequence"]]
        )

    if relevant_guides.empty:
        st.write("No guides targeting this gene")
