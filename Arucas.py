import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import os
import glob
import urllib.request
import urllib.parse
import base64
import matplotlib.pyplot as plt
from math import pi
import gc
from PIL import Image
import re
import csv
from datetime import date
import json

# --- 0. SISTEMA DE LOGIN Y CONFIGURACIÓN ---
st.set_page_config(page_title="Scouting Dani FC | Dani Rodríguez", layout="wide")

CORREOS_AUTORIZADOS = ["danielrr.3998@gmail.com", "dd@danifc.com", "prueba@danifc.com"]

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Acceso Scouting Dani FC")
        st.write("Bienvenido a la plataforma de análisis de Dani FC. Por favor, identifícate.")
        correo_input = st.text_input("Correo electrónico:")
        if st.button("Entrar"):
            if correo_input.lower().strip() in CORREOS_AUTORIZADOS:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Acceso denegado. Correo no autorizado.")
    st.stop() 

# --- 1. ESTILO MODERNO (TEMA DANI FC - AZUL Y AMARILLO) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; color: #1e293b; } 
    h1, h2, h3 { color: #1e3a8a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; } 
    
    .player-card { 
        border: 1px solid #fde047; padding: 30px; border-radius: 12px; 
        background-color: #ffffff; box-shadow: 0 10px 15px -3px rgba(30, 58, 138, 0.1);
        margin-bottom: 20px;
        border-top: 5px solid #eab308; 
    }
    .card-header { display: flex; align-items: center; gap: 25px; margin-bottom: 15px; border-bottom: 1px solid #fef08a; padding-bottom: 20px; }
    .header-photos { display: flex; align-items: center; gap: 20px; }
    .header-title-area h2 { margin: 0; font-size: 2.2rem; }
    .header-title-area p { margin: 5px 0 0 0; color: #1e40af; font-size: 1.1rem;}
    
    .profile-face { border-radius: 50%; border: 4px solid #fde047; box-shadow: 0 4px 6px rgba(0,0,0,0.1); object-fit: cover; height: 110px; width: 110px; }
    .team-logo { height: 80px; width: 80px; object-fit: contain; }
    .debug-text-card { font-size: 0.75rem; color: #ef4444; font-weight: bold; margin: 2px 0; text-align:center;}
    
    .stDataFrame { border: 1px solid #fde047; border-radius: 8px; overflow: hidden; }
    hr { border-color: #fef08a; margin: 15px 0; }
    
    .stButton > button { background-color: #1e3a8a; color: #fde047; border: 1px solid #eab308; border-radius: 6px; font-weight: bold; }
    .stButton > button:hover { background-color: #1e40af; color: #ffffff; }
    div[data-testid="stRadio"] > div { flex-direction: row; align-items: center; justify-content: flex-end; }
    
    /* Estilos ranking Once Ideal */
    .ranking-box { background-color: white; border: 1px solid #fde047; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .ranking-title { color: #1e3a8a; border-bottom: 2px solid #eab308; padding-bottom: 5px; margin-bottom: 10px; font-weight: bold; font-size: 1.2rem; }
    .ranking-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #f8fafc; }
    .ranking-item:last-child { border-bottom: none; }
    .ranking-score { font-weight: bold; color: #1e3a8a; background-color: #fef08a; padding: 2px 8px; border-radius: 12px; font-size: 0.9rem;}
    .ranking-avatar { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 1px solid #1e3a8a; margin-right: 8px; vertical-align: middle; }
    </style>
    """, unsafe_allow_html=True)

def cambiar_jugador(nombre):
    st.session_state.selector_ficha = nombre

if 'selector_ficha' not in st.session_state:
    st.session_state.selector_ficha = ""

# --- CABECERA COMÚN ---
URL_LOGO = "danifc.png" 

col_logo, col_titulo, col_modo = st.columns([1, 4, 3])
with col_logo: 
    if os.path.exists(URL_LOGO): st.image(URL_LOGO, width=120)
with col_titulo: 
    st.title("Dani FC | Scouting Lab")
with col_modo:
    st.write("")
    st.write("")
    modo_seleccionado = st.radio("Modo de análisis:", ["👁️ Normal", "🙈 Ciego"], horizontal=True, label_visibility="collapsed")
    blind_mode = (modo_seleccionado == "🙈 Ciego")

st.markdown("---")

# ==========================================================
# MENÚ PRINCIPAL LATERAL
# ==========================================================
if os.path.exists(URL_LOGO):
    st.sidebar.image(URL_LOGO, width=150)
    
st.sidebar.title("Navegación General")
modulo_seleccionado = st.sidebar.radio("Área de trabajo:", 
                                       ["🌐 Módulo Big Data (Wyscout)", 
                                        "📋 Módulo Scouting de Campo"])
st.sidebar.markdown("---")


# =========================================================================================
# ======================== MÓDULO 1: BIG DATA (WYSCOUT) ===================================
# =========================================================================================
if modulo_seleccionado == "🌐 Módulo Big Data (Wyscout)":
    
    CARPETAS_CARAS = ["jugadores_2RFEF_Grupo_1", "jugadores_2RFEF_Grupo_2", "jugadores_2RFEF_Grupo_3", "jugadores_2RFEF_Grupo_4", "jugadores_2RFEF_Grupo_5"]
    CARPETAS_ESCUDOS = ["escudos_2RFEF_Grupo_1", "escudos_2RFEF_Grupo_2", "escudos_2RFEF_Grupo_3", "escudos_2RFEF_Grupo_4", "escudos_2RFEF_Grupo_5"]

    def limpiar_texto(texto):
        if pd.isna(texto): return ""
        sustituciones = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', 'ü': 'u', "'": "", ".": "", "_": " "}
        res = str(texto).lower().strip()
        for orig, dest in sustituciones.items(): res = res.replace(orig, dest)
        return res

    @st.cache_data
    def escanear_archivos(carpetas, extensiones=(".jpg", ".jpeg", ".png")):
        archivos_disponibles = {}
        for carpeta in carpetas:
            if os.path.exists(carpeta):
                for root, dirs, files in os.walk(carpeta):
                    for archivo in files:
                        if archivo.lower().endswith(extensiones):
                            nombre_sin_ext = os.path.splitext(archivo)[0]
                            clave_limpia = limpiar_texto(nombre_sin_ext)
                            archivos_disponibles[clave_limpia] = os.path.join(root, archivo)
        return archivos_disponibles

    @st.cache_data
    def buscar_mejor_coincidencia(nombre_buscado, diccionario_archivos):
        if not nombre_buscado: return None
        buscado_limpio = limpiar_texto(nombre_buscado)
        buscado_tokens = set(buscado_limpio.split())
        if buscado_limpio in diccionario_archivos: return diccionario_archivos[buscado_limpio]
        buscado_junto = buscado_limpio.replace(" ", "")
        for nombre_archivo, ruta in diccionario_archivos.items():
            archivo_junto = nombre_archivo.replace(" ", "")
            if len(archivo_junto) >= 4 and archivo_junto in buscado_junto: return ruta
            if len(buscado_junto) >= 4 and buscado_junto in archivo_junto: return ruta
        palabras_prohibidas = {"real", "fc", "cd", "sd", "ud", "cf", "de", "la", "el", "los", "las", "club", "atletico", "racing", "deportivo"}
        buscado_tokens_utiles = buscado_tokens - palabras_prohibidas
        for nombre_archivo, ruta in diccionario_archivos.items():
            archivo_tokens = set(nombre_archivo.split())
            palabras_comunes = [t for t in buscado_tokens_utiles.intersection(archivo_tokens) if len(t) >= 4]
            if palabras_comunes: return ruta
        return None

    def convertir_imagen_base64(ruta_imagen, default_url, mime_type="image/jpeg"):
        if ruta_imagen and os.path.exists(ruta_imagen):
            with open(ruta_imagen, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode()
            return f"data:{mime_type};base64,{encoded_string}", True
        return default_url, False

    ARCHIVOS_CARAS = escanear_archivos(CARPETAS_CARAS, (".jpg", ".jpeg", ".png"))
    ARCHIVOS_ESCUDOS = escanear_archivos(CARPETAS_ESCUDOS, (".png", ".jpg", ".jpeg"))

    @st.cache_data
    def load_data():
        rutas_posibles = ["datos/*.xlsx", "*.xlsx"]
        archivos = []
        for r in rutas_posibles: archivos.extend(glob.glob(r))
        if not archivos: return pd.DataFrame()
        dfs = []
        for f in archivos:
            try:
                temp = pd.read_excel(f)
                if not any(col in temp.columns for col in ['Player', 'Jugador', 'Nombre']):
                    temp = pd.read_excel(f, header=1)
                temp.columns = temp.columns.astype(str).str.strip()
                for p in ['Position', 'Posición', 'Puesto', 'Pos', 'Role', 'Posición específica']:
                    if p in temp.columns: temp = temp.rename(columns={p: 'Position'}); break
                for c in temp.columns:
                    cl = c.lower()
                    if cl in ['player', 'jugador', 'nombre', 'player name']: temp = temp.rename(columns={c: 'Player'})
                    elif cl in ['team', 'equipo', 'current team']: temp = temp.rename(columns={c: 'Team'})
                    elif cl in ['age', 'edad']: temp = temp.rename(columns={c: 'Age'})
                    elif cl in ['foot', 'pie', 'lateralidad']: temp = temp.rename(columns={c: 'Foot'})
                    elif 'contrat' in cl or 'contract' in cl or 'vencimiento' in cl: temp = temp.rename(columns={c: 'Contract expires'})
                    elif 'minut' in cl: temp = temp.rename(columns={c: 'Minutes played'})
                    elif cl in ['goals', 'goles']: temp = temp.rename(columns={c: 'Goals'})
                    elif cl in ['assists', 'asistencias']: temp = temp.rename(columns={c: 'Assists'})
                    elif cl in ['matches played', 'partidos jugados', 'partidos']: temp = temp.rename(columns={c: 'Matches played'})
                    elif cl in ['market value', 'valor de mercado', 'market value (in eur)', 'valor de mercado (€)']: temp = temp.rename(columns={c: 'Valor de mercado'})
                
                fn = f.lower() 
                if "2 rfef" in fn or "segunda rfef" in fn or "segunda federacion" in fn: 
                    temp['Categoria'] = "Segunda Federación"; temp['Pais'] = "España"
                else: 
                    temp['Categoria'] = "Otros"; temp['Pais'] = "Otros"
                dfs.append(temp)
            except: continue
            
        if not dfs: return pd.DataFrame()
        df = pd.concat(dfs, ignore_index=True)
        df = df[df['Categoria'] == "Segunda Federación"]
        
        for c in ['Team', 'Player', 'Age', 'Position', 'Matches played', 'Minutes played', 'Goals', 'Assists', 'Foot', 'Contract expires', 'Valor de mercado']:
            if c not in df.columns: df[c] = np.nan
            
        df['Team'] = df['Team'].replace(['none', 'None', 0, '0'], np.nan)
        df.loc[df['Team'].isna(), 'Categoria'] = "Libre"
        df = df.dropna(subset=['Player'])

        if df['Valor de mercado'].dtype == object: df['Valor de mercado'] = df['Valor de mercado'].astype(str).str.replace('€', '').str.replace(',', '').str.replace('.', '').str.extract(r'(\d+)').astype(float)
        df['Valor de mercado'] = pd.to_numeric(df['Valor de mercado'], errors='coerce').fillna(0)

        def map_foot(val):
            if pd.isna(val): return 'Desconocido'
            v = str(val).lower()
            if 'right' in v or 'diestro' in v or 'derech' in v: return 'Diestro'
            if 'left' in v or 'zurdo' in v or 'izquierd' in v: return 'Zurdo'
            if 'both' in v or 'ambi' in v: return 'Ambidiestro'
            return 'Desconocido'
        df['Foot'] = df['Foot'].apply(map_foot)

        def map_pos(val):
            if pd.isna(val): return 'Desconocido'
            p = str(val).upper().replace(' ', '')
            if any(x in p for x in ['GK', 'PORTERO']): return 'Portero'
            if any(x in p for x in ['CB', 'CENTRAL', 'DEFENSA']): return 'Central'
            if any(x in p for x in ['WB', 'RB', 'LB', 'LATERAL']): return 'Lateral'
            if any(x in p for x in ['WF', 'WING', 'LW', 'RAMF', 'RW', 'EXTREMO']): return 'Extremo'
            if any(x in p for x in ['CF', 'SS', 'DELANTERO', 'ATTACK']): return 'Delantero'
            if any(x in p for x in ['MF', 'DM', 'CM', 'AM', 'PIVOTE', 'MEDIO']): return 'Mediocentro'
            return 'Desconocido'

        df['Posicion_Scouting'] = df['Position'].apply(map_pos)

        diccionario_metricas = {
            'Porterías a cero': ['porterías a cero', 'clean sheets', 'imbatidas'],
            'Paradas %': ['paradas, %', 'paradas %', 'saves, %', 'paradas'],
            'xG en contra': ['xg en contra', 'xg conceded'],
            'Goles evitados': ['goles evitados', 'prevented'],
            'Duelos aéreos ganados %': ['duelos aéreos ganados, %', 'duelos aereos ganados, %', 'aerial duels won, %', 'duelos aéreos, %', 'duelos aéreos ganados'],
            'Duelos defensivos %': ['duelos defensivos ganados, %', 'defensive duels won, %', 'duelos defensivos, %', 'duelos defensivos ganados'],
            'Pases hacia adelante %': ['pases hacia adelante precisos, %', 'pases hacia adelante, %', 'forward passes accurate, %', 'pases hacia adelante precisos'],
            'Interceptaciones': ['intercepciones/90', 'interceptaciones/90', 'interceptions/90', 'intercepciones', 'interceptaciones'],
            'Entradas': ['entradas/90', 'tackles/90', 'entradas'],
            'Faltas': ['faltas/90', 'fouls/90', 'faltas'],
            'Centros %': ['centros precisos, %', 'centros, %', 'crosses accurate, %', 'centros precisos'],
            'Carreras progresivas': ['carreras en progresión/90', 'carreras progresivas/90', 'progressive runs/90', 'carreras progresivas', 'conducciones progresivas/90', 'conducciones progresivas'],
            'Pases precisos %': ['pases precisos, %', 'pases con éxito, %', 'pases completados, %', 'pases, %', 'accurate passes, %', 'pases precisos', 'pases con éxito', 'pases completados'],
            'Recuperaciones': ['posesión conquistada después de una interceptación', 'recuperaciones/90', 'recoveries/90', 'recuperaciones'],
            'Precisión pases en el último tercio %': ['precisión pases en el último tercio, %', 'precision pases en el ultimo tercio', 'pases clave/90', 'key passes/90', 'pases clave'],
            'Regates %': ['regates realizados, %', 'regates con éxito, %', 'regates ganados, %', 'regates, %', 'dribbles successful, %', 'regates con éxito', 'regates ganados'],
            'xA': ['xa/90', 'xa'],
            'xG': ['xg/90', 'xg'], 
            'Tiros a puerta %': ['tiros a la portería, %', 'tiros a porteria, %', 'tiros a portería, %', 'tiros a puerta, %', 'shots on target, %', 'tiros a portería', 'tiros a puerta'],
            'Toques en área': ['toques en el área de castigo/90', 'toques en el área/90', 'touches in box/90', 'toques en el área de castigo', 'toques en el área', 'toques en área']
        }
        for nombre_final, palabras_clave in diccionario_metricas.items():
            if nombre_final not in df.columns:
                for col in list(df.columns):
                    col_lower = col.lower().strip()
                    if any(k in col_lower for k in palabras_clave):
                        df = df.rename(columns={col: nombre_final})
                        break
            if nombre_final not in df.columns: df[nombre_final] = 0.0 
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='ignore')
        for c in ['Age', 'Matches played', 'Minutes played', 'Goals', 'Assists']: 
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)

        def es_seleccion(equipo):
            if pd.isna(equipo): return False
            eq = str(equipo).strip().upper()
            paises = ["SPAIN", "ESPAÑA"] 
            if eq in paises: return True
            if re.search(r'\bU\d{2}\b', eq): return True  
            if re.search(r'\bSUB-\d{2}\b', eq): return True 
            if re.search(r'\bSUB \d{2}\b', eq): return True 
            return False

        df = df[~df['Team'].apply(es_seleccion)]
        col_fecha = next((c for c in df.columns if 'último partido' in str(c).lower() or 'ultimo partido' in str(c).lower() or 'last match' in str(c).lower() or 'date' == str(c).lower()), None)
        if col_fecha:
            df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
            df = df.sort_values(by=[col_fecha, 'Minutes played'], ascending=[False, False])
        else:
            df = df.sort_values(by='Minutes played', ascending=False)
            
        df = df.drop_duplicates(subset=['Player'], keep='first')
        return df

    df = load_data()
    if df.empty:
        st.error("🚨 No se encontraron datos. Asegúrate de que los Excel están en la carpeta correspondiente y se refieren a Segunda RFEF.")
        st.stop()

    if 'blind_mapping' not in st.session_state or len(st.session_state.blind_mapping) != len(df['Player'].unique()):
        st.session_state.blind_mapping = {p: f"Perfil Oculto {i+1}" for i, p in enumerate(df['Player'].unique())}
        st.session_state.team_mapping = {t: f"Club Oculto {i+1}" for i, t in enumerate(df['Team'].dropna().unique())}

    def get_name(real_name): return st.session_state.blind_mapping.get(real_name, real_name) if blind_mode else real_name
    def get_team(real_team):
        if pd.isna(real_team) or str(real_team).lower() == 'none': return 'AGENTE LIBRE'
        return st.session_state.team_mapping.get(real_team, real_team) if blind_mode else real_team

    metrics_dict = {
        'Portero': ['Porterías a cero', 'Paradas %', 'xG en contra', 'Goles evitados', 'Duelos aéreos ganados %'],
        'Central': ['Duelos defensivos %', 'Duelos aéreos ganados %', 'Pases hacia adelante %', 'Interceptaciones', 'Entradas'],
        'Lateral': ['Centros %', 'Carreras progresivas', 'Duelos defensivos %', 'Interceptaciones', 'Pases precisos %'],
        'Mediocentro': ['Pases precisos %', 'Precisión pases en el último tercio %', 'Regates %', 'Recuperaciones', 'Interceptaciones'],
        'Extremo': ['Regates %', 'Centros %', 'xA', 'Carreras progresivas', 'Toques en área'],
        'Delantero': ['Goals', 'xG', 'Tiros a puerta %', 'Toques en área', 'Duelos aéreos ganados %']
    }

    st.sidebar.markdown("### Filtros Wyscout")
    f_cat = st.sidebar.multiselect("Categoría", ["Segunda Federación"], default=["Segunda Federación"])
    f_team_opciones = sorted(df['Team'].dropna().unique())
    f_team = st.sidebar.multiselect("Equipo", f_team_opciones, format_func=lambda x: get_team(x))
    orden_posiciones = ["Portero", "Central", "Lateral", "Mediocentro", "Extremo", "Delantero"]
    pos_disponibles = [p for p in orden_posiciones if p in df['Posicion_Scouting'].unique()]
    if 'Desconocido' in df['Posicion_Scouting'].unique(): pos_disponibles.append('Desconocido')
    f_pos = st.sidebar.multiselect("Posición", pos_disponibles, default=pos_disponibles)
    min_age_val = int(df['Age'].min()) if not df.empty else 0
    max_age_val = int(df['Age'].max()) if not df.empty and int(df['Age'].max()) > 0 else 40
    f_age = st.sidebar.slider("Rango de edad", min_age_val, max_age_val, (min_age_val, max_age_val))
    max_vm = int(df['Valor de mercado'].max()) if 'Valor de mercado' in df.columns and int(df['Valor de mercado'].max()) > 0 else 50000000
    f_vm = st.sidebar.slider("Valor Transfermarkt (€)", 0, max_vm, (0, max_vm), step=100000, format="%d")
    max_min = int(df['Minutes played'].max()) if not df.empty and int(df['Minutes played'].max()) > 0 else 5000
    f_min = st.sidebar.slider("Minutos jugados", 0, max_min, (0, max_min))
    lat_ordenadas = ["Zurdo", "Diestro", "Ambidiestro", "Desconocido"]
    f_foot = st.sidebar.multiselect("Lateralidad", lat_ordenadas, default=lat_ordenadas)
    f_contrato = st.sidebar.multiselect("Vencimiento contrato", sorted(df['Contract expires'].dropna().astype(str).unique()))

    df_filt = df[
        (df['Categoria'].isin(f_cat)) & 
        (df['Posicion_Scouting'].isin(f_pos)) & 
        (df['Age'].between(f_age[0], f_age[1])) & (df['Minutes played'].between(f_min[0], f_min[1])) &
        (df['Valor de mercado'].between(f_vm[0], f_vm[1])) &
        (df['Foot'].isin(f_foot))
    ].copy()
    if f_team: df_filt = df_filt[df_filt['Team'].isin(f_team)]
    if f_contrato: df_filt = df_filt[df_filt['Contract expires'].astype(str).isin(f_contrato)]

    def find_similar(p_row, df_t):
        if df_t.empty: return "Ninguno"
        f = ['Age', 'Minutes played']
        for col in f: df_t[col] = df_t[col].fillna(0)
        scaler = StandardScaler()
        t_sc = scaler.fit_transform(df_t[f].values)
        p_sc = scaler.transform(p_row[f].fillna(0).values.reshape(1, -1))
        nn = NearestNeighbors(n_neighbors=1).fit(t_sc)
        return df_t.iloc[nn.kneighbors(p_sc)[1][0][0]]['Player']

    class DarkScoutingPDF(FPDF):
        def header(self):
            self.set_fill_color(30, 58, 138) 
            self.rect(0, 0, 210, 297, 'F')
            self.set_y(15)
            self.set_font('Arial', 'B', 14)
            self.set_text_color(253, 224, 71) 
            self.cell(0, 10, 'INFORME DE SCOUTING DANI FC', 0, 1, 'C')
            self.set_draw_color(234, 179, 8)
            self.line(20, 25, 190, 25)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(254, 240, 138)
            self.cell(0, 10, f'Informe - Dani FC - Página {self.page_no()} | Creado por Dani Rodríguez', 0, 0, 'L')
            try:
                if os.path.exists(URL_LOGO): self.image(URL_LOGO, x=185, y=280, w=15)
            except: pass

    def create_radar_matplotlib(labels, vals_1, vals_2, color1, color2, filename, legend1='Jugador', legend2='Media Liga'):
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(5, 5), facecolor='#1e3a8a') 
        ax = fig.add_subplot(111, polar=True, facecolor='#1e3a8a')
        N = len(labels)
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]
        v1 = vals_1 + vals_1[:1]
        v2 = vals_2 + vals_2[:1]
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)
        plt.xticks(angles[:-1], labels, color='#fde047', size=9, weight='bold')
        ax.set_yticklabels([])
        ax.spines['polar'].set_color('#eab308')
        ax.grid(color='#eab308', linestyle='--')
        ax.plot(angles, v2, linewidth=1.5, linestyle='--', color=color2, label=legend2)
        ax.fill(angles, v2, color2, alpha=0.2)
        ax.plot(angles, v1, linewidth=2, linestyle='solid', color=color1, label=legend1)
        ax.fill(angles, v1, color1, alpha=0.4)
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1), facecolor='#1e40af', edgecolor='#eab308', labelcolor='white')
        fig.savefig(filename, facecolor=fig.get_facecolor(), bbox_inches='tight', transparent=True, dpi=200)
        fig.clf(); plt.close('all'); gc.collect()

    def create_scatter_matplotlib(df_data, p_name, x_col, y_col, filename):
        plt.style.use('dark_background')
        fig_sc = plt.figure(figsize=(8, 5.5), facecolor='#1e3a8a') 
        ax_sc = fig_sc.add_subplot(111, facecolor='#1e3a8a')
        x_o = df_data[df_data['Player'] != p_name][x_col]
        y_o = df_data[df_data['Player'] != p_name][y_col]
        x_p = df_data.loc[df_data['Player'] == p_name, x_col].values[0]
        y_p = df_data.loc[df_data['Player'] == p_name, y_col].values[0]
        ax_sc.scatter(x_o, y_o, color='#fef08a', alpha=0.5, label='Rivales (>800\')')
        ax_sc.scatter(x_p, y_p, color='#eab308', s=180, edgecolor='white', label=p_name, zorder=5) 
        for idx, row in df_data.iterrows():
            if row['Player'] != p_name:
                ax_sc.text(row[x_col], row[y_col], str(row['Player'])[:10], fontsize=7, color='#fef08a', alpha=0.8, va='bottom', ha='center')
        ax_sc.set_xlabel(x_col.encode('latin-1', 'ignore').decode('latin-1'), color='#fde047', weight='bold')
        ax_sc.set_ylabel(y_col.encode('latin-1', 'ignore').decode('latin-1'), color='#fde047', weight='bold')
        ax_sc.tick_params(colors='#fef08a')
        ax_sc.spines['bottom'].set_color('#eab308')
        ax_sc.spines['left'].set_color('#eab308')
        ax_sc.spines['top'].set_visible(False)
        ax_sc.spines['right'].set_visible(False)
        ax_sc.legend(facecolor='#1e40af', edgecolor='#eab308', labelcolor='white')
        fig_sc.savefig(filename, facecolor=fig_sc.get_facecolor(), bbox_inches='tight', dpi=200)
        fig_sc.clf(); plt.close('all'); gc.collect()

    tab_ficha, tab_comp, tab_intel, tab_tabla = st.tabs([
        "📋 Ficha y Vídeo", "⚖️ Comparador", "📊 Inteligencia de Mercado", "🗃️ Base de Datos Big Data"
    ])

    with tab_ficha:
        st.header("🔍 Ficha de Jugador y Generador PDF (Big Data)")
        opciones_perfil = [""] + sorted(df_filt['Player'].dropna().unique().tolist())
        if st.session_state.selector_ficha not in opciones_perfil: st.session_state.selector_ficha = ""
        jugador_sel = st.selectbox("Buscar perfil en base de datos:", opciones_perfil, key='selector_ficha', format_func=lambda x: get_name(x) if x != "" else "")

        if jugador_sel:
            p = df_filt[df_filt['Player'] == jugador_sel].iloc[0]
            display_name = get_name(p['Player'])
            display_team = get_team(p['Team'])
            
            df_sup = df[(df['Posicion_Scouting'] == p['Posicion_Scouting']) & (df['Categoria'] == 'Segunda Federación')] 
            df_inf = df[(df['Posicion_Scouting'] == p['Posicion_Scouting']) & (df['Categoria'] == 'Libre')]
            
            if blind_mode:
                url_jugador = "https://ui-avatars.com/api/?name=PO&background=1e3a8a&color=fff&size=128&bold=true"
                url_escudo = "https://ui-avatars.com/api/?name=CO&background=transparent&color=1e3a8a&size=128&bold=true"
                cara_ok, escudo_ok = True, True
                ruta_cara_encontrada, ruta_escudo_encontrada = None, None
            else:
                nombre_limpio_url = urllib.parse.quote(p['Player'])
                url_jugador_fallback = f"https://ui-avatars.com/api/?name={nombre_limpio_url}&background=1e3a8a&color=fff&size=128&bold=true"
                ruta_cara_encontrada = buscar_mejor_coincidencia(p['Player'], ARCHIVOS_CARAS)
                url_jugador, cara_ok = convertir_imagen_base64(ruta_cara_encontrada, url_jugador_fallback, "image/jpeg")
                
                equipo_limpio_url = urllib.parse.quote(str(display_team))
                url_escudo_fallback = f"https://ui-avatars.com/api/?name={equipo_limpio_url}&background=transparent&color=1e3a8a&size=128&bold=true"
                ruta_escudo_encontrada = buscar_mejor_coincidencia(str(p['Team']), ARCHIVOS_ESCUDOS) if str(p['Team']).lower() != 'none' else None
                url_escudo, escudo_ok = convertir_imagen_base64(ruta_escudo_encontrada, url_escudo_fallback, "image/png")
            
            val_mercado = p.get('Valor de mercado', 0)
            txt_mercado = f"{int(val_mercado):,} €".replace(',', '.') if val_mercado > 0 else "N/D"
            contrato_print = p.get('Contract expires', 'N/D') if pd.notna(p.get('Contract expires')) and str(p.get('Contract expires')).lower() != 'none' else 'N/D'

            colA, colB = st.columns([2, 1.1])
            with colA:
                txt_debug_cara = f'<p class="debug-text-card">No hay .jpg</p>' if not cara_ok else ''
                txt_debug_escudo = f'<p class="debug-text-card">No hay escudo</p>' if not escudo_ok and str(p['Team']).lower() != 'none' else ''
                
                sim_sup_name = get_name(find_similar(p, df_sup))
                sim_inf_name = get_name(find_similar(p, df_inf))

                st.markdown(f"""
                <div class="player-card">
                    <div class="card-header">
                        <div class="header-photos">
                            <div><img src="{url_jugador}" class="profile-face">{txt_debug_cara}</div>
                            <div><img src="{url_escudo}" class="team-logo">{txt_debug_escudo}</div>
                        </div>
                        <div class="header-title-area">
                            <h2>{display_name}</h2>
                            <p><b>{display_team}</b> | {p['Categoria']} ({p['Pais']})</p>
                        </div>
                    </div>
                    <div style="font-size: 1.1rem; padding-top: 5px;">
                        <p><b>Posición:</b> {p['Posicion_Scouting']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Edad:</b> {p['Age']} años</p>
                        <p><b>Lateralidad:</b> {p['Foot']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Vencimiento:</b> {contrato_print} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Valor Transfermarkt:</b> {txt_mercado}</p>
                        <hr>
                        <p><b>Minutos jugados:</b> {p['Minutes played']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Goles:</b> {p['Goals']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Asistencias:</b> {p['Assists']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if not blind_mode:
                    st.markdown("### 🎥 Central de Vídeo Automatizada")
                    yt_query = f"{p['Player']} {str(p['Team']).replace('none','')} highlights skills"
                    youtube_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_query)}"
                    wyscout_url = "https://platform.wyscout.com/"
                    c_vid1, c_vid2 = st.columns(2)
                    with c_vid1: st.link_button("▶️ Buscar clips en YouTube", youtube_url, use_container_width=True)
                    with c_vid2: st.link_button("🔍 Abrir plataforma Wyscout", wyscout_url, use_container_width=True)
                else:
                    st.info("🙈 La central de vídeo está desactivada en el modo scouting ciego.")

                stats_clave = metrics_dict.get(p['Posicion_Scouting'], [])
                df_contexto = df[(df['Categoria'] == p['Categoria']) & (df['Posicion_Scouting'] == p['Posicion_Scouting']) & (df['Minutes played'] >= 800)].copy()
                if p.name not in df_contexto.index: df_contexto = pd.concat([df_contexto, df.loc[[p.name]]])
                df_contexto_display = df_contexto.copy()
                if blind_mode:
                    df_contexto_display['Player'] = df_contexto_display['Player'].apply(get_name)
                    df_contexto_display['Team'] = df_contexto_display['Team'].apply(get_team)

                with st.spinner("Generando análisis de big data..."):
                    temp_face, temp_escudo = "temp_face.png", "temp_escudo.png"
                    if not blind_mode:
                        if ruta_cara_encontrada: temp_face = f"temp_face{os.path.splitext(ruta_cara_encontrada)[1].lower()}"
                        if ruta_escudo_encontrada: temp_escudo = f"temp_escudo{os.path.splitext(ruta_escudo_encontrada)[1].lower()}"
                        
                    try:
                        if not blind_mode and ruta_cara_encontrada and os.path.exists(ruta_cara_encontrada): 
                            with open(ruta_cara_encontrada, 'rb') as f_in:
                                with open(temp_face, 'wb') as f_out: f_out.write(f_in.read())
                        else: 
                            url_f = url_jugador_fallback if not blind_mode else url_jugador
                            req = urllib.request.Request(url_f, headers={'User-Agent': 'Mozilla/5.0'})
                            with open(temp_face, 'wb') as f: f.write(urllib.request.urlopen(req).read())
                    except Exception: pass
                    
                    try:
                        if not blind_mode and ruta_escudo_encontrada and os.path.exists(ruta_escudo_encontrada): 
                            with open(ruta_escudo_encontrada, 'rb') as f_in:
                                with open(temp_escudo, 'wb') as f_out: f_out.write(f_in.read())
                        else: 
                            url_e = url_escudo_fallback if not blind_mode else url_escudo
                            req = urllib.request.Request(url_e, headers={'User-Agent': 'Mozilla/5.0'})
                            with open(temp_escudo, 'wb') as f: f.write(urllib.request.urlopen(req).read())
                    except Exception: pass

                    theta_labels, vals_jug, vals_med = [], [], []
                    dict_max, dict_mean, dict_min = {}, {}, {}
                    pct_list_for_dafo = []
                    
                    for s in stats_clave:
                        if s in df.columns:
                            df_contexto[s] = pd.to_numeric(df_contexto[s], errors='coerce').fillna(0.0)
                            mean_val, min_val, max_val = df_contexto[s].mean(), df_contexto[s].min(), df_contexto[s].max()
                            if max_val == min_val: max_val = min_val + 1
                            dict_max[s], dict_min[s], dict_mean[s] = max_val, min_val, mean_val
                            v_p = float(p.get(s, 0.0))
                            vals_jug.append(max(0, min(100, ((v_p - min_val)/(max_val - min_val))*100)))
                            vals_med.append(max(0, min(100, ((mean_val - min_val)/(max_val - min_val))*100)))
                            theta_labels.append(s.encode('latin-1', 'ignore').decode('latin-1')[:15])
                            pct_val = df_contexto[s].rank(pct=True).loc[p.name] * 100
                            pct_list_for_dafo.append((s, pct_val))

                    temp_radar = "temp_radar.png"
                    if theta_labels: create_radar_matplotlib(theta_labels, vals_jug, vals_med, '#eab308', '#fef08a', temp_radar)

                    pct_list_for_dafo.sort(key=lambda x: x[1], reverse=True)
                    txt_fortaleza = txt_oportunidad = txt_debilidad = txt_amenaza = "No hay datos suficientes."
                    if len(pct_list_for_dafo) >= 2:
                        txt_fortaleza = f"Destaca en: {pct_list_for_dafo[0][0]} (percentil {int(pct_list_for_dafo[0][1])}). Rendimiento de élite en esta métrica clave comparado con el resto de la liga."
                        txt_debilidad = f"Debe mejorar en: {pct_list_for_dafo[-1][0]} (percentil {int(pct_list_for_dafo[-1][1])}). Es su punto táctico más débil respecto al promedio de la competición."
                        txt_oportunidad = f"Potencial: Muestra números altísimos en {pct_list_for_dafo[1][0]} (percentil {int(pct_list_for_dafo[1][1])}). "
                        if p['Age'] <= 23: txt_oportunidad += "Su juventud le otorga un techo de progresión altísimo en sistemas ofensivos."
                        else: txt_oportunidad += "Gran fiabilidad como jugador de rendimiento inmediato para un sistema adaptado a estas virtudes."
                        txt_amenaza = "Adaptación táctica: Riesgo de caída de rendimiento si el contexto del nuevo equipo le exige exponerse constantemente en sus métricas más débiles."

                    scatter_configs = {
                        'Portero': [('Paradas %', 'Goles evitados'), ('Porterías a cero', 'xG en contra'), ('Paradas %', 'Minutes played'), ('xG en contra', 'Goles evitados'), ('Pases precisos %', 'Duelos aéreos ganados %')],
                        'Central': [('Duelos defensivos %', 'Duelos aéreos ganados %'), ('Pases hacia adelante %', 'Interceptaciones'), ('Entradas', 'Duelos defensivos %'), ('Pases precisos %', 'Carreras progresivas'), ('Recuperaciones', 'Duelos aéreos ganados %')],
                        'Lateral': [('Centros %', 'Carreras progresivas'), ('Duelos defensivos %', 'Interceptaciones'), ('Pases precisos %', 'Centros %'), ('Duelos defensivos %', 'Recuperaciones'), ('xA', 'Pases hacia adelante %')],
                        'Mediocentro': [('Pases precisos %', 'Precisión pases en el último tercio %'), ('Regates %', 'Pases precisos %'), ('Duelos defensivos %', 'Entradas'), ('xA', 'Carreras progresivas')],
                        'Extremo': [('Regates %', 'Toques en área'), ('Centros %', 'xA'), ('Carreras progresivas', 'Regates %'), ('xG', 'Tiros a puerta %'), ('Pases precisos %', 'Toques en área')],
                        'Delantero': [('Goals', 'xG'), ('Tiros a puerta %', 'Toques en área'), ('xG', 'Duelos aéreos ganados %'), ('Regates %', 'Carreras progresivas'), ('xA', 'Pases precisos %')]
                    }
                    scatters_to_plot = scatter_configs.get(p['Posicion_Scouting'], [('Minutes played', 'Age'), ('Goals', 'Assists'), ('Age', 'Minutes played'), ('Matches played', 'Goals'), ('Minutes played', 'Goals')])
                    temp_scatters = []
                    for idx, (m_x, m_y) in enumerate(scatters_to_plot):
                        if m_x in df_contexto_display.columns and m_y in df_contexto_display.columns:
                            f_name = f"temp_scatter_{idx}.png"
                            create_scatter_matplotlib(df_contexto_display, display_name, m_x, m_y, f_name)
                            temp_scatters.append(f_name)

                    pct_cols = []
                    for s in stats_clave:
                        if s in df.columns:
                            df_contexto[s+'_pct'] = df_contexto[s].rank(pct=True)
                            pct_cols.append(s+'_pct')

                    df_comp_all = df_contexto.copy()
                    if len(pct_cols) > 0: df_comp_all['score_g'] = df_comp_all[pct_cols].mean(axis=1)
                    else: df_comp_all['score_g'] = df_comp_all['Minutes played']
                    
                    df_comp_all = df_comp_all.sort_values('score_g', ascending=False).reset_index(drop=True)
                    target_idx = df_comp_all[df_comp_all['Player'] == p['Player']].index[0]
                    start_idx = max(0, target_idx - 4)
                    end_idx = min(len(df_comp_all), target_idx + 5)
                    table_players = df_comp_all.iloc[start_idx:end_idx]

                    players_to_compare = pd.DataFrame()
                    if len(df_comp_all) >= 5: players_to_compare = pd.concat([df_comp_all.head(2), df_comp_all.iloc[len(df_comp_all)//2 : len(df_comp_all)//2 + 1], df_comp_all.tail(2)])
                    else: players_to_compare = df_comp_all[df_comp_all['Player'] != p['Player']]

                    # --- PDF ---
                    pdf = DarkScoutingPDF()
                    pdf.add_page()
                    try:
                        if os.path.exists(temp_face):
                            Image.open(temp_face).convert('RGB').save("temp_face_pdf.jpg", "JPEG")
                            pdf.image("temp_face_pdf.jpg", x=20, y=25, w=28)
                    except: pass
                    try:
                        if os.path.exists(temp_escudo): pdf.image(temp_escudo, x=165, y=28, w=22)
                    except: pass

                    pdf.set_y(35)
                    pdf.set_text_color(248, 250, 252) 
                    pdf.set_font("Arial", 'B', 24)
                    pdf.cell(0, 10, str(display_name).encode('latin-1', 'ignore').decode('latin-1').upper(), ln=True, align='C')
                    pdf.set_font("Arial", '', 12)
                    pdf.set_text_color(253, 224, 71) 
                    pdf.cell(0, 8, f"{display_team.upper()}  |  {p['Posicion_Scouting'].upper()}  |  {p['Age']} AÑOS", ln=True, align='C')
                    pdf.set_text_color(254, 240, 138)
                    pdf.cell(0, 8, f"Liga: {p['Categoria']}  |  Minutos: {p['Minutes played']}  |  V. Transfermarkt: {txt_mercado}", ln=True, align='C')
                    if os.path.exists(temp_radar): pdf.image(temp_radar, x=45, y=70, w=120)

                    pdf.set_y(200)
                    pdf.set_fill_color(30, 64, 175) 
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", 'B', 11)
                    pdf.cell(90, 10, " MÉTRICA CLAVE", border=1, fill=True)
                    pdf.cell(50, 10, " JUGADOR", border=1, align='C', fill=True)
                    pdf.cell(50, 10, " MEDIA LIGA", border=1, align='C', fill=True, ln=True)
                    pdf.set_font("Arial", '', 10)
                    for s in stats_clave:
                        val = float(p.get(s, 0))
                        mean = dict_mean.get(s, 0)
                        txt_val = f"{val:.1f}%" if "%" in s else str(val)
                        txt_mean = f"{mean:.1f}%" if "%" in s else f"{mean:.1f}"
                        inv = True if 'contra' in s.lower() or 'faltas' in s.lower() else False
                        if inv: pdf.set_text_color(253, 224, 71) if val < mean * 0.95 else (pdf.set_text_color(239, 68, 68) if val > mean * 1.05 else pdf.set_text_color(250, 204, 21))
                        else: pdf.set_text_color(253, 224, 71) if val > mean * 1.05 else (pdf.set_text_color(239, 68, 68) if val < mean * 0.95 else pdf.set_text_color(250, 204, 21))
                        pdf.cell(90, 8, f" {s.encode('latin-1', 'ignore').decode('latin-1')}", border=1)
                        pdf.cell(50, 8, txt_val, border=1, align='C')
                        pdf.set_text_color(248, 250, 252) 
                        pdf.cell(50, 8, txt_mean, border=1, align='C', ln=True)

                    pdf.add_page()
                    pdf.set_y(25)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(0, 10, " ANÁLISIS DAFO (BIG DATA SCOUTING)", ln=True)
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_text_color(253, 224, 71) 
                    pdf.cell(0, 6, " FORTALEZAS", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.set_text_color(254, 240, 138)
                    pdf.multi_cell(0, 5, "  " + txt_fortaleza.encode('latin-1', 'ignore').decode('latin-1'))
                    pdf.ln(2)
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_text_color(234, 179, 8) 
                    pdf.cell(0, 6, " OPORTUNIDADES", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.set_text_color(254, 240, 138)
                    pdf.multi_cell(0, 5, "  " + txt_oportunidad.encode('latin-1', 'ignore').decode('latin-1'))
                    pdf.ln(2)
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_text_color(239, 68, 68) 
                    pdf.cell(0, 6, " DEBILIDADES", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.set_text_color(254, 240, 138)
                    pdf.multi_cell(0, 5, "  " + txt_debilidad.encode('latin-1', 'ignore').decode('latin-1'))
                    pdf.ln(2)
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_text_color(250, 204, 21) 
                    pdf.cell(0, 6, " AMENAZAS", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.set_text_color(254, 240, 138)
                    pdf.multi_cell(0, 5, "  " + txt_amenaza.encode('latin-1', 'ignore').decode('latin-1'))
                    pdf.ln(10)
                    
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, " TABLA DE CONTEXTO VS RIVALES (rendimiento global)", ln=True)
                    w_p, w_num, w_stat = 38, 14, 25
                    cols_stats = stats_clave[:4] 
                    pdf.set_fill_color(30, 64, 175)
                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(w_p, 8, " JUGADOR", border=1, fill=True)
                    pdf.cell(w_num, 8, " P.J.", border=1, align='C', fill=True)
                    pdf.cell(w_num, 8, " MIN", border=1, align='C', fill=True)
                    pdf.cell(w_num, 8, " GOL", border=1, align='C', fill=True)
                    pdf.cell(w_num, 8, " ASIS", border=1, align='C', fill=True)
                    for s in cols_stats: pdf.cell(w_stat, 8, s.encode('latin-1', 'ignore').decode('latin-1')[:14], border=1, align='C', fill=True)
                    pdf.ln()

                    pdf.set_font("Arial", 'B', 8)
                    for _, r_t in table_players.iterrows():
                        iter_name = get_name(r_t['Player'])
                        if r_t['Player'] == p['Player']: 
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_fill_color(30, 58, 138) 
                        else: 
                            pdf.set_text_color(254, 240, 138)
                            pdf.set_fill_color(30, 41, 59) 
                        pj = str(r_t.get('Matches played', '-'))
                        mins = str(r_t.get('Minutes played', 0))
                        gol = str(r_t.get('Goals', 0))
                        asi = str(r_t.get('Assists', 0))
                        pdf.cell(w_p, 8, f" {str(iter_name).encode('latin-1', 'ignore').decode('latin-1')[:18]}", border=1, fill=True)
                        pdf.cell(w_num, 8, pj, border=1, align='C', fill=True)
                        pdf.cell(w_num, 8, mins, border=1, align='C', fill=True)
                        pdf.cell(w_num, 8, gol, border=1, align='C', fill=True)
                        pdf.cell(w_num, 8, asi, border=1, align='C', fill=True)
                        for s in cols_stats:
                            val = float(r_t.get(s, 0)); mean = dict_mean.get(s, 0); txt_c = f"{val:.1f}%" if "%" in s else f"{val:.1f}"
                            inv = True if 'contra' in s.lower() or 'faltas' in s.lower() else False
                            if inv:
                                if val < mean * 0.95: pdf.set_fill_color(234, 179, 8) 
                                elif val > mean * 1.05: pdf.set_fill_color(239, 68, 68) 
                                else: pdf.set_fill_color(217, 119, 6) 
                            else:
                                if val > mean * 1.05: pdf.set_fill_color(234, 179, 8) 
                                elif val < mean * 0.95: pdf.set_fill_color(239, 68, 68) 
                                else: pdf.set_fill_color(217, 119, 6) 
                            pdf.set_text_color(255, 255, 255)
                            pdf.cell(w_stat, 8, txt_c, border=1, align='C', fill=True)
                        pdf.ln()

                    pdf.set_fill_color(0, 0, 0); pdf.set_text_color(255, 255, 255)
                    pdf.cell(w_p, 8, " MEDIA DE LA LIGA", border=1, fill=True)
                    m_pj = f"{df_contexto['Matches played'].mean():.1f}" if 'Matches played' in df_contexto.columns else "-"
                    m_min = f"{df_contexto['Minutes played'].mean():.0f}"
                    m_gol = f"{df_contexto['Goals'].mean():.1f}"
                    m_asi = f"{df_contexto['Assists'].mean():.1f}"
                    pdf.cell(w_num, 8, m_pj, border=1, align='C', fill=True); pdf.cell(w_num, 8, m_min, border=1, align='C', fill=True)
                    pdf.cell(w_num, 8, m_gol, border=1, align='C', fill=True); pdf.cell(w_num, 8, m_asi, border=1, align='C', fill=True)
                    for s in cols_stats:
                        txt_c = f"{dict_mean.get(s,0):.1f}%" if "%" in s else f"{dict_mean.get(s,0):.1f}"
                        pdf.cell(w_stat, 8, txt_c, border=1, align='C', fill=True)
                    pdf.ln()

                    count_sc = 0
                    for i, f_sc in enumerate(temp_scatters):
                        if count_sc == 0:
                            pdf.add_page()
                            pdf.set_y(20)
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_font("Arial", 'B', 14)
                            pdf.cell(0, 10, " MAPAS DE DISPERSIÓN MULTIDIMENSIONAL", ln=True)
                            y_pos_sc = 35
                        if os.path.exists(f_sc): pdf.image(f_sc, x=25, y=y_pos_sc, w=160)
                        y_pos_sc += 125
                        count_sc += 1
                        if count_sc == 2: count_sc = 0

                    pdf.add_page()
                    pdf.set_y(25)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, " COMPARATIVA VISUAL VS OTROS PERFILES DE LA LIGA", ln=True)
                    y_comp = pdf.get_y() + 5
                    x_comp = 15
                    count_r = 0
                    for i, r_comp in players_to_compare.iterrows():
                        if count_r == 2: 
                            x_comp = 15; y_comp += 85; count_r = 0
                            if y_comp > 200: 
                                pdf.add_page(); y_comp = 30
                        vals_c = []
                        for s in stats_clave:
                            if s in df.columns:
                                mn, mx = dict_min.get(s, 0), dict_max.get(s, 100)
                                val = float(r_comp.get(s, 0.0))
                                vals_c.append(max(0, min(100, ((val - mn) / (mx - mn)) * 100)))
                            else: vals_c.append(0)
                        f_comp = f"temp_comp_{i}.png"
                        c_name = get_name(r_comp['Player'])[:12]
                        create_radar_matplotlib(theta_labels, vals_jug, vals_c, '#eab308', '#1e40af', f_comp, display_name[:10], c_name)
                        if os.path.exists(f_comp): pdf.image(f_comp, x=x_comp, y=y_comp, w=80)
                        x_comp += 90; count_r += 1

                    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')

            with colB:
                st.markdown(f"**Estadísticas clave ({p['Posicion_Scouting']}):**")
                if stats_clave:
                    df_contexto_media = df[(df['Categoria'] == p['Categoria']) & (df['Posicion_Scouting'] == p['Posicion_Scouting']) & (df['Minutes played'] >= 800)]
                    if len(df_contexto_media) < 3: df_contexto_media = df[(df['Categoria'] == p['Categoria']) & (df['Posicion_Scouting'] == p['Posicion_Scouting'])]
                    theta_labels, vals_jugador_pct, vals_media_pct, hover_jugador, hover_media = [], [], [], [], []
                    for s in stats_clave: 
                        val_real = p.get(s, 0)
                        if isinstance(val_real, float): val_real = int(val_real) if val_real.is_integer() else round(val_real, 1)
                        txt_val = f"{val_real}%" if "%" in s else str(val_real)
                        st.write(f"- {s}: **{txt_val}**")
                        if s in df.columns:
                            mean_real = df_contexto_media[s].mean() if not df_contexto_media.empty else 0
                            max_val = df_contexto_media[s].max() if not df_contexto_media.empty else 100
                            min_val = df_contexto_media[s].min() if not df_contexto_media.empty else 0
                            if max_val == min_val: max_val = min_val + 1
                            scaled_jugador = max(0, min(100, ((float(val_real) - min_val) / (max_val - min_val)) * 100))
                            scaled_media = max(0, min(100, ((mean_real - min_val) / (max_val - min_val)) * 100))
                            if isinstance(mean_real, float): mean_real = int(mean_real) if mean_real.is_integer() else round(mean_real, 1)
                            theta_labels.append(f"{s}<br><b>{val_real}</b> (Med: {mean_real})")
                            vals_jugador_pct.append(scaled_jugador)
                            vals_media_pct.append(scaled_media)
                            hover_jugador.append(f"{s}: {val_real}")
                            hover_media.append(f"Media en {p['Categoria']}: {mean_real}")
                        else:
                            theta_labels.append(s); vals_jugador_pct.append(0); vals_media_pct.append(0); hover_jugador.append("N/D"); hover_media.append("N/D")
                        
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(r=vals_media_pct, theta=theta_labels, fill='toself', name=f"Media {p['Posicion_Scouting']}", line_color='gray', opacity=0.4, hoverinfo="text", hovertext=hover_media))
                    fig.add_trace(go.Scatterpolar(r=vals_jugador_pct, theta=theta_labels, fill='toself', name=display_name, line_color='#eab308', opacity=0.8, hoverinfo="text", hovertext=hover_jugador))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 100])), margin=dict(l=80, r=80, t=50, b=50), legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5))
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.markdown("### 🧠 Análisis DAFO (Big Data Scouting)")
            c_dafo1, c_dafo2 = st.columns(2)
            with c_dafo1:
                st.success(f"**Fortalezas:** {txt_fortaleza}")
                st.error(f"**Debilidades:** {txt_debilidad}")
            with c_dafo2:
                st.info(f"**Oportunidades:** {txt_oportunidad}")
                st.warning(f"**Amenazas:** {txt_amenaza}")
                
            st.markdown("### 📊 Tabla de Contexto vs Rivales (Rendimiento Global)")
            html_table = "<table style='width:100%; text-align:center; border-collapse: collapse; font-family: sans-serif;'>"
            html_table += "<tr style='background-color:#1e3a8a; color:#fde047;'><th style='padding: 10px;'>JUGADOR</th><th>P.J.</th><th>MIN</th><th>GOL</th><th>ASIS</th>"
            for s in stats_clave: html_table += f"<th>{s[:14]}</th>"
            html_table += "</tr>"
            
            for _, r_t in table_players.iterrows():
                iter_name_ui = get_name(r_t['Player'])
                bg_tr = "#fef08a" if r_t['Player'] == p['Player'] else "transparent"
                color_tr = "#1e3a8a" if r_t['Player'] == p['Player'] else "#1e293b"
                html_table += f"<tr style='background-color:{bg_tr}; color:{color_tr}; border-bottom:1px solid #fde047;'><td style='text-align:left; padding:10px; font-weight:bold;'>{str(iter_name_ui)[:18]}</td>"
                html_table += f"<td>{r_t.get('Matches played', '-')}</td><td>{r_t.get('Minutes played', 0)}</td><td>{r_t.get('Goals', 0)}</td><td>{r_t.get('Assists', 0)}</td>"
                for s in stats_clave:
                    val = float(r_t.get(s, 0)); mean = dict_mean.get(s, 0); txt_c = f"{val:.1f}%" if "%" in s else f"{val:.1f}"
                    inv = True if 'contra' in s.lower() or 'faltas' in s.lower() else False
                    if inv:
                        if val < mean * 0.95: bg_td = "#eab308" 
                        elif val > mean * 1.05: bg_td = "#ef4444" 
                        else: bg_td = "#f59e0b" 
                    else:
                        if val > mean * 1.05: bg_td = "#eab308" 
                        elif val < mean * 0.95: bg_td = "#ef4444" 
                        else: bg_td = "#f59e0b" 
                    html_table += f"<td style='background-color:{bg_td}; color:white; font-weight:bold;'>{txt_c}</td>"
                html_table += "</tr>"
                
            html_table += "<tr style='background-color:#1e3a8a; color:#fde047; font-weight:bold;'><td style='text-align:left; padding:10px;'>Media de la liga</td>"
            html_table += f"<td>{m_pj}</td><td>{m_min}</td><td>{m_gol}</td><td>{m_asi}</td>"
            for s in stats_clave:
                txt_c = f"{dict_mean.get(s,0):.1f}%" if "%" in s else f"{dict_mean.get(s,0):.1f}"
                html_table += f"<td>{txt_c}</td>"
            html_table += "</tr></table>"
            st.markdown(html_table, unsafe_allow_html=True)

            st.markdown("### 🎯 Mapas de Dispersión Multidimensionales")
            sc_cols = st.columns(2)
            for col_idx, f_sc in enumerate(temp_scatters):
                if os.path.exists(f_sc): sc_cols[col_idx % 2].image(f_sc, use_container_width=True)
                    
            st.markdown("---")
            st.download_button(label="📥 Descargar informe de jugador", data=pdf_bytes, file_name=f"Scouting_DaniFC_{display_name.replace(' ','_')}.pdf", mime='application/pdf')

            for f_tmp in glob.glob("temp_*.png") + glob.glob("temp_*.jpg"):
                try: os.remove(f_tmp)
                except: pass

    with tab_comp:
        st.header("⚖️ Comparador Múltiple (hasta 5 jugadores)")
        jugadores_comp = st.multiselect("Selecciona hasta 5 jugadores para comparar", sorted(df_filt['Player'].dropna().unique().tolist()), max_selections=5, format_func=lambda x: get_name(x))
        if jugadores_comp:
            datos_jugadores = [df[df['Player'] == j].iloc[0] for j in jugadores_comp]
            posicion_base = datos_jugadores[0]['Posicion_Scouting']
            stats_comp = metrics_dict.get(posicion_base, [])
            colores_comp = ['#1e3a8a', '#ef4444', '#eab308', '#f59e0b', '#8b5cf6']
            
            if stats_comp:
                if any(p['Posicion_Scouting'] != posicion_base for p in datos_jugadores): st.warning(f"⚠️ Estás comparando jugadores de diferentes posiciones. Las métricas se basan en: **{posicion_base}**.")
                col_r, col_t = st.columns([1.5, 1])
                with col_r:
                    fig_comp = go.Figure()
                    for i, p_data in enumerate(datos_jugadores):
                        name_disp = get_name(p_data['Player'])
                        v = [(df[df['Categoria'] == p_data['Categoria']][m].rank(pct=True).loc[p_data.name] * 100) if m in df.columns else 0 for m in stats_comp]
                        fig_comp.add_trace(go.Scatterpolar(r=v, theta=stats_comp, fill='toself', name=name_disp, line_color=colores_comp[i], opacity=0.5))
                    fig_comp.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(l=80, r=80, t=50, b=50))
                    st.plotly_chart(fig_comp, use_container_width=True)
                with col_t:
                    st.markdown("### Cara a Cara (valores reales)")
                    fig_bar = go.Figure()
                    for i, p_data in enumerate(datos_jugadores):
                        name_disp = get_name(p_data['Player']); val_list, text_list = [], []
                        for s in stats_comp:
                            v = p_data.get(s, 0)
                            val_num = float(v) if pd.notna(v) else 0.0
                            val_list.append(val_num)
                            v_fmt = int(v) if isinstance(v, float) and v.is_integer() else round(val_num, 2)
                            text_list.append(f"{v_fmt}%" if "%" in s else str(v_fmt))
                        fig_bar.add_trace(go.Bar(y=stats_comp, x=val_list, name=name_disp, orientation='h', marker_color=colores_comp[i], text=text_list, textposition='auto'))
                    fig_bar.update_layout(barmode='group', margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig_bar, use_container_width=True)

    with tab_intel:
        st.header("📊 Inteligencia de Mercado - Segunda Federación")
        vista_intel = st.radio("Módulo:", ["Mapa de dispersión", "Mejores por posición", "Campograma visual"], horizontal=True)
        st.markdown("---")
        df_intel_plot = df_filt.copy()
        if blind_mode:
            df_intel_plot['Player'] = df_intel_plot['Player'].apply(get_name)
            df_intel_plot['Team'] = df_intel_plot['Team'].apply(get_team)

        if vista_intel == "Mapa de dispersión":
            cx, cy = st.columns(2)
            ex = cx.selectbox("Eje X", df_intel_plot.columns, index=df_intel_plot.columns.get_loc('Minutes played') if 'Minutes played' in df_intel_plot.columns else 0)
            ey = cy.selectbox("Eje Y", df_intel_plot.columns, index=df_intel_plot.columns.get_loc('Age') if 'Age' in df_intel_plot.columns else 0)
            fig_scat = px.scatter(df_intel_plot, x=ex, y=ey, color="Posicion_Scouting", text="Player", hover_name="Player")
            fig_scat.update_traces(textposition='top center')
            st.plotly_chart(fig_scat, use_container_width=True)

        elif vista_intel == "Mejores por posición":
            dfr = df_intel_plot.copy()
            for pos, stats in metrics_dict.items():
                dp = dfr[dfr['Posicion_Scouting'] == pos].copy()
                if not dp.empty:
                    dp['Rating'] = sum(dp[s].rank(pct=True) for s in stats if s in dp.columns)
                    st.markdown(f"**🏆 Mejores {pos} de la liga**")
                    st.dataframe(dp.nlargest(5, 'Rating')[['Player', 'Team', 'Age'] + [s for s in stats if s in dp.columns]])

        elif vista_intel == "Campograma visual":
            col_met, col_sist = st.columns(2)
            with col_met: metodologia = st.selectbox("🧠 Metodología:", ["Juego de posición (posesión)", "Bloque bajo y contraataque", "Presión alta y transiciones rápidas"])
            with col_sist: sistema = st.selectbox("📋 Sistema:", ["1-4-3-3", "1-4-4-2", "1-4-2-3-1", "1-5-3-2", "1-3-4-3"])

            metricas_tacticas = {
                "Juego de posición (posesión)": {'Portero': ['Pases precisos %', 'Paradas %'], 'Central': ['Pases hacia adelante %', 'Pases precisos %', 'Duelos defensivos %'], 'Lateral': ['Pases precisos %', 'Centros %', 'Duelos defensivos %'], 'Mediocentro': ['Precisión pases en el último tercio %', 'Pases precisos %', 'Regates %'], 'Extremo': ['Regates %', 'xA', 'Toques en área'], 'Delantero': ['xG', 'Pases precisos %', 'Toques en área']},
                "Bloque bajo y contraataque": {'Portero': ['Paradas %', 'Goles evitados'], 'Central': ['Duelos aéreos ganados %', 'Duelos defensivos %', 'Interceptaciones'], 'Lateral': ['Duelos defensivos %', 'Interceptaciones'], 'Mediocentro': ['Recuperaciones', 'Interceptaciones', 'Duelos defensivos %'], 'Extremo': ['Carreras progresivas', 'xA'], 'Delantero': ['Goals', 'xG', 'Duelos aéreos ganados %']},
                "Presión alta y transiciones rápidas": {'Portero': ['Paradas %', 'Goles evitados'], 'Central': ['Duelos defensivos %', 'Interceptaciones', 'Pases hacia adelante %'], 'Lateral': ['Carreras progresivas', 'Recuperaciones', 'Centros %'], 'Mediocentro': ['Recuperaciones', 'Entradas', 'Pases hacia adelante %'], 'Extremo': ['Regates %', 'Recuperaciones', 'Toques en área'], 'Delantero': ['xG', 'Toques en área', 'Recuperaciones']}
            }

            estructuras = {
                "1-4-3-3": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'LI', 'rol': 'Lateral', 'x': 15, 'y': 25, 'lado': 'Izq'}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 35, 'y': 22, 'lado': 'Izq'}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 65, 'y': 22, 'lado': 'Der'}, {'id': 'LD', 'rol': 'Lateral', 'x': 85, 'y': 25, 'lado': 'Der'}, {'id': 'MCD', 'rol': 'Mediocentro', 'x': 50, 'y': 40, 'lado': None}, {'id': 'MC (I)', 'rol': 'Mediocentro', 'x': 30, 'y': 55, 'lado': 'Izq'}, {'id': 'MC (D)', 'rol': 'Mediocentro', 'x': 70, 'y': 55, 'lado': 'Der'}, {'id': 'EI', 'rol': 'Extremo', 'x': 20, 'y': 78, 'lado': 'Izq'}, {'id': 'ED', 'rol': 'Extremo', 'x': 80, 'y': 78, 'lado': 'Der'}, {'id': 'DC', 'rol': 'Delantero', 'x': 50, 'y': 85, 'lado': None}],
                "1-4-4-2": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'LI', 'rol': 'Lateral', 'x': 15, 'y': 25, 'lado': 'Izq'}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 35, 'y': 22, 'lado': 'Izq'}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 65, 'y': 22, 'lado': 'Der'}, {'id': 'LD', 'rol': 'Lateral', 'x': 85, 'y': 25, 'lado': 'Der'}, {'id': 'MI', 'rol': 'Extremo', 'x': 15, 'y': 55, 'lado': 'Izq'}, {'id': 'MC (I)', 'rol': 'Mediocentro', 'x': 35, 'y': 50, 'lado': 'Izq'}, {'id': 'MC (D)', 'rol': 'Mediocentro', 'x': 65, 'y': 50, 'lado': 'Der'}, {'id': 'MD', 'rol': 'Extremo', 'x': 85, 'y': 55, 'lado': 'Der'}, {'id': 'DC (I)', 'rol': 'Delantero', 'x': 35, 'y': 82, 'lado': 'Izq'}, {'id': 'DC (D)', 'rol': 'Delantero', 'x': 65, 'y': 82, 'lado': 'Der'}],
                "1-4-2-3-1": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'LI', 'rol': 'Lateral', 'x': 15, 'y': 25, 'lado': 'Izq'}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 35, 'y': 22, 'lado': 'Izq'}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 65, 'y': 22, 'lado': 'Der'}, {'id': 'LD', 'rol': 'Lateral', 'x': 85, 'y': 25, 'lado': 'Der'}, {'id': 'MCD (I)', 'rol': 'Mediocentro', 'x': 35, 'y': 45, 'lado': 'Izq'}, {'id': 'MCD (D)', 'rol': 'Mediocentro', 'x': 65, 'y': 45, 'lado': 'Der'}, {'id': 'EI', 'rol': 'Extremo', 'x': 20, 'y': 68, 'lado': 'Izq'}, {'id': 'MCO', 'rol': 'Mediocentro', 'x': 50, 'y': 65, 'lado': None}, {'id': 'ED', 'rol': 'Extremo', 'x': 80, 'y': 68, 'lado': 'Der'}, {'id': 'DC', 'rol': 'Delantero', 'x': 50, 'y': 85, 'lado': None}],
                "1-5-3-2": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'CAI', 'rol': 'Lateral', 'x': 12, 'y': 35, 'lado': 'Izq'}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 30, 'y': 22, 'lado': 'Izq'}, {'id': 'DFC (C)', 'rol': 'Central', 'x': 50, 'y': 19, 'lado': None}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 70, 'y': 22, 'lado': 'Der'}, {'id': 'CAD', 'rol': 'Lateral', 'x': 88, 'y': 35, 'lado': 'Der'}, {'id': 'MC (I)', 'rol': 'Mediocentro', 'x': 30, 'y': 55, 'lado': 'Izq'}, {'id': 'MCD', 'rol': 'Mediocentro', 'x': 50, 'y': 48, 'lado': None}, {'id': 'MC (D)', 'rol': 'Mediocentro', 'x': 70, 'y': 55, 'lado': 'Der'}, {'id': 'DC (I)', 'rol': 'Delantero', 'x': 35, 'y': 82, 'lado': 'Izq'}, {'id': 'DC (D)', 'rol': 'Delantero', 'x': 65, 'y': 82, 'lado': 'Der'}],
                "1-3-4-3": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 25, 'y': 22, 'lado': 'Izq'}, {'id': 'DFC (C)', 'rol': 'Central', 'x': 50, 'y': 19, 'lado': None}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 75, 'y': 22, 'lado': 'Der'}, {'id': 'MI / CAI', 'rol': 'Lateral', 'x': 15, 'y': 50, 'lado': 'Izq'}, {'id': 'MC (I)', 'rol': 'Mediocentro', 'x': 35, 'y': 45, 'lado': 'Izq'}, {'id': 'MC (D)', 'rol': 'Mediocentro', 'x': 65, 'y': 45, 'lado': 'Der'}, {'id': 'MD / CAD', 'rol': 'Lateral', 'x': 85, 'y': 50, 'lado': 'Der'}, {'id': 'EI', 'rol': 'Extremo', 'x': 25, 'y': 78, 'lado': 'Izq'}, {'id': 'ED', 'rol': 'Extremo', 'x': 75, 'y': 78, 'lado': 'Der'}, {'id': 'DC', 'rol': 'Delantero', 'x': 50, 'y': 85, 'lado': None}]
            }

            if df_filt.empty:
                st.warning("No hay suficientes jugadores con los filtros actuales.")
            else:
                df_opt = df_filt.copy()
                df_opt['Rating_Tactico'] = 0.0
                metricas_elegidas = metricas_tacticas[metodologia]
                for pos_eval, stats in metricas_elegidas.items():
                    mask = df_opt['Posicion_Scouting'] == pos_eval
                    if mask.sum() > 0:
                        for s in stats:
                            if s in df_opt.columns: df_opt.loc[mask, 'Rating_Tactico'] += df_opt.loc[mask, s].fillna(0).rank(pct=True)
                
                df_opt = df_opt.sort_values(by='Rating_Tactico', ascending=False)
                selected_players, formation_data = [], []
                
                def obtener_base64_y_nombres(df_disponible, lado, excluidos):
                    df_libre = df_disponible[~df_disponible['Player'].isin(excluidos)]
                    if lado == 'Izq': df_ideal = df_libre[df_libre['Foot'].isin(['Zurdo', 'Ambidiestro'])]
                    elif lado == 'Der': df_ideal = df_libre[df_libre['Foot'].isin(['Diestro', 'Ambidiestro'])]
                    else: df_ideal = df_libre
                    df_final = pd.concat([df_ideal, df_libre[~df_libre['Player'].isin(df_ideal['Player'])]]).head(3) if len(df_ideal) < 3 else df_ideal.head(3)
                    if df_final.empty: return None, "N/D", "N/D", "N/D", []
                    p1_real = df_final.iloc[0]['Player'] if len(df_final) > 0 else "N/D"
                    p2_real = df_final.iloc[1]['Player'] if len(df_final) > 1 else "N/D"
                    p3_real = df_final.iloc[2]['Player'] if len(df_final) > 2 else "N/D"
                    if p1_real != "N/D":
                        url_jugador_top1 = "https://ui-avatars.com/api/?name=PO&background=1e3a8a&color=fff&size=128&bold=true" if blind_mode else convertir_imagen_base64(buscar_mejor_coincidencia(p1_real, ARCHIVOS_CARAS), f"https://ui-avatars.com/api/?name={urllib.parse.quote(p1_real)}&background=1e3a8a&color=fff&size=128&bold=true")[0]
                    else: url_jugador_top1 = None
                    return url_jugador_top1, p1_real, p2_real, p3_real, [n for n in [p1_real, p2_real, p3_real] if n != "N/D"]
                
                for pos_data in estructuras[sistema]:
                    img_top1, p1_real, p2_real, p3_real, usados = obtener_base64_y_nombres(df_opt[df_opt['Posicion_Scouting'] == pos_data['rol']], pos_data.get('lado'), selected_players)
                    if usados: selected_players.extend(usados)
                    formation_data.append({'id': pos_data['id'], 'x': pos_data['x'], 'y': pos_data['y'], 'image': img_top1, 'top1_real': p1_real, 'top1_disp': get_name(p1_real) if p1_real != "N/D" else "N/D", 'top2_real': p2_real, 'top2_disp': get_name(p2_real) if p2_real != "N/D" else "N/D", 'top3_real': p3_real, 'top3_disp': get_name(p3_real) if p3_real != "N/D" else "N/D"})

                fig_pitch = go.Figure()
                fig_pitch.update_layout(xaxis=dict(range=[0, 100], visible=False, fixedrange=True), yaxis=dict(range=[0, 100], visible=False, fixedrange=True), plot_bgcolor='#1e3a8a', margin=dict(l=0, r=0, t=0, b=0), height=700)
                fig_pitch.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, line=dict(color="#fde047", width=2), layer="below")
                fig_pitch.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line=dict(color="#fde047", width=2), layer="below")
                fig_pitch.add_shape(type="circle", x0=40, y0=40, x1=60, y1=60, line=dict(color="#fde047", width=2), layer="below")
                fig_pitch.add_shape(type="rect", x0=20, y0=0, x1=80, y1=18, line=dict(color="#fde047", width=2), layer="below")
                fig_pitch.add_shape(type="rect", x0=35, y0=0, x1=65, y1=6, line=dict(color="#fde047", width=2), layer="below")
                fig_pitch.add_shape(type="rect", x0=20, y0=82, x1=80, y1=100, line=dict(color="#fde047", width=2), layer="below")
                fig_pitch.add_shape(type="rect", x0=35, y0=94, x1=65, y1=100, line=dict(color="#fde047", width=2), layer="below")
                
                for item in formation_data:
                    if item['image']: fig_pitch.add_layout_image(dict(source=item['image'], xref="x", yref="y", x=item['x'], y=item['y'], sizex=12, sizey=12, xanchor="center", yanchor="middle", layer="above"))

                x_pts, y_pts, texts, hover_txts = [], [], [], []
                for item in formation_data:
                    x_pts.append(item['x']); y_pts.append(item['y'])
                    if item['top1_real'] != "N/D":
                        texts.append(item['top1_disp']); hover_txts.append(f"<b>{item['id']}</b><br>1️⃣ {item['top1_disp']}<br>2️⃣ {item['top2_disp']}<br>3️⃣ {item['top3_disp']}")
                    else: texts.append("N/D"); hover_txts.append(f"<b>{item['id']}</b><br>Sin datos")

                fig_pitch.add_trace(go.Scatter(x=x_pts, y=[y - 8 for y in y_pts], mode='text', text=texts, textfont=dict(color='#fde047', size=12, family="Arial Black"), hoverinfo='none'))
                fig_pitch.add_trace(go.Scatter(x=x_pts, y=y_pts, mode='markers', marker=dict(size=45, color='rgba(0,0,0,0)'), hoverinfo='text', hovertext=hover_txts))
                st.plotly_chart(fig_pitch, use_container_width=True, config={'displayModeBar': False})

                st.markdown("### 🔄 Radar de Opciones de Mercado")
                cols = st.columns(3)
                for idx, item in enumerate(formation_data):
                    with cols[idx % 3]: 
                        st.markdown(f"**{item['id']}**")
                        if item['top1_real'] != "N/D": st.button(f"🥇 {item['top1_disp']}", key=f"btn1_{item['id']}", on_click=cambiar_jugador, args=(item['top1_real'],))
                        if item['top2_real'] != "N/D": st.button(f"🥈 {item['top2_disp']}", key=f"btn2_{item['id']}", on_click=cambiar_jugador, args=(item['top2_real'],))
                        if item['top3_real'] != "N/D": st.button(f"🥉 {item['top3_disp']}", key=f"btn3_{item['id']}", on_click=cambiar_jugador, args=(item['top3_real'],))
                        st.write("---")

    with tab_tabla:
        st.header("🗃️ Base de Datos Filtrada Big Data")
        df_tabla_mostrar = df_filt.copy()
        if blind_mode:
            df_tabla_mostrar['Player'] = df_tabla_mostrar['Player'].apply(get_name)
            df_tabla_mostrar['Team'] = df_tabla_mostrar['Team'].apply(get_team)
        st.dataframe(df_tabla_mostrar, use_container_width=True)


