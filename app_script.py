import streamlit as st

import pandas as pd
import altair as alt
#import re
#from sklearn.linear_model import LinearRegression


st.set_page_config(page_title="Phillips2025", page_icon=":test_tube:", layout="wide")


@st.cache_data
def load_data(data_url):
    df = pd.read_csv(data_url)
    #df.index = df["design"]
    return df


fold_data_url = "https://raw.githubusercontent.com/aphren/Phillips2025/refs/heads/main/streamlit_dataset.csv"
fold_data = load_data(fold_data_url)

## extract a dictionary to retrieve gene descriptions

gene_data_url = "https://raw.githubusercontent.com/aphren/Phillips2025/refs/heads/main/gene_data.csv"
gene_data = load_data(gene_data_url)


st.sidebar.markdown(
    """<center>
    <h2>Welcome to our gRNA data visualization tool! <br> <a href="https://www.biorxiv.org/content/10.1101/2025.05.23.651106v3.abstract">Phillips et al. 2025</a> <h2>
    <br>
    """,    
    unsafe_allow_html=True,
)

gene_input = st.sidebar.text_input(
    "Enter gene name: ", key="gene_user_input"
)
gene_list = gene_input.split()

try:
    gene_start = gene_data[gene_data['gene_name'] == gene_input]['start'].values[0].astype(int)
    gene_end = gene_data[gene_data['gene_name'] == gene_input]['end'].values[0].astype(int)
except:
    st.write('Error: Invalid gene name')
    gene_start = 0
    gene_end = 0

relevant_guides = fold_data[(fold_data['start'] >= gene_start) & (fold_data['end'] <= gene_end)]






# Define shared x-scale with domain from gene_start to gene_end
x_scale = alt.Scale(domain=[gene_start, gene_end])



# Chart for relevant guides (floating horizontal bars)
chart2 = alt.Chart(relevant_guides).mark_bar(size=10).encode(
    x=alt.X('start:Q', scale=alt.Scale(domain=[gene_start, gene_end]), title=['Chromosomal Position']),
    x2='end:Q',
    y=alt.Y('A-score:Q', title=['A-score']),
    color=alt.Color('A-score:Q', scale=alt.Scale(scheme='blues'), legend=alt.Legend(title='A-score')),
    tooltip=['design','A-score','start']
)

# Layer charts and share x scale to have a single x-axis
final_chart = alt.layer(chart2)

st.altair_chart(final_chart, use_container_width=True)
st.write(relevant_guides)
st.write(gene_data)


