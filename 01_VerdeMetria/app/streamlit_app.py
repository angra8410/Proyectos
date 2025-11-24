#!/usr/bin/env python3
"""
Streamlit app para visualizar resultados NDVI (ganancia/pérdida) por municipio.
Coloca este archivo en la raíz del repo (o /app) junto con la carpeta outputs/.
Ejecuta localmente: streamlit run streamlit_app.py
"""
import os
import json
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

# Parámetros / paths relativos (se asume que outputs/ está en el repo)
OUT = os.path.join(os.getcwd(), "outputs")
CSV_AREAS = os.path.join(OUT, "areas_by_sector_vs_2016.csv")
CSV_AREAS_FILTERED = os.path.join(OUT, "areas_by_sector_vs_2016_filtered.csv")
GEOJSON_YEAR = os.path.join(OUT, "areas_by_municipio_2025.geojson")  # ejemplo exportado por año
GEOJSON_CUMULATIVE = os.path.join(OUT, "areas_by_municipio_2025.geojson")  # fallback
TOP10_CSV = os.path.join(OUT, "top10_by_year.csv")
CHOROPLETH_HTML = os.path.join(OUT, "choropleth_cumulative_pct.html")

st.set_page_config(layout="wide", page_title="NDVI Changes Explorer")

st.title("NDVI Changes Explorer — pérdidas/ganancias vs 2016")
st.markdown("Interactivo para explorar resultados por municipio y año. Fuente: outputs/ en el repositorio.")

# Caching loaders
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

# Cargar datos (intenta el filtrado si existe)
df = load_csv(CSV_AREAS_FILTERED) or load_csv(CSV_AREAS)
if df is None:
    st.error(f"No encontré CSV de áreas en outputs/. Ejecuta el notebook y asegúrate de que {CSV_AREAS} exista.")
    st.stop()

# columns cleanup
df.columns = [c.strip() for c in df.columns]
if 'area_ha' not in df.columns and 'area_m2' in df.columns:
    df['area_ha'] = df['area_m2'] / 10000.0

years = sorted(df['year'].astype(int).unique())
kinds = sorted(df['kind'].unique())

# Sidebar controls
st.sidebar.header("Filtros")
year = st.sidebar.selectbox("Año", options=years, index=len(years)-1)
kind = st.sidebar.radio("Tipo", options=kinds, index=0)
topN = st.sidebar.slider("Top N", min_value=3, max_value=50, value=10)
name_col = st.sidebar.text_input("Campo nombre municipio", value="NAME_2")

# Main layout
left_col, right_col = st.columns((1,1))

with left_col:
    st.subheader(f"Top {topN} municipios — {kind} — {year}")
    sub = df[(df['year']==int(year)) & (df['kind']==kind)].copy()
    if sub.empty:
        st.info("No hay datos para la selección.")
    else:
        top = sub.sort_values('area_ha', ascending=False).head(topN)
        st.dataframe(top[[name_col, 'area_ha']].rename(columns={name_col: "Municipio", 'area_ha': 'Área (ha)'}).reset_index(drop=True))
        # Plot horizontal bar using matplotlib
        fig, ax = plt.subplots(figsize=(6, max(3, 0.3*len(top))))
        ax.barh(top[name_col].astype(str), top['area_ha'], color='green' if kind=='gain' else 'red')
        ax.invert_yaxis()
        ax.set_xlabel('Área (ha)')
        ax.set_title(f'Top {topN} {kind} — {year}')
        st.pyplot(fig)

    # Allow CSV download of current top
    csv_bytes = top.to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar Top actual (CSV)", data=csv_bytes, file_name=f"top{topN}_{kind}_{year}.csv", mime='text/csv')

with right_col:
    st.subheader("Mapa interactivo")
    # Try to load geojson cumulative or year-specific. If not present, fallback to choropleth HTML
    geo = load_geojson(GEOJSON_YEAR) or load_geojson(GEOJSON_CUMULATIVE)
    if geo:
        # Merge values from df (selected year/net) into geojson properties if needed
        # Prepare a dict municipality -> value
        val_map = {}
        if 'net_ha' in df.columns:
            # use net_ha if available, else area_ha for selected kind
            pivot = df.pivot_table(index=['NAME_2','year'], columns='kind', values='area_ha', aggfunc='sum').fillna(0).reset_index()
            pivot['net_ha'] = pivot.get('gain',0) - pivot.get('loss',0)
            sel = pivot[pivot['year']==int(year)][['NAME_2','net_ha']].set_index('NAME_2')['net_ha'].to_dict()
            val_map = sel
            legend_name = 'Net (ha)'
        else:
            sel = df[(df['year']==int(year)) & (df['kind']==kind)].set_index(name_col)['area_ha'].to_dict()
            val_map = sel
            legend_name = f'Área (ha) {kind} {year}'
        # attach values into geo features
        for feat in geo.get('features', []):
            props = feat.get('properties', {})
            key = props.get(name_col) or props.get('NAME_2') or props.get('name')
            feat['properties'][ 'value' ] = val_map.get(key, 0)
        # create a folium map
        # compute center from features centroid approximate
        m = folium.Map(location=[11.0, -74.85], zoom_start=10, tiles='CartoDB positron')
        folium.GeoJson(
            geo,
            name='municipios',
            tooltip=folium.features.GeoJsonTooltip(fields=['NAME_2','value'], aliases=['Municipio','Valor (ha)'], localize=True),
            style_function=lambda feat: {
                'fillColor': '#ffffff' if feat['properties'].get('value',0)==0 else
                             plt.cm.RdYlGn(min(1, feat['properties']['value']/1000))[:3], # not used directly
                'color':'#444','weight':0.4,'fillOpacity':0.6
            }
        ).add_to(m)
        # Render with streamlit_folium
        st_data = st_folium(m, width=700, height=500)
    else:
        if os.path.exists(CHOROPLETH_HTML):
            st.info("No GeoJSON encontrada en outputs/. Abriendo el HTML coroplético guardado.")
            html = open(CHOROPLETH_HTML,'r',encoding='utf-8').read()
            st.components.v1.html(html, height=600)
        else:
            st.warning("No hay geojson ni HTML de mapa en outputs/. Ejecuta las celdas de export en tu notebook primero.")

# Footer: quick stats and links
st.markdown("---")
st.markdown("Archivos de datos usados (desde outputs/):")
files = [f for f in os.listdir(OUT) if f.endswith(('.csv','.geojson','.gpkg','.html','.png'))]
st.write(files)

st.markdown("Instrucciones: si modificas los datos en notebook, vuelve a exportar los geojson/gpkg y haz push al repo para que la app en Streamlit Cloud se actualice.")