# =========================================================================================
# ======================== MÓDULO 2: SCOUTING DE CAMPO (DANI FC) ==========================
# =========================================================================================
elif modulo_seleccionado == "📋 Módulo Scouting de Campo":

    ARCHIVO_INFORMES = "mis_informes.csv"
    COLUMNAS_BASE = ["Fecha", "Jugador", "Equipo", "Categoria", "Edad", "Lateralidad", "Posicion", "Partido", "Valoracion", "Fortalezas", "Debilidades", "Comentarios", "Metricas_Rol", "Imagen", "Ojeador"]

    if not os.path.exists(ARCHIVO_INFORMES):
        df_init = pd.DataFrame(columns=COLUMNAS_BASE)
        df_init.to_csv(ARCHIVO_INFORMES, index=False, encoding='utf-8')
    else:
        df_check = pd.read_csv(ARCHIVO_INFORMES, encoding='utf-8')
        modificado = False
        
        nuevas_cols = ["Edad", "Lateralidad", "Partido", "Imagen", "Ojeador"]
        for col in nuevas_cols:
            if col not in df_check.columns:
                df_check[col] = "-"
                modificado = True
                
        if "Metricas_Rol" not in df_check.columns:
            df_check["Metricas_Rol"] = "{}"
            modificado = True

        faltantes = [c for c in COLUMNAS_BASE if c not in df_check.columns]
        for f in faltantes: df_check[f] = "-"
        df_check = df_check[COLUMNAS_BASE]
        
        if modificado:
            df_check.to_csv(ARCHIVO_INFORMES, index=False, encoding='utf-8')

    PERFILES_DICT = {
        "Portero": {
            "POR 1.1 (Dominador)": ["Dominio área", "Blocaje", "Posicionamiento", "Juego Aéreo"],
            "POR 1.2 (Ágil)": ["Reflejos", "1vs1", "Agilidad", "Estirada"]
        },
        "Central": {
            "DFC 2.1 (Táctico)": ["Anticipación", "Lectura juego", "Cortes pase"],
            "DFC 2.2 (Corrector)": ["Velocidad recup.", "Cobertura espalda", "Transición def."],
            "DFC 2.3 (Físico)": ["Dominio aéreo", "Contundencia", "Marcaje ind."],
            "DFC 2.4 (Salida)": ["Pase diagonal", "Salida balón", "Calma presión"]
        },
        "Lateral": {
            "LAT 4.1 (Profundo)": ["Aceleración", "Desdoblamiento", "Centro carrera"],
            "LAT 4.2 (Asociativo)": ["Centro medido", "Circulación", "Pausa"],
            "LAT 4.3 (Interiorizado)": ["Incorporación int.", "Sostén salida", "Atraer/Fijar"]
        },
        "Mediocentro": {
            "MC 6.1 (Organizador)": ["Pase corto", "Gestión ritmo", "Seguridad pos."],
            "MC 6.2 (Lanzador)": ["Pase diagonal", "Cambios orient.", "Visión global"],
            "MC 6.3 (Conductor)": ["Conducción", "Protección balón", "Giro/Progresión"],
            "MC 6.4 (Defensivo)": ["Cobertura", "Recuperación", "Fuerza física"]
        },
        "Extremo": {
            "EXT 9.1 (Desborde)": ["Velocidad cond.", "1vs1 abierto", "Explosividad"],
            "EXT 9.2 (Técnico)": ["Desequilibrio corto", "Cambios dirección", "Resolución interior"],
            "EXT 9.3 (Asociativo)": ["Paciencia comb.", "Ocupación interior", "Asociación"],
            "EXT 9.4 (Profundidad)": ["Ruptura", "Velocidad punta", "Timing arranque"]
        },
        "Delantero": {
            "DC 10.1 (Potente)": ["Potencia disparo", "Imposición física", "Resolución directa"],
            "DC 10.2 (Técnico)": ["Primer control", "Generación espacio", "Agilidad"],
            "DC 10.3 (Referencia)": ["Dominio aéreo", "Fijación centrales", "Protección balón"],
            "DC 10.4 (Móvil)": ["Descuelga apoyo", "Pase último tercio", "Buen golpeo"],
            "DC 10.5 (Ruptura)": ["Desmarques ruptura", "Atacar espaldas", "Finalización carrera"]
        }
    }

    tab_crear_informe, tab_informe_partido, tab_once_ideal, tab_mis_informes = st.tabs([
        "✍️ Crear Informe Individual",
        "🏟️ Informe de Partido",
        "🏆 Onces Ideales",
        "📂 Informes"
    ])

    with tab_crear_informe:
        st.header("✍️ Crear Informe Individual")
        st.info("Al valorar las métricas específicas, el sistema asignará automáticamente el perfil táctico que mejor encaje con el jugador. La valoración global se calcula sola haciendo la media de todas tus puntuaciones.")
        
        posicion_pre = st.selectbox("Posición principal (desbloquea métricas)", list(PERFILES_DICT.keys()))
        
        with st.form("form_crear_informe_individual"):
            st.markdown("### 📋 Datos del jugador y ojeador")
            col_inf1, col_inf2, col_inf3, col_inf_oj = st.columns(4)
            fecha_obs = col_inf1.date_input("Fecha de observación", value=date.today())
            nombre_jugador = col_inf2.text_input("Nombre del jugador *")
            equipo_jugador = col_inf3.text_input("Equipo actual")
            ojeador_input = col_inf_oj.selectbox("Ojeador responsable", ["Dani Rodríguez", "Colaborador Externo", "Dirección Deportiva"])
            
            c1, c2, c3, c4 = st.columns(4)
            categoria_jugador = c1.selectbox("Categoría", ["Tercera Federación", "Segunda Federación", "Primera Federación", "División de Honor Juvenil", "Regionales"])
            edad_jugador = c2.number_input("Edad", min_value=14, max_value=45, value=22)
            lat_jugador = c3.selectbox("Lateralidad (pie)", ["Diestro", "Zurdo", "Ambidiestro"])
            partido_vis = c4.text_input("Partido visualizado / ubicación", placeholder="Ej. Dani FC vs CD Ficticio (Dani FC)")
            
            img_jugador = st.text_input("URL de fotografía del jugador (opcional)", placeholder="https://ejemplo.com/foto_jugador.jpg")
            
            st.markdown(f"### 📊 Métricas específicas: {posicion_pre}")
            valores_metricas = {}
            
            cols_met = st.columns(3)
            idx_col = 0
            metricas_listadas = []
            for sub_rol, metricas in PERFILES_DICT[posicion_pre].items():
                for met in metricas:
                    if met not in metricas_listadas:
                        metricas_listadas.append(met)
                        valores_metricas[met] = cols_met[idx_col % 3].slider(met, 1, 10, 5)
                        idx_col += 1

            st.markdown("### Notas tácticas")
            notas_fortalezas = st.text_area("Fortalezas")
            notas_debilidades = st.text_area("Debilidades")
            notas_comentarios = st.text_area("Comentarios")
            
            submitted = st.form_submit_button("💾 Guardar informe")
            
            if submitted:
                if nombre_jugador.strip() == "":
                    st.error("⚠️ El campo 'Nombre del jugador' es obligatorio.")
                else:
                    valoracion_general = round(sum(valores_metricas.values()) / len(valores_metricas), 1)

                    promedios_roles = {}
                    for sub_rol, metricas in PERFILES_DICT[posicion_pre].items():
                        promedio = sum(valores_metricas[m] for m in metricas) / len(metricas)
                        promedios_roles[sub_rol] = promedio
                    
                    rol_asignado = max(promedios_roles, key=promedios_roles.get)
                    valores_metricas["Rol_Calculado"] = rol_asignado
                    json_metricas = json.dumps(valores_metricas)
                    
                    df_actual = pd.read_csv(ARCHIVO_INFORMES, encoding='utf-8') if os.path.exists(ARCHIVO_INFORMES) else pd.DataFrame(columns=COLUMNAS_BASE)
                    
                    if not df_actual.empty and 'Jugador' in df_actual.columns:
                        mask = df_actual['Jugador'].str.strip().str.lower() == nombre_jugador.strip().lower()
                        if mask.sum() > 0:
                            df_actual.loc[mask, ['Fecha', 'Equipo', 'Categoria', 'Edad', 'Lateralidad', 'Posicion', 'Partido', 'Valoracion', 'Fortalezas', 'Debilidades', 'Comentarios', 'Metricas_Rol', 'Imagen', 'Ojeador']] = [
                                fecha_obs, equipo_jugador, categoria_jugador, edad_jugador, lat_jugador, posicion_pre, partido_vis, valoracion_general, notas_fortalezas, notas_debilidades, notas_comentarios, json_metricas, img_jugador, ojeador_input
                            ]
                            df_actual.to_csv(ARCHIVO_INFORMES, index=False, encoding='utf-8')
                            st.success(f"🔄 ¡Informe actualizado (suscrito)! El jugador **{nombre_jugador}** ya existía y se han sobrescrito sus datos.")
                        else:
                            nuevo_dato = pd.DataFrame([[fecha_obs, nombre_jugador, equipo_jugador, categoria_jugador, edad_jugador, lat_jugador, posicion_pre, partido_vis, valoracion_general, notas_fortalezas, notas_debilidades, notas_comentarios, json_metricas, img_jugador, ojeador_input]], columns=COLUMNAS_BASE)
                            nuevo_dato.to_csv(ARCHIVO_INFORMES, mode='a', header=False, index=False, encoding='utf-8')
                            st.success(f"✅ ¡Guardado con éxito! Nota media calculada: ⭐ {valoracion_general}/10. Rol asignado: **{rol_asignado}**")
                    else:
                        nuevo_dato = pd.DataFrame([[fecha_obs, nombre_jugador, equipo_jugador, categoria_jugador, edad_jugador, lat_jugador, posicion_pre, partido_vis, valoracion_general, notas_fortalezas, notas_debilidades, notas_comentarios, json_metricas, img_jugador, ojeador_input]], columns=COLUMNAS_BASE)
                        nuevo_dato.to_csv(ARCHIVO_INFORMES, mode='a', header=False, index=False, encoding='utf-8')
                        st.success(f"✅ ¡Guardado con éxito! Nota media calculada: ⭐ {valoracion_general}/10. Rol asignado: **{rol_asignado}**")

    with tab_informe_partido:
        st.header("🏟️ Informe de Partido")
        st.info("Introduce los 16 jugadores por equipo (11 titulares + hasta 5 suplentes), asígnales posición y pondera sus métricas clave. Al guardar, se suscribirán automáticamente a tu base de datos.")

        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        cat_partido = col_p1.selectbox("Categoría del partido", ["Tercera Federación", "Segunda Federación", "Primera Federación", "División de Honor Juvenil", "Regionales"], key="cat_part_11")
        fecha_partido = col_p2.date_input("Fecha del partido", value=date.today(), key="fec_part_11")
        lugar_partido = col_p3.text_input("Lugar / estadio / partido", placeholder="Ej. Estadio Dani FC / Dani FC vs Club Rival")
        ojeador_partido = col_p4.selectbox("Ojeador responsable", ["Dani Rodríguez", "Colaborador Externo", "Dirección Deportiva"], key="oj_part_11")
        
        col_eq1, col_eq2 = st.columns(2)
        eq_local = col_eq1.text_input("Equipo local", placeholder="Ej. Dani FC")
        eq_visitante = col_eq2.text_input("Equipo visitante", placeholder="Ej. Club Rival")

        posiciones_lista = ["Portero", "Lateral", "Central", "Mediocentro", "Extremo", "Delantero"]
        def_16 = ["Portero", "Lateral", "Central", "Central", "Lateral", "Mediocentro", "Mediocentro", "Extremo", "Mediocentro", "Extremo", "Delantero"] + ["Mediocentro" for _ in range(5)]

        df_local_base = pd.DataFrame({
            "Jugador": [f"Titular {i+1}" if i<11 else f"Suplente {i-10}" for i in range(16)],
            "Posicion": pd.Categorical(def_16, categories=posiciones_lista),
            "Edad": [21 for _ in range(16)],
            "Lateralidad": pd.Categorical(["Diestro" for _ in range(16)], categories=["Diestro", "Zurdo", "Ambidiestro"]),
        })
        df_visita_base = pd.DataFrame({
            "Jugador": [f"Titular {i+1}" if i<11 else f"Suplente {i-10}" for i in range(16)],
            "Posicion": pd.Categorical(def_16, categories=posiciones_lista),
            "Edad": [21 for _ in range(16)],
            "Lateralidad": pd.Categorical(["Diestro" for _ in range(16)], categories=["Diestro", "Zurdo", "Ambidiestro"]),
        })

        st.markdown("---")
        st.markdown("### 🎛️ Panel de Ponderación de Métricas en Directo")
        equipo_a_ponderar = st.radio("Selecciona qué equipo deseas ponderar métricamente en vivo:", [eq_local if eq_local else "Local", eq_visitante if eq_visitante else "Visitante"], horizontal=True)

        c_l_edit, c_v_edit = st.columns(2)
        with c_l_edit:
            st.markdown(f"**Plantilla base (11+5): {eq_local if eq_local else 'Local'}**")
            edit_l_inf = st.data_editor(df_local_base, key="edit_l_16", use_container_width=True, num_rows="dynamic")
        with c_v_edit:
            st.markdown(f"**Plantilla base (11+5): {eq_visitante if eq_visitante else 'Visitante'}**")
            edit_v_inf = st.data_editor(df_visita_base, key="edit_v_16", use_container_width=True, num_rows="dynamic")

        st.markdown("---")
        st.markdown(f"#### ⚙️ Ponderando métricas en directo para: **{equipo_a_ponderar}**")
        
        if 'dict_ponderacion_partido' not in st.session_state:
            st.session_state.dict_ponderacion_partido = {}

        plantilla_activa = edit_l_inf if equipo_a_ponderar == (eq_local if eq_local else "Local") else edit_v_inf
        nombres_activos = [j for j in plantilla_activa['Jugador'].tolist() if str(j).strip() != "" and not str(j).startswith("Titular ") and not str(j).startswith("Suplente ")]
        
        if not nombres_activos:
            st.info("💡 Escribe los nombres reales de los jugadores en la tabla superior para poder ponderar sus métricas aquí.")
        else:
            jugador_seleccionado_pond = st.selectbox("Selecciona jugador a ponderar:", nombres_activos)
            fila_j = plantilla_activa[plantilla_activa['Jugador'] == jugador_seleccionado_pond].iloc[0]
            pos_j = fila_j['Posicion']
            
            st.write(f"Demarcación detectada: **{pos_j}**. Ajusta sus notas según lo visto en el partido:")
            
            sub_roles_pos = PERFILES_DICT.get(pos_j, {})
            pond_actuales = {}
            col_p1, col_p2, col_p3 = st.columns(3)
            idx_p = 0
            for sr, mets in sub_roles_pos.items():
                for m in mets:
                    if m not in pond_actuales:
                        val_previo = st.session_state.dict_ponderacion_partido.get(jugador_seleccionado_pond, {}).get(m, 5)
                        pond_actuales[m] = [col_p1, col_p2, col_p3][idx_p % 3].slider(f"[{sr}] {m}", 1, 10, int(val_previo), key=f"pond_{jugador_seleccionado_pond}_{m}")
                        idx_p += 1
            
            notas_part_j = st.text_area(f"Notas específicas de {jugador_seleccionado_pond} en este partido", key=f"notas_part_{jugador_seleccionado_pond}")
            
            if st.button("➕ Guardar ponderación de este jugador"):
                proms = {}
                for sr, mets in sub_roles_pos.items():
                    proms[sr] = sum(pond_actuales[m] for m in mets) / len(mets)
                rol_calc = max(proms, key=proms.get)
                pond_actuales["Rol_Calculado"] = rol_calc
                
                val_media_calc = round(sum(v for k, v in pond_actuales.items() if k != "Rol_Calculado") / (len(pond_actuales)-1), 1)
                
                st.session_state.dict_ponderacion_partido[jugador_seleccionado_pond] = {
                    "metricas": pond_actuales,
                    "valoracion": val_media_calc,
                    "rol": rol_calc,
                    "notas": notas_part_j,
                    "posicion": pos_j,
                    "edad": fila_j['Edad'],
                    "lateralidad": fila_j['Lateralidad']
                }
                st.success(f"✅ ¡Ponderación guardada temporalmente para **{jugador_seleccionado_pond}** (Media: {val_media_calc} | Rol: {rol_calc})!")

        st.markdown("---")
        if st.button("💾 Guardar informe global de partido y suscribir todo", type="primary"):
            if not eq_local or not eq_visitante:
                st.error("⚠️ Debes introducir el nombre de ambos equipos.")
            else:
                df_db = pd.read_csv(ARCHIVO_INFORMES, encoding='utf-8') if os.path.exists(ARCHIVO_INFORMES) else pd.DataFrame(columns=COLUMNAS_BASE)
                registros_nuevos = []
                
                for _, row in edit_l_inf.iterrows():
                    j_nom = str(row["Jugador"]).strip()
                    if j_nom != "" and not j_nom.startswith("Titular ") and not j_nom.startswith("Suplente "):
                        if j_nom in st.session_state.dict_ponderacion_partido:
                            datos_pond = st.session_state.dict_ponderacion_partido[j_nom]
                            val_g = datos_pond["valoracion"]
                            coms = datos_pond["notas"]
                            json_m = json.dumps(datos_pond["metricas"])
                        else:
                            val_g = 5.0
                            coms = "Evaluado en partido"
                            json_m = "{}"
                        
                        mask = df_db['Jugador'].str.strip().str.lower() == j_nom.lower()
                        if not df_db.empty and mask.sum() > 0:
                            df_db.loc[mask, ['Fecha', 'Equipo', 'Categoria', 'Edad', 'Lateralidad', 'Posicion', 'Partido', 'Valoracion', 'Comentarios', 'Metricas_Rol', 'Ojeador']] = [
                                fecha_partido, eq_local, cat_partido, row["Edad"], row["Lateralidad"], row["Posicion"], lugar_partido, val_g, coms, json_m, ojeador_partido
                            ]
                        else:
                            registros_nuevos.append([fecha_partido, j_nom, eq_local, cat_partido, row["Edad"], row["Lateralidad"], row["Posicion"], lugar_partido, val_g, "-", "-", coms, json_m, "", ojeador_partido])

                for _, row in edit_v_inf.iterrows():
                    j_nom = str(row["Jugador"]).strip()
                    if j_nom != "" and not j_nom.startswith("Titular ") and not j_nom.startswith("Suplente "):
                        if j_nom in st.session_state.dict_ponderacion_partido:
                            datos_pond = st.session_state.dict_ponderacion_partido[j_nom]
                            val_g = datos_pond["valoracion"]
                            coms = datos_pond["notas"]
                            json_m = json.dumps(datos_pond["metricas"])
                        else:
                            val_g = 5.0
                            coms = "Evaluado en partido"
                            json_m = "{}"
                        
                        mask = df_db['Jugador'].str.strip().str.lower() == j_nom.lower()
                        if not df_db.empty and mask.sum() > 0:
                            df_db.loc[mask, ['Fecha', 'Equipo', 'Categoria', 'Edad', 'Lateralidad', 'Posicion', 'Partido', 'Valoracion', 'Comentarios', 'Metricas_Rol', 'Ojeador']] = [
                                fecha_partido, eq_visitante, cat_partido, row["Edad"], row["Lateralidad"], row["Posicion"], lugar_partido, val_g, coms, json_m, ojeador_partido
                            ]
                        else:
                            registros_nuevos.append([fecha_partido, j_nom, eq_visitante, cat_partido, row["Edad"], row["Lateralidad"], row["Posicion"], lugar_partido, val_g, "-", "-", coms, json_m, "", ojeador_partido])

                if registros_nuevos:
                    df_add = pd.DataFrame(registros_nuevos, columns=COLUMNAS_BASE)
                    df_db = pd.concat([df_db, df_add], ignore_index=True)
                
                df_db.to_csv(ARCHIVO_INFORMES, index=False, encoding='utf-8')
                st.success("✅ ¡Informe de partido guardado y base de datos suscrita/actualizada correctamente!")

    with tab_once_ideal:
        st.header("🏆 Onces Ideales por Categoría (Campograma Táctico)")
        st.info("Selecciona la categoría, la metodología de juego y el sistema táctico para generar un once ideal visual con los mejores jugadores evaluados en tus informes de campo.")
        
        if os.path.exists(ARCHIVO_INFORMES):
            df_bd = pd.read_csv(ARCHIVO_INFORMES, encoding='utf-8')
            
            if not df_bd.empty:
                col_c1, col_c2, col_c3 = st.columns(3)
                cat_once = col_c1.selectbox("Categoría:", df_bd['Categoria'].unique(), key="cat_once_campo")
                metodologia_campo = col_c2.selectbox("Metodología:", ["Juego de posición (posesión)", "Bloque bajo y contraataque", "Presión alta y transiciones rápidas"], key="met_campo")
                sistema_campo = col_c3.selectbox("Sistema táctico:", ["1-4-3-3", "1-4-4-2", "1-4-2-3-1", "1-5-3-2", "1-3-4-3"], key="sis_campo")
                
                df_once_cat = df_bd[df_bd['Categoria'] == cat_once].copy()
                
                if df_once_cat.empty:
                    st.warning("No hay jugadores evaluados en esta categoría.")
                else:
                    estructuras_campo = {
                        "1-4-3-3": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'LI', 'rol': 'Lateral', 'x': 15, 'y': 25, 'lado': 'Zurdo'}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 35, 'y': 22, 'lado': None}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 65, 'y': 22, 'lado': None}, {'id': 'LD', 'rol': 'Lateral', 'x': 85, 'y': 25, 'lado': 'Diestro'}, {'id': 'MCD', 'rol': 'Mediocentro', 'x': 50, 'y': 40, 'lado': None}, {'id': 'MC (I)', 'rol': 'Mediocentro', 'x': 30, 'y': 55, 'lado': None}, {'id': 'MC (D)', 'rol': 'Mediocentro', 'x': 70, 'y': 55, 'lado': None}, {'id': 'EI', 'rol': 'Extremo', 'x': 20, 'y': 78, 'lado': 'Zurdo'}, {'id': 'ED', 'rol': 'Extremo', 'x': 80, 'y': 78, 'lado': 'Diestro'}, {'id': 'DC', 'rol': 'Delantero', 'x': 50, 'y': 85, 'lado': None}],
                        "1-4-4-2": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'LI', 'rol': 'Lateral', 'x': 15, 'y': 25, 'lado': 'Zurdo'}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 35, 'y': 22, 'lado': None}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 65, 'y': 22, 'lado': None}, {'id': 'LD', 'rol': 'Lateral', 'x': 85, 'y': 25, 'lado': 'Diestro'}, {'id': 'MI', 'rol': 'Extremo', 'x': 15, 'y': 55, 'lado': 'Zurdo'}, {'id': 'MC (I)', 'rol': 'Mediocentro', 'x': 35, 'y': 50, 'lado': None}, {'id': 'MC (D)', 'rol': 'Mediocentro', 'x': 65, 'y': 50, 'lado': None}, {'id': 'MD', 'rol': 'Extremo', 'x': 85, 'y': 55, 'lado': 'Diestro'}, {'id': 'DC (I)', 'rol': 'Delantero', 'x': 35, 'y': 82, 'lado': None}, {'id': 'DC (D)', 'rol': 'Delantero', 'x': 65, 'y': 82, 'lado': None}],
                        "1-4-2-3-1": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'LI', 'rol': 'Lateral', 'x': 15, 'y': 25, 'lado': 'Zurdo'}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 35, 'y': 22, 'lado': None}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 65, 'y': 22, 'lado': None}, {'id': 'LD', 'rol': 'Lateral', 'x': 85, 'y': 25, 'lado': 'Diestro'}, {'id': 'MCD (I)', 'rol': 'Mediocentro', 'x': 35, 'y': 45, 'lado': None}, {'id': 'MCD (D)', 'rol': 'Mediocentro', 'x': 65, 'y': 45, 'lado': None}, {'id': 'EI', 'rol': 'Extremo', 'x': 20, 'y': 68, 'lado': 'Zurdo'}, {'id': 'MCO', 'rol': 'Mediocentro', 'x': 50, 'y': 65, 'lado': None}, {'id': 'ED', 'rol': 'Extremo', 'x': 80, 'y': 68, 'lado': 'Diestro'}, {'id': 'DC', 'rol': 'Delantero', 'x': 50, 'y': 85, 'lado': None}],
                        "1-5-3-2": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'CAI', 'rol': 'Lateral', 'x': 12, 'y': 35, 'lado': 'Zurdo'}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 30, 'y': 22, 'lado': None}, {'id': 'DFC (C)', 'rol': 'Central', 'x': 50, 'y': 19, 'lado': None}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 70, 'y': 22, 'lado': None}, {'id': 'CAD', 'rol': 'Lateral', 'x': 88, 'y': 35, 'lado': 'Diestro'}, {'id': 'MC (I)', 'rol': 'Mediocentro', 'x': 30, 'y': 55, 'lado': None}, {'id': 'MCD', 'rol': 'Mediocentro', 'x': 50, 'y': 48, 'lado': None}, {'id': 'MC (D)', 'rol': 'Mediocentro', 'x': 70, 'y': 55, 'lado': None}, {'id': 'DC (I)', 'rol': 'Delantero', 'x': 35, 'y': 82, 'lado': None}, {'id': 'DC (D)', 'rol': 'Delantero', 'x': 65, 'y': 82, 'lado': None}],
                        "1-3-4-3": [{'id': 'POR', 'rol': 'Portero', 'x': 50, 'y': 8, 'lado': None}, {'id': 'DFC (I)', 'rol': 'Central', 'x': 25, 'y': 22, 'lado': None}, {'id': 'DFC (C)', 'rol': 'Central', 'x': 50, 'y': 19, 'lado': None}, {'id': 'DFC (D)', 'rol': 'Central', 'x': 75, 'y': 22, 'lado': None}, {'id': 'MI / CAI', 'rol': 'Lateral', 'x': 15, 'y': 50, 'lado': 'Zurdo'}, {'id': 'MC (I)', 'rol': 'Mediocentro', 'x': 35, 'y': 45, 'lado': None}, {'id': 'MC (D)', 'rol': 'Mediocentro', 'x': 65, 'y': 45, 'lado': None}, {'id': 'MD / CAD', 'rol': 'Lateral', 'x': 85, 'y': 50, 'lado': 'Diestro'}, {'id': 'EI', 'rol': 'Extremo', 'x': 25, 'y': 78, 'lado': 'Zurdo'}, {'id': 'ED', 'rol': 'Extremo', 'x': 75, 'y': 78, 'lado': 'Diestro'}, {'id': 'DC', 'rol': 'Delantero', 'x': 50, 'y': 85, 'lado': None}]
                    }

                    selected_players_field = []
                    formation_field_data = []

                    for pos_data in estructuras_campo[sistema_campo]:
                        rol_necesario = pos_data['rol']
                        df_pos_cand = df_once_cat[df_once_cat['Posicion'] == rol_necesario].copy()
                        df_pos_cand = df_pos_cand[~df_pos_cand['Jugador'].isin(selected_players_field)]
                        
                        if pos_data.get('lado') and 'Lateralidad' in df_pos_cand.columns:
                            lado_req = pos_data['lado']
                            df_ideal_lado = df_pos_cand[df_pos_cand['Lateralidad'].isin([lado_req, 'Ambidiestro'])]
                            if not df_ideal_lado.empty:
                                df_pos_cand = pd.concat([df_ideal_lado, df_pos_cand[~df_pos_cand['Jugador'].isin(df_ideal_lado['Jugador'])]])

                        df_pos_cand = df_pos_cand.sort_values(by="Valoracion", ascending=False)
                        
                        p1 = df_pos_cand.iloc[0]['Jugador'] if len(df_pos_cand) > 0 else "N/D"
                        img_p1 = df_pos_cand.iloc[0].get('Imagen', '') if len(df_pos_cand) > 0 else ''
                        p2 = df_pos_cand.iloc[1]['Jugador'] if len(df_pos_cand) > 1 else "N/D"
                        p3 = df_pos_cand.iloc[2]['Jugador'] if len(df_pos_cand) > 2 else "N/D"
                        
                        if p1 != "N/D": selected_players_field.append(p1)
                        
                        img_url_final = img_p1 if pd.notna(img_p1) and str(img_p1).startswith("http") else f"https://ui-avatars.com/api/?name={urllib.parse.quote(p1)}&background=1e3a8a&color=fff&size=128&bold=true"
                        
                        formation_field_data.append({
                            'id': pos_data['id'], 'x': pos_data['x'], 'y': pos_data['y'],
                            'top1': p1, 'top2': p2, 'top3': p3, 'image': img_url_final if p1 != "N/D" else None
                        })

                    fig_pitch_c = go.Figure()
                    fig_pitch_c.update_layout(xaxis=dict(range=[0, 100], visible=False, fixedrange=True), yaxis=dict(range=[0, 100], visible=False, fixedrange=True), plot_bgcolor='#1e3a8a', margin=dict(l=0, r=0, t=0, b=0), height=700)
                    fig_pitch_c.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, line=dict(color="#fde047", width=2), layer="below")
                    fig_pitch_c.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line=dict(color="#fde047", width=2), layer="below")
                    fig_pitch_c.add_shape(type="circle", x0=40, y0=40, x1=60, y1=60, line=dict(color="#fde047", width=2), layer="below")
                    fig_pitch_c.add_shape(type="rect", x0=20, y0=0, x1=80, y1=18, line=dict(color="#fde047", width=2), layer="below")
                    fig_pitch_c.add_shape(type="rect", x0=35, y0=0, x1=65, y1=6, line=dict(color="#fde047", width=2), layer="below")
                    fig_pitch_c.add_shape(type="rect", x0=20, y0=82, x1=80, y1=100, line=dict(color="#fde047", width=2), layer="below")
                    fig_pitch_c.add_shape(type="rect", x0=35, y0=94, x1=65, y1=100, line=dict(color="#fde047", width=2), layer="below")

                    for item in formation_field_data:
                        if item['image']:
                            fig_pitch_c.add_layout_image(dict(source=item['image'], xref="x", yref="y", x=item['x'], y=item['y'], sizex=12, sizey=12, xanchor="center", yanchor="middle", layer="above"))

                    x_pts_c, y_pts_c, texts_c, hover_c = [], [], [], []
                    for item in formation_field_data:
                        x_pts_c.append(item['x']); y_pts_c.append(item['y'])
                        texts_c.append(item['top1'])
                        hover_c.append(f"<b>{item['id']}</b><br>1️⃣ {item['top1']}<br>2️⃣ {item['top2']}<br>3️⃣ {item['top3']}")

                    fig_pitch_c.add_trace(go.Scatter(x=x_pts_c, y=[y - 8 for y in y_pts_c], mode='text', text=texts_c, textfont=dict(color='#fde047', size=12, family="Arial Black"), hoverinfo='none'))
                    fig_pitch_c.add_trace(go.Scatter(x=x_pts_c, y=y_pts_c, mode='markers', marker=dict(size=45, color='rgba(0,0,0,0)'), hoverinfo='text', hovertext=hover_c))
                    st.plotly_chart(fig_pitch_c, use_container_width=True, config={'displayModeBar': False})

            else:
                st.info("Aún no tienes informes para generar el once ideal.")
        else:
            st.info("Aún no tienes informes para generar el once ideal.")

    with tab_mis_informes:
        st.header("📂 Base de Datos General de Informes")
        
        if os.path.exists(ARCHIVO_INFORMES):
            df_informes_propios = pd.read_csv(ARCHIVO_INFORMES, encoding='utf-8')
            
            if df_informes_propios.empty:
                st.info("Aún no tienes ningún informe guardado.")
            else:
                col_f1, col_f2, col_f3 = st.columns(3)
                f_cat_inf = col_f1.multiselect("Categoría:", df_informes_propios['Categoria'].unique(), key="f_cat_mis")
                f_pos_inf = col_f2.multiselect("Posición:", df_informes_propios['Posicion'].unique(), key="f_pos_mis")
                partidos_disponibles = [p for p in df_informes_propios['Partido'].unique() if pd.notna(p) and p != "-"]
                f_part_inf = col_f3.multiselect("Partido visualizado / ubicación:", partidos_disponibles)

                df_inf_filt = df_informes_propios.copy()
                if f_cat_inf: df_inf_filt = df_inf_filt[df_inf_filt['Categoria'].isin(f_cat_inf)]
                if f_pos_inf: df_inf_filt = df_inf_filt[df_inf_filt['Posicion'].isin(f_pos_inf)]
                if f_part_inf: df_inf_filt = df_inf_filt[df_inf_filt['Partido'].isin(f_part_inf)]

                st.dataframe(df_inf_filt[['Fecha', 'Jugador', 'Equipo', 'Categoria', 'Posicion', 'Partido', 'Valoracion', 'Ojeador']], use_container_width=True)

                st.markdown("---")
                st.markdown("### 📖 Historial de Partidos Vistos, Ponderación de Métricas y Valor Global")
                opciones_jugadores_propios = [""] + sorted(df_inf_filt['Jugador'].unique().tolist())
                jugador_leer = st.selectbox("Selecciona un jugador:", opciones_jugadores_propios, key="sel_leer_j")
                
                if jugador_leer != "":
                    registros_jugador = df_informes_propios[df_informes_propios['Jugador'].str.strip().str.lower() == jugador_leer.strip().lower()]
                    
                    valoracion_global_jugador = round(registros_jugador['Valoracion'].mean(), 1)
                    
                    col_txt, col_radar = st.columns([1.2, 1])
                    with col_txt:
                        img_rep = registros_jugador.iloc[0].get('Imagen', '')
                        if pd.notna(img_rep) and str(img_rep).startswith("http"):
                            st.markdown(f'<img src="{img_rep}" class="profile-face" style="margin-bottom: 15px;">', unsafe_allow_html=True)

                        st.markdown(f"## {jugador_leer}")
                        st.markdown(f"**Equipo actual:** {registros_jugador.iloc[0]['Equipo']} &nbsp;&nbsp;|&nbsp;&nbsp; **Categoría:** {registros_jugador.iloc[0]['Categoria']}")
                        st.markdown(f"**Posición:** {registros_jugador.iloc[0]['Posicion']} &nbsp;&nbsp;|&nbsp;&nbsp; **Edad:** {registros_jugador.iloc[0].get('Edad', '-')} años &nbsp;&nbsp;|&nbsp;&nbsp; **Lateralidad:** {registros_jugador.iloc[0].get('Lateralidad', '-')}")
                        st.markdown(f"**⭐ Valoración global (media de todos los partidos vistos):** {valoracion_global_jugador}/10.0")
                        st.markdown(f"**👁️ Ojeador responsable:** {registros_jugador.iloc[0].get('Ojeador', 'Dani Rodríguez')}")
                        st.markdown("---")
                        
                        st.markdown("#### 🏟️ Historial de Partidos Visualizados")
                        for idx_r, row_r in registros_jugador.iterrows():
                            with st.expander(f"📅 {row_r['Fecha']} | Partido: {row_r.get('Partido', 'N/D')} (Nota: {row_r['Valoracion']})"):
                                st.write(f"**Ojeador:** {row_r.get('Ojeador', 'Dani Rodríguez')}")
                                st.write(f"**Comentarios / notas:** {row_r.get('Comentarios', '-')}")
                                
                                modo_edicion_met = st.toggle(f"✏️ Editar ponderación de métricas de este partido ({row_r.get('Partido', 'Partido')})", key=f"toggle_ed_{idx_r}")
                                
                                if modo_edicion_met:
                                    try:
                                        met_json_actual = json.loads(row_r.get('Metricas_Rol', '{}'))
                                    except:
                                        met_json_actual = {}
                                    
                                    pos_reg = row_r['Posicion']
                                    perfiles_pos_dic = PERFILES_DICT.get(pos_reg, {})
                                    
                                    with st.form(f"form_edit_met_{idx_r}"):
                                        st.write("Ajusta las ponderaciones (métricas). La valoración global se recalculará automáticamente al guardar:")
                                        nuevas_notas_met = {}
                                        for sr_ed, mets_ed in perfiles_pos_dic.items():
                                            for m_ed in mets_ed:
                                                val_antiguo = met_json_actual.get(m_ed, 5)
                                                nuevas_notas_met[m_ed] = st.slider(f"[{sr_ed}] {m_ed}", 1, 10, int(val_antiguo), key=f"slider_ed_{idx_r}_{m_ed}")
                                        
                                        nueva_nota_com = st.text_area("Comentarios de este partido", value=str(row_r.get('Comentarios', '')), key=f"com_ed_{idx_r}")
                                        
                                        btn_act_met = st.form_submit_button("💾 Recalcular y guardar ponderación")
                                        if btn_act_met:
                                            proms_ed = {}
                                            for sr_ed, mets_ed in perfiles_pos_dic.items():
                                                proms_ed[sr_ed] = sum(nuevas_notas_met[m_ed] for m_ed in mets_ed) / len(mets_ed)
                                            rol_nuevo_calc = max(proms_ed, key=proms_ed.get)
                                            nuevas_notas_met["Rol_Calculado"] = rol_nuevo_calc
                                            
                                            nueva_val_media = round(sum(v for k, v in nuevas_notas_met.items() if k != "Rol_Calculado") / (len(nuevas_notas_met)-1), 1)
                                            
                                            df_informes_propios.loc[idx_r, ['Valoracion', 'Comentarios', 'Metricas_Rol']] = [
                                                nueva_val_media, nueva_nota_com, json.dumps(nuevas_notas_met)
                                            ]
                                            df_informes_propios.to_csv(ARCHIVO_INFORMES, index=False, encoding='utf-8')
                                            st.success("✅ ¡Ponderación y nota actualizada con éxito!")
                                            st.rerun()

                    with col_radar:
                        reg_principal = registros_jugador.iloc[-1]
                        if 'Metricas_Rol' in reg_principal and pd.notna(reg_principal['Metricas_Rol']) and str(reg_principal['Metricas_Rol']).strip() != "":
                            try:
                                datos_met = json.loads(reg_principal['Metricas_Rol'])
                                if datos_met:
                                    rol_final = datos_met.pop("Rol_Calculado", "Desconocido")
                                    st.markdown(f"### 🎯 Perfil asignado: **{rol_final}**")
                                    etiquetas = list(datos_met.keys())
                                    valores = list(datos_met.values())
                                    if etiquetas:
                                        fig = go.Figure()
                                        fig.add_trace(go.Scatterpolar(r=valores, theta=etiquetas, fill='toself', name=rol_final, line_color='#eab308'))
                                        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False, margin=dict(l=40, r=40, t=20, b=20))
                                        st.plotly_chart(fig, use_container_width=True)
                            except Exception: pass
                                    
                        st.markdown("---")
        else:
            st.info("Aún no tienes ningún informe guardado.")