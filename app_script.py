import streamlit as st

import pandas as pd
import altair as alt

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


# chrom_pos_end =


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
            ### Tip:
            - For faster chart loading, clear your previous gene selection with the x in the dropdown prior to selecting a new one.
            """
    )


## add checkbox for guides outside of genes
## add boxes for entering manual chromosomal positions
## graph all genes in that area
## expand view button? for easy expansion?

if gene_input_dropdown:
    gene_input = gene_input_dropdown.lower()
else:
    gene_input = None


if gene_input and gene_input in gene_data["gene_name_lower"].to_list():
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
        value=gene_start - 20,
        key="chrom_start",
    )

    chrom_pos_end = st.sidebar.text_input(
        "Ending chromosomal position:", value=gene_end - 20, key="chrom_end"
    )

    chart_start = int(chrom_pos_start) - 20
    chart_end = int(chrom_pos_end) + 20

    relevant_guides = fold_data[
        (fold_data["start"] >= chart_start) & (fold_data["end"] <= chart_end)
    ]

    if not relevant_guides.empty:
        strand = gene_data[gene_data["gene_name_lower"] == gene_input]["strand"].values[
            0
        ]

        # Define shared x-scale with domain from gene_start to gene_end
        x_scale = alt.Scale(domain=[chart_start, chart_end])

        # Chart for relevant guides (floating horizontal bars)
        chart2 = (
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

        # Data/chart for gene bars:
        gene_bar = pd.DataFrame(
            {
                "start": [gene_start],
                "end": [gene_end],
                "y": [min(relevant_guides["A-score"]) - 1],  # place below guide bars
                "direction": ["forward" if strand == "+" else "reverse"],
                "gene": [gene_input_dropdown],
                "midpoint": [(gene_start + gene_end) / 2],
            }
        )
        gene_chart = (
            alt.Chart(gene_bar)
            .mark_bar(size=10, color="green", opacity=1.0)
            .encode(
                x=alt.X("start:Q", scale=x_scale),
                x2="end:Q",
                y=alt.Y("y:Q"),  # fixed Y
                tooltip=["gene", "direction"],
            )
        )

        # Show gene direction
        x_field = "end:Q" if strand == "+" else "start:Q"
        rotation = -30 if gene_end > gene_start else 30

        arrow_chart = (
            alt.Chart(gene_bar)
            .mark_point(
                shape="triangle", size=450, color="green", filled=True, opacity=1.0
            )
            .encode(
                x=alt.X(x_field, type="quantitative", scale=x_scale),
                y=alt.Y("y:Q"),
                angle=alt.value(-30 if gene_bar["direction"][0] == "forward" else 30),
            )
        )
        # Text on the gene bar

        text_chart = gene_chart.mark_text(
            # align="center",
            # baseline="middle",
            color="white",
            fontWeight="bold",
            fontSize=15,
            align="right",
            baseline="middle",
            dy=-1.5,
        ).encode(text="gene", x=alt.X("midpoint:Q", scale=x_scale))

        combined_chart = (
            alt.layer(chart2, gene_chart, arrow_chart, text_chart)
            .properties(title=f"gRNAs targeting {gene_input_dropdown}")
            .configure_title(anchor="middle", fontSize=16)
        )
        with st.spinner("Rendering in your browser..."):
            st.altair_chart(combined_chart, use_container_width=True)
            st.write("gRNA data:", relevant_guides)

        # st.write(gene_data)
    if relevant_guides.empty:
        st.write("No guides targeting this gene")

elif gene_input and gene_input not in gene_data["gene_name_lower"].to_list():
    st.write("Error: Invalid gene name")
