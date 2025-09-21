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

# If a dropdown choice is made, use it to populate the text input
if gene_input_dropdown:
    default_text = gene_input_dropdown
else:
    default_text = ""


# Text input with dropdown as default value
gene_input_manual = st.sidebar.text_input(
    "Or enter gene name manually:", value=default_text, key="gene_user_input"
)

if not gene_input_manual:
    st.markdown(
        """
            ### This tool allows you to:
            - Select a gene and view all gRNAs targeting the corresponding chromosomal region.
            High A-score indicates effective guides. 
            - View and download gRNA-specific data (A-score, sequence, position, etc.)
            ### Getting started:
            - Select a gene from the sidebar dropdown menu, or manually enter a gene name in the text box
            - View all guides targeting said gene and view corresponding data below
    
            """
    )


## add checkbox for guides outside of genes
## add boxes for entering manual chromosomal positions
## graph all genes in that area
## expand view button? for easy expansion?


gene_input = gene_input_manual.lower()
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

    relevant_guides = fold_data[
        (fold_data["start"] >= gene_start) & (fold_data["end"] <= gene_end)
    ]

    strand = gene_data[gene_data["gene_name_lower"] == gene_input]["strand"].values[0]

    # Define shared x-scale with domain from gene_start to gene_end
    x_scale = alt.Scale(domain=[gene_start - 20, gene_end + 20])

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
            "gene": [gene_input_manual],
        }
    )
    gene_chart = (
        alt.Chart(gene_bar)
        .mark_bar(size=10, color="green", opacity=0.5)
        .encode(
            x="start:Q",
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
        .mark_point(shape="triangle", size=100, color="green", filled=True)
        .encode(
            x=alt.X(
                x_field,
                type="quantitative",
            ),
            y=alt.Y("y:Q"),
            angle=alt.value(-30 if gene_bar["direction"][0] == "forward" else 30),
        )
    )

    combined_chart = (
        alt.layer(chart2, gene_chart, arrow_chart)  # your guide bars  # gene indicator
        .properties(title=f"gRNAs targeting {gene_input_manual}")
        .configure_title(anchor="middle", fontSize=16)
    )

    st.altair_chart(combined_chart, use_container_width=True)
    st.write(relevant_guides)
    st.write(gene_data)
elif gene_input and gene_input not in gene_data["gene_name_lower"].to_list():
    st.write("Error: Invalid gene name")
