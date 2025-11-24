#!/usr/bin/env python3
"""
Streamlit app ligera para mostrar los resultados NDVI desde outputs/.
Ruta esperada para datos: ../outputs (relativo a esta app).
"""
import os
import json
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

# Rutas relativas (funciona estando el archivo en 01_VerdeMetria/app/)
BASE_DIR = os.path.dirname(__file__)                # .../01_VerdeMetria/app
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))  # .../01_VerdeMetria
OUT = os.path.join(PROJECT_DIR, 'outputs')
CSV_AREAS = os.path.join(OUT, 'areas_by_sector_vs_2016.csv')
CSV_AREAS_FILTERED = os.path.join(OUT, 'areas_by_sector_vs_2016_filtered.csv')
GEOJSON_YEAR = os.path.join(OUT, 'areas_by_municipio_2025.geojson')  # ejemplo
CHOROPLETH_HTML = os.path.join(OUT, 'choropleth_cumulative_pct.html')

st.set_page_config(layout="wide", page_title="NDVI Changes Explorer")

st.title("NDVI Changes Explorer — pérdidas/ganancias vs 2016")
st.markdown("Interactivo (datos desde carpeta outputs/ del proyecto)")

@st.cache_data
def load_csv(path):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)

@st.cache_data
def load_geojson(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# cargar datos (prefiere filtrado si existe)
df = load_csv(CSV_AREAS_FILTERED) or load_csv(CSV_AREAS)
if df is None:
    st.error("No encontré CSV de áreas en outputs/. Ejecuta el notebook y exporta los resultados a outputs/")
    st.stop()

df.columns = [c.strip() for c in df.columns]
if 'area_ha' not in df.columns and 'area_m2' in df.columns:
    df['area_ha'] = df['area_m2'] / 10000.0

years = sorted(df['year'].astype(int).unique())
kinds = sorted(df['kind'].unique())

# Controls sidebar
st.sidebar.header("Filtros")
year = st.sidebar.selectbox("Año", options=years, index=len(years)-1)
kind = st.sidebar.radio("Tipo", options=kinds, index=0)
topN = st.sidebar.slider("Top N", min_value=3, max_value=50, value=10)
name_col = st.sidebar.text_input("Campo nombre municipio", value="NAME_2")

left_col, right_col = st.columns((1,1))

with left_col:
    st.subheader(f"Top {topN} municipios — {kind} — {year}")
    sub = df[(df['year']==int(year)) & (df['kind']==kind)].copy()
    if sub.empty:
        st.info("No hay datos para la selección.")
    else:
        top = sub.sort_values('area_ha', ascending=False).head(topN)
        st.dataframe(top[[name_col, 'area_ha']].rename(columns={name_col: "Municipio", 'area_ha': 'Área (ha)'}).reset_index(drop=True))
        fig, ax = plt.subplots(figsize=(6, max(3, 0.3*len(top))))
        ax.barh(top[name_col].astype(str), top['area_ha'], color='green' if kind=='gain' else 'red')
        ax.invert_yaxis()
        ax.set_xlabel('Área (ha)')
        ax.set_title(f'Top {topN} {kind} — {year}')
        st.pyplot(fig)
        csv_bytes = top.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar Top actual (CSV)", data=csv_bytes, file_name=f"top{topN}_{kind}_{year}.csv", mime='text/csv')

with right_col:
    st.subheader("Mapa interactivo")
    geo = load_geojson(GEOJSON_YEAR)
    if geo:
        # build value map for selected year/kind
        sel = df[(df['year']==int(year)) & (df['kind']==kind)].set_index(name_col)['area_ha'].to_dict()
        for feat in geo.get('features', []):
            key = feat.get('properties', {}).get(name_col) or feat.get('properties', {}).get('NAME_2')
            feat['properties']['value'] = sel.get(key, 0)
        m = folium.Map(location=[11.0, -74.85], zoom_start=10, tiles='CartoDB positron')
        folium.GeoJson(
            geo,
            name='municipios',
            tooltip=folium.features.GeoJsonTooltip(fields=[name_col,'value'], aliases=['Municipio','Valor (ha)']),
            style_function=lambda feat: {
                'fillColor': '#ffffff' if feat['properties'].get('value',0)==0 else '#f28f3b',
                'color':'#444','weight':0.4,'fillOpacity':0.6
            }
        ).add_to(m)
        st_folium(m, width=700, height=500)
    else:
        if os.path.exists(CHOROPLETH_HTML):
            st.info("Mostrando HTML coroplético guardado")
            html = open(CHOROPLETH_HTML,'r',encoding='utf-8').read()
            st.components.v1.html(html, height=600)
        else:
            st.warning("No hay geojson ni HTML de mapa en outputs/. Ejecuta las celdas de export en tu notebook.")
# Footer - files present
st.markdown("---")
st.markdown("Archivos en outputs/:")
files = [f for f in os.listdir(OUT) if f.endswith(('.csv','.geojson','.gpkg','.html','.png'))]
st.write(files)
