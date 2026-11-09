import altair as alt
import folium
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import requests
import seaborn as sns
import streamlit as st
from streamlit_folium import st_folium

API_BAIRROS_URL = (
    "https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Cartografia/"
    "Limites_administrativos/MapServer/4/query"
)

BACKGROUND_GRAFICOS = "#e7e7e7"
FONT_COLOR = "#383B3E"
FONT_FAMILY = "monospace"


@st.cache_data
def get_data():
    df = pd.read_csv(
        "dados/ITBI_-_TransaA7B5es_por_Logradouro_e_MAAs_-_ImB3veis_Residenciais_e_NA3o_Residenciais.csv"
    )
    df = df.dropna(subset=["média_valor_imóvel"])
    pd.set_option("display.float_format", lambda x: "%.2f" % x)

    return df


def selecionar_anos(df: pd.DataFrame):
    ano_minimo = df["ano_transação"].unique().min()
    ano_maximo = df["ano_transação"].unique().max()

    anos_slider = st.sidebar.slider(
        "Selecionar Anos:", ano_minimo, ano_maximo, (ano_minimo, ano_maximo)
    )
    anos_lista = list(range(anos_slider[0], anos_slider[1] + 1))

    df_filtrado = df[df["ano_transação"].isin(anos_lista)]

    return df_filtrado


@st.cache_data
def gerar_geojson_bairros(df: pd.DataFrame) -> dict:
    bairros_df = set(
        df["bairro"]
        .dropna()
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    if not bairros_df:
        raise ValueError("A coluna 'bairro' não possui valores válidos.")

    resposta = requests.get(
        API_BAIRROS_URL,
        params={
            "where": "1=1",
            "outFields": "*",
            "outSR": "4326",
            "f": "geojson",
        },
        timeout=30,
    )
    resposta.raise_for_status()
    geojson = resposta.json()

    geojson["features"] = [
        feature
        for feature in geojson.get("features", [])
        if str(feature.get("properties", {}).get("nome", "")).strip() in bairros_df
    ]

    if not geojson["features"]:
        raise ValueError("Nenhum bairro do dataframe foi encontrado na API.")

    return geojson


@st.cache_data
def estatistica_bairros(df: pd.DataFrame):
    media_imoveis_bairro = pd.DataFrame({"bairro": [], "media_valor_imovel": []})
    bairro_transacoes = df.groupby(by=["bairro", "codbairro"], as_index=False)[
        "total_transações"
    ].sum()

    bairros = df["bairro"].unique()

    for i in range(len(bairros)):
        bairro = df[["bairro", "total_transações", "média_valor_imóvel"]][
            df["bairro"] == bairros[i]
        ]
        soma_transacoes = bairro["total_transações"].sum()

        valores = []
        for r in range(len(bairro)):
            valores.append(
                bairro["média_valor_imóvel"].iloc[r]
                * bairro["total_transações"].iloc[r]
            )

        soma_valores = sum(valores)
        new_row = {
            "bairro": bairro["bairro"].iloc[0],
            "media_valor_imovel": soma_valores / soma_transacoes,
        }
        media_imoveis_bairro.loc[len(media_imoveis_bairro)] = new_row

    bairros_stat = bairro_transacoes.merge(
        media_imoveis_bairro, on="bairro", how="left"
    )
    bairros_stat.set_index("codbairro", inplace=True)
    return bairros_stat


def display_map(geo_dados: dict, bairros_stat: pd.DataFrame):
    estatisticas = bairros_stat.reset_index().copy()
    estatisticas["bairro"] = (
        estatisticas["bairro"]
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    estatisticas_por_bairro = estatisticas.drop_duplicates("bairro").set_index("bairro")

    mapa_rio = folium.Map(
        location=[-22.9, -43.4],
        zoom_start=10,
        scrollWheelZoom=False,
    )

    choropleth = folium.Choropleth(
        geo_data=geo_dados,
        data=estatisticas,
        columns=["bairro", "total_transações"],
        key_on="feature.properties.nome",
        fill_color="YlOrRd",
        nan_fill_color="white",
        bins=10,
        legend_name="Total Transações",
        fill_opacity=0.9,
        line_opacity=0.2,
    ).add_to(mapa_rio)
    choropleth.color_scale.width = 500

    for feature in choropleth.geojson.data["features"]:
        nome_bairro = " ".join(
            str(feature.get("properties", {}).get("nome", "")).split()
        )
        estatistica = estatisticas_por_bairro.loc[nome_bairro]
        feature["properties"]["total_transações"] = int(estatistica["total_transações"])
        feature["properties"]["media_valor_imovel"] = round(
            float(estatistica["media_valor_imovel"]), 2
        )

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=["nome", "total_transações", "media_valor_imovel"],
            aliases=[
                "Bairro:",
                "Total de transações:",
                "Média valor do imóvel:",
            ],
            labels=True,
            sticky=False,
            localize=True,
            style=(
                "max-width: 500px; font-size: 14px; padding: 10px; font-family: FONT_FAMILY"
            ),
        )
    )

    st_folium(mapa_rio, width=700, height=400)


def grafico_logradouro_transacoes(df: pd.DataFrame):
    logradouro_total_transacao = df.groupby(by="logradouro", as_index=False)[
        "total_transações"
    ].sum()
    logradouro_total_transacao.sort_values(
        by="total_transações", ascending=False, inplace=True
    )
    top10_logradouro = logradouro_total_transacao.head(10)

    fig, ax = plt.subplots(figsize=(8, 13.5))
    sns.set_theme(font=FONT_FAMILY)
    ax = sns.barplot(
        data=top10_logradouro,
        y=top10_logradouro["logradouro"].head(10),
        hue=top10_logradouro["logradouro"].head(10),
        x=top10_logradouro["total_transações"].head(10),
        orient="h",
        palette="crest_r",
        legend="auto",
    )

    sns.set_style(
        rc={"axes.facecolor": "black", "figure.facecolor": BACKGROUND_GRAFICOS}
    )

    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_title(
        "Top 10 Logradouros com mais transações",
        fontsize=22,
        color="black",
        fontdict={"weight": "bold"},
    )
    ax.set_frame_on(False)
    ax.yaxis.set_tick_params(labelsize=16)
    ax.tick_params(axis="y", colors=FONT_COLOR)

    for i, v in enumerate(top10_logradouro["total_transações"].head(10)):
        ax.text(
            v + 20, i, str(v), color=FONT_COLOR, fontsize=16, ha="left", va="center"
        )

    ax.get_xaxis().set_visible(False)

    st.pyplot(fig)


def grafico_transacoes_ano(df: pd.DataFrame):
    transacao_ano = df.groupby(by="ano_transação", as_index=False)[
        "total_transações"
    ].sum()

    fig = px.line(
        transacao_ano,
        x=transacao_ano["ano_transação"],
        y=transacao_ano["total_transações"],
    )
    fig.update_traces(line_color="#334670", line_width=4, mode="markers+lines")

    fig.update_layout(
        width=10,
        height=400,
        plot_bgcolor=BACKGROUND_GRAFICOS,
        paper_bgcolor="#8F8F8C",
        font_family=FONT_FAMILY,
        font_size=16,
        title_font_color="black",
        title_font_size=18,
        title={
            "text": "Número de Transações por Ano",
            "xanchor": "center",
            "x": 0.5,
            "yanchor": "bottom",
        },
        xaxis={"tickangle": -45},
        yaxis_title="Transações",
        xaxis_title="Ano",
    )

    st.plotly_chart(fig)


@st.cache_data
def media_valor_imoveis(df: pd.DataFrame):
    valores = []
    for i in range(len(df)):
        valores.append(
            df["média_valor_imóvel"].iloc[i] * df["total_transações"].iloc[i]
        )

    soma_valores = sum(valores)
    soma_transacoes = df["total_transações"].sum()

    media_valor_imoveis = soma_valores / soma_transacoes

    return media_valor_imoveis


@st.cache_data
def total_transacoes(df: pd.DataFrame):
    return df["total_transações"].sum()


def main():
    df = get_data()
    df_filtrado = selecionar_anos(df)

    st.set_page_config(
        page_title="Imóveis Rio de Janeiro",
        page_icon=":office:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    alt.themes.enable("dark")

    st.title("Transção Imóveis Rio de Janeiro :office:")
    st.markdown(
        "Dashboard utilizando dados de transações imobiliárias por Logradouro, na Cidade do Rio de Janeiro disponibilizado na [DATA.RIO](https://www.data.rio/datasets/5e4dda4d33f44b1eb9246559b281d1b8_8/explore)"
    )

    col1, col2 = st.columns([0.6, 0.4], gap="xsmall")
    col_card, col_grafico_linha = st.columns([0.2, 0.8], gap="xsmall")

    with col1:
        geo_bairros = gerar_geojson_bairros(df_filtrado)
        bairro_stat = estatistica_bairros(df_filtrado)
        display_map(geo_bairros, bairro_stat)

    with col2:
        grafico_logradouro_transacoes(df_filtrado)

    with col_card:
        st.metric(
            label="Total de Transações",
            value=total_transacoes(df_filtrado),
            format="localized",
            border=True,
        )
        st.metric(
            label="Média Valor Imovéis",
            value=round(media_valor_imoveis(df_filtrado), 2),
            format="localized",
            border=True,
        )

    with col_grafico_linha:
        grafico_transacoes_ano(df_filtrado)


if __name__ == "__main__":
    main()
