import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
import re

# ==========================================
# 0. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Torneo TC2000",
    page_icon="🏎️",
    layout="wide"
)

# ==========================================
# 1. ESTILOS MODERNOS (F1/Motorsport TV Style)
# ==========================================
st.markdown("""
    <style>
    /* Eliminamos restricciones de ancho para que use toda la pantalla */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 95% !important;
    }
   
    [data-testid="stSidebar"] {
        background-color: #121620;
        border-right: 1px solid #1f293d;
    }
   
    /* Textos del sidebar en blanco brillante */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #ffffff !important;
    }

    /* Botonera moderna estilo tarjeta */
    div.stButton > button {
        width: 100%;
        background-color: #1a2233;
        color: #ffffff;
        border: 1px solid #2d3b55;
        border-radius: 8px;
        padding: 12px;
        font-weight: 600;
        text-align: left;
        transition: all 0.3s ease;
        margin-bottom: 6px;
    }
    div.stButton > button:hover {
        background-color: #e10600;
        border-color: #e10600;
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(225, 6, 0, 0.4);
    }

    /* Tarjetas estilo F1 */
    .tarjeta-simulacion-f1 {
        background-color: #161925; 
        border-left: 5px solid #e10600; 
        border-radius: 10px;
        padding: 18px; 
        margin-bottom: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .titulo-simulacion-f1 { margin: 0; font-size: 11px; color: #9fa6b2; text-transform: uppercase; font-weight: bold; letter-spacing: 1px; }
    .piloto-simulacion-f1 { margin: 0; padding: 4px 0; color: #ffffff; font-size: 26px; font-weight: bold; }
    .divisor-simulacion-f1 { margin: 8px 0; border-color: #2a2f45; }
    .bloque-valores-f1 { display: flex; justify-content: space-between; align-items: center; }
    .sub-metrica-f1 { text-align: left; }
    .sub-metrica-der-f1 { text-align: right; }
    .texto-gris-f1 { margin: 0; font-size: 12px; color: #9fa6b2; }
    .texto-blanco-bold-f1 { margin: 0; font-size: 20px; color: #ffffff; font-weight: bold; font-family: monospace; }
    .texto-rojo-bold-f1 { margin: 0; font-size: 15px; color: #e10600; font-weight: bold; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

# Nombre del archivo local
ARCHIVO_EXCEL = "Torneo MGE.xlsx"

# =========================================================================
# FUNCIONES AUXILIARES DE TIEMPOS
# =========================================================================

def tiempo_a_segundos(tiempo_str):
    try:
        if pd.isna(tiempo_str):
            return None
        
        if isinstance(tiempo_str, (datetime.time, datetime.datetime)):
            total_segundos = (tiempo_str.minute * 60) + tiempo_str.second + (tiempo_str.microsecond / 1000000.0)
            if total_segundos <= 5.0:
                return None
            return total_segundos
            
        t_str = str(tiempo_str).replace(',', '.').strip()
        
        if t_str.count(':') == 2:
            partes = t_str.split(':')
            t_str = f"{partes[1]}:{partes[2]}"
            
        if ':' in t_str:
            partes = t_str.split(':')
            minutos = float(partes[0])
            segundos = float(partes[1])
            if minutos == 0 and segundos <= 5.0:
                return None
            return (minutos * 60.0) + segundos
            
        num = float(t_str)
        if num <= 5.0:
            return None
        return num
    except:
        return None

def formato_diferencia(segundos):
    if segundos == 0:
        return "0.000"
    return f"+{segundos:.3f}"

def parse_tiempo_a_segundos(val):
    if pd.isna(val):
        return None
    try:
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip().replace(',', '.')
        if ":" in val_str:
            partes = val_str.split(":")
            return float(partes[0]) * 60 + float(partes[1])
        return float(val_str)
    except:
        return None

# =========================================================================
# PROCESADOR DINÁMICO DE DATOS
# =========================================================================

def procesar_hoja_dinamica(file_path, sheet_name):
    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='openpyxl')
    registros = []
    circuito_actual = "Desconocido"

    for row_idx in range(len(df_raw)):
        row_vals = df_raw.iloc[row_idx].dropna().tolist()
        
        if len(row_vals) == 1 and isinstance(row_vals[0], str):
            val = row_vals[0].strip()
            if not val.isdigit() and "PILOTO" not in val.upper() and ":" not in val:
                circuito_actual = val
                continue
        
        for col_idx in range(len(df_raw.columns) - 1):
            val_header = str(df_raw.iloc[row_idx, col_idx]).strip()
            
            if val_header and val_header.lower() != 'nan' and not val_header.isdigit() and val_header.upper() != 'PILOTO':
                for r in range(row_idx + 1, len(df_raw)):
                    vuelta_num = df_raw.iloc[r, col_idx]
                    tiempo_val = df_raw.iloc[r, col_idx + 1]
                    
                    if pd.notna(vuelta_num) and pd.notna(tiempo_val):
                        if str(vuelta_num).strip().isdigit():
                            registros.append({
                                'Circuito': circuito_actual,
                                'Piloto': val_header,
                                'Vuelta': int(vuelta_num),
                                'Tiempo': str(tiempo_val).strip()
                            })
                        else:
                            break
                    else:
                        break

    return pd.DataFrame(registros).drop_duplicates()

# =========================================================================
# CARGA Y PREPARACIÓN DE VARIABLES GLOBALES
# =========================================================================

opciones_fechas_combinadas = ["Campeonato Completo"]

if os.path.exists(ARCHIVO_EXCEL):
    try:
        xls = pd.ExcelFile(ARCHIVO_EXCEL, engine='openpyxl')
        hojas = xls.sheet_names
        
        df_datos = pd.read_excel(ARCHIVO_EXCEL, sheet_name='DATOS', engine='openpyxl') if 'DATOS' in hojas else pd.DataFrame()
        df_tiempos = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Carga Tiempos', engine='openpyxl') if 'Carga Tiempos' in hojas else pd.DataFrame()
        
        if 'Carga Tiempos' in hojas:
            df_crudo_aux = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Carga Tiempos', header=None, engine='openpyxl')
            columna_a_rellenada = df_crudo_aux.iloc[:, 0].ffill()
            circuitos_detectados = []
            for c in columna_a_rellenada.dropna().astype(str).str.strip():
                c_upper = c.upper()
                if c_upper not in [x.upper() for x in circuitos_detectados] and c != "" and "NAN" not in c_upper and not c_upper.startswith("FECHA"):
                    circuitos_detectados.append(c)
            
            for idx, nombre_circuito in enumerate(circuitos_detectados):
                opciones_fechas_combinadas.append(f"Fecha {idx + 1} - {nombre_circuito}")
    except Exception as e:
        df_datos = pd.DataFrame()
        df_tiempos = pd.DataFrame()
        opciones_fechas_combinadas = ["Campeonato Completo"] + [f"Fecha {i}" for i in range(1, 11)]
else:
    df_datos = pd.DataFrame()
    df_tiempos = pd.DataFrame()
    opciones_fechas_combinadas = ["Campeonato Completo"]

# ==========================================
# 2. MENÚ LATERAL MODERNIZADO
# ==========================================
st.sidebar.markdown("## 🏎️ Torneo TC2000")
st.sidebar.markdown("##### Campeonato Interno")
st.sidebar.markdown("---")

if 'pagina_activa' not in st.session_state:
    st.session_state['pagina_activa'] = "Resumen"

if st.sidebar.button("📊 Resumen General", use_container_width=True):
    st.session_state['pagina_activa'] = "Resumen"
if st.sidebar.button("⏱️ Comparativa de Tiempos", use_container_width=True):
    st.session_state['pagina_activa'] = "Comparativa de Tiempos"
if st.sidebar.button("⚖️ Lastre", use_container_width=True):
    st.session_state['pagina_activa'] = "Lastre"
if st.sidebar.button("⚔️ Duelo H2H", use_container_width=True):
    st.session_state['pagina_activa'] = "Duelo H2H"
if st.sidebar.button("🎮 Simulador de Campeonato", use_container_width=True):
    st.session_state['pagina_activa'] = "Simulador de Campeonato"
if st.sidebar.button("📈 Estadísticas", use_container_width=True):
    st.session_state['pagina_activa'] = "Estadisticas"

opcion = st.session_state['pagina_activa']
pilotos = ["Agus", "Pablo", "Juandi", "Eze"]

df_resumen = pd.DataFrame({
    "Piloto": pilotos,
    "Puntos": [0, 0, 0, 0],
    "Victorias": [0, 0, 0, 0],
    "Poles": [0, 0, 0, 0],
    "Lastre Actual (kg)": [0, 0, 0, 0]
})

# ==========================================
# 3. VISTA: RESUMEN GENERAL
# ==========================================
if opcion == "Resumen":
    st.title("📊 Resumen del Campeonato")
    st.write("Sincronizado con tu archivo local Torneo.xlsx")

    if os.path.exists(ARCHIVO_EXCEL):
        try:
            # 1. CARGA DE BASE DE DATOS Y FILTRADOS DE CONTROL
            df_puntos_graf = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Tabla Final', engine='openpyxl')
            df_puntos_graf.columns = [str(c).strip() for c in df_puntos_graf.columns]
            df_puntos_graf = df_puntos_graf.dropna(subset=["PILOTO"])

            df_hoja1_graf = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Hoja1', header=None, engine='openpyxl')
            columna_f_graf = df_hoja1_graf.iloc[:, 5].astype(str).str.strip().str.upper().str.replace("Ó", "O", regex=False)
            
            filas_totales_fecha = columna_f_graf[columna_f_graf == "TOTAL FECHA"].index.tolist()
            filas_lastre_acum = columna_f_graf[columna_f_graf == "LASTRE ACUMULADO"].index.tolist()
            filas_c1 = columna_f_graf[columna_f_graf == "C1"].index.tolist()
            filas_c2 = columna_f_graf[columna_f_graf == "C2"].index.tolist()
            filas_pole_hoja1 = columna_f_graf[columna_f_graf == "POLE"].index.tolist()
            
            indices_pilotos_graf = {"Agus": 6, "Pablo": 8, "Juandi": 10, "Eze": 12}
            pilotos_torneo = list(indices_pilotos_graf.keys())
            
            datos_evolucion_limpios = []
            puntos_acumulados_carrera = {p: 0.0 for p in indices_pilotos_graf.keys()}
            max_puntaje_detectado = 0.0
            ultima_fecha_con_datos = 0

            for idx, fila_total in enumerate(filas_totales_fecha):
                tiene_datos_esta_fecha = False
                for piloto, col_idx in indices_pilotos_graf.items():
                    val_puntos = df_hoja1_graf.iloc[fila_total, col_idx]
                    if pd.notna(val_puntos):
                        try:
                            if float(str(val_puntos).replace(',', '.', 1)) > 0:
                                tiene_datos_esta_fecha = True
                        except: pass
                if tiene_datos_esta_fecha:
                    ultima_fecha_con_datos = idx + 1

            fecha_seleccionada = st.selectbox("Seleccionar Fecha o Histórico:", opciones_fechas_combinadas)

            # --- FILTRADO DINÁMICO DE PUNTOS SEGÚN LA FECHA ELEGIDA ---
            if fecha_seleccionada == "Campeonato Completo":
                df_filtrado_resumen = df_puntos_graf[["PILOTO", "PTS"]].sort_values(by="PTS", ascending=False).reset_index(drop=True)
                df_filtrado_resumen.columns = ["Piloto", "Puntos"]
                titulo_grafico = "Puntos - Campeonato Completo"
            else:
                try:
                    coincidencias = re.findall(r'\d+', str(fecha_seleccionada))
                    numero_fecha_detectado = int(coincidencias[0]) - 1 if coincidencias else 0
                except:
                    numero_fecha_detectado = 0
                
                fila_total_bloque_hoja1 = filas_totales_fecha[numero_fecha_detectado] if numero_fecha_detectado < len(filas_totales_fecha) else filas_totales_fecha[-1]
                tabla_puntos_fecha_individual = []
                
                for piloto_n, col_idx in indices_pilotos_graf.items():
                    val_puntos_celda = df_hoja1_graf.iloc[fila_total_bloque_hoja1, col_idx]
                    try:
                        puntos_limpios_num = float(str(val_puntos_celda).replace(",", ".").strip())
                    except:
                        puntos_limpios_num = 0.0
                    tabla_puntos_fecha_individual.append({"Piloto": piloto_n, "Puntos": puntos_limpios_num})
                
                df_filtrado_resumen = pd.DataFrame(tabla_puntos_fecha_individual).sort_values(by="Puntos", ascending=False).reset_index(drop=True)
                titulo_grafico = f"Puntos Netos - {fecha_seleccionada}"

            # --- GRÁFICO DE DONA CON POSICIONES ---
            st.subheader(f"🎯 Distribución de Puntos y Posiciones ({fecha_seleccionada})")
            
            df_dona = df_filtrado_resumen.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
            
            etiquetas_con_pos = []
            for idx, row in df_dona.iterrows():
                pos = idx + 1
                simbolo_podio = "🥇" if pos == 1 else ("🥈" if pos == 2 else ("🥉" if pos == 3 else f"{pos}°"))
                etiquetas_con_pos.append(f"{simbolo_podio} {row['Piloto']}<br>({row['Puntos']:.2f} pts)")
            
            df_dona["EtiquetaDona"] = etiquetas_con_pos

            col_izq, col_centro, col_der = st.columns([0.2, 3.6, 0.2])
            with col_centro:
                fig_dona = px.pie(
                    df_dona,
                    names="EtiquetaDona",
                    values="Puntos",
                    hole=0.55,
                    template="plotly_dark",
                    color_discrete_sequence=["#e10600", "#00b0ff", "#ff9100", "#00e676"]
                )
                
                fig_dona.update_traces(
                    textinfo='label',
                    textposition='outside',
                    textfont=dict(size=15, color='white'),
                    marker=dict(line=dict(color='#0f111a', width=2))
                )
                
                fig_dona.update_layout(
                    plot_bgcolor="#161925",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=60, r=60, t=30, b=30),
                    height=420, showlegend=False
                )
                
                st.plotly_chart(fig_dona, use_container_width=True, key="resumen_dona_con_posiciones_grande")

            # --- EVOLUCIÓN TEMPORAL LÍNEAS ---
            for idx, fila_total in enumerate(filas_totales_fecha[:ultima_fecha_con_datos]):
                nombre_fecha_eje_x = f"Fecha {idx + 1}"
                try:
                    circuito_real = opciones_fechas_combinadas[idx + 1].split(" - ")[1]
                except:
                    circuito_real = f"Carrera {idx + 1}"
                
                for piloto, col_idx in indices_pilotos_graf.items():
                    val_puntos_fecha = df_hoja1_graf.iloc[fila_total, col_idx]
                    puntos_fecha_limpio = str(val_puntos_fecha).replace(',', '.', 1) if pd.notna(val_puntos_fecha) else "0.0"
                    try:
                        puntos_fecha = float(puntos_fecha_limpio)
                    except:
                        puntos_fecha = 0.0
                    
                    puntos_acumulados_carrera[piloto] += puntos_fecha
                    if puntos_acumulados_carrera[piloto] > max_puntaje_detectado:
                        max_puntaje_detectado = puntos_acumulados_carrera[piloto]
                    
                    pos_c1 = "-"
                    pos_c2 = "-"
                    if idx < len(filas_c1):
                        val_c1 = df_hoja1_graf.iloc[filas_c1[idx], col_idx]
                        if pd.notna(val_c1):
                            try: pos_c1 = f"P{int(float(str(val_c1).replace(',','.',1)))}"
                            except: pass
                    if idx < len(filas_c2):
                        val_c2 = df_hoja1_graf.iloc[filas_c2[idx], col_idx]
                        if pd.notna(val_c2):
                            try: pos_c2 = f"P{int(float(str(val_c2).replace(',','.',1)))}"
                            except: pass
                    
                    resultado_txt = f"{pos_c1} / {pos_c2}"

                    lastre_txt = "0 Kg"
                    if idx > 0 and idx - 1 < len(filas_lastre_acum):
                        fila_lastre_anterior = filas_lastre_acum[idx - 1]
                        val_lastre = df_hoja1_graf.iloc[fila_lastre_anterior, col_idx]
                        if pd.notna(val_lastre):
                            lastre_txt = f"{str(val_lastre).upper().replace('KG', '').strip()} Kg"
                    
                    datos_evolucion_limpios.append({
                        "Piloto": piloto, "Gran Premio": nombre_fecha_eje_x, "Puntos Acumulados": puntos_acumulados_carrera[piloto],
                        "Circuito": circuito_real, "Resultado": resultado_txt, "LastreInicial": lastre_txt
                    })

            if datos_evolucion_limpios:
                st.markdown("---")
                st.subheader("📈 Evolución del Campeonato y Lastre en Vivo")
                df_melted_evolucion = pd.DataFrame(datos_evolucion_limpios)
                fig_evolucion = px.line(
                    df_melted_evolucion, x="Gran Premio", y="Puntos Acumulados", color="Piloto",
                    template="plotly_dark", markers=True, custom_data=["Circuito", "Resultado", "LastreInicial", "Piloto"]
                )
                fig_evolucion.update_traces(
                    line=dict(width=3.5), marker=dict(size=8),
                    hovertemplate="<br><b>Piloto:</b> %{customdata[3]}<br>📍 <b>Circuito:</b> %{customdata[0]}<br>🏁 <b>Resultado (C1/C2):</b> %{customdata[1]}<br>⚖️ <b>Lastre Inicial:</b> %{customdata[2]} <br>🏆 <b>Puntos Acumulados:</b> %{y} pts<extra></extra>"
                )

                fig_evolucion.update_layout(hovermode="closest", plot_bgcolor="#161925", paper_bgcolor="#0f111a", margin=dict(l=20, r=20, t=20, b=20), height=400)
                st.plotly_chart(fig_evolucion, use_container_width=True, key="evolucion_lineas_resumen_fijo")

            # =========================================================================
            # 📊 SECCIÓN DE TELEMETRÍA (RITMO MEDIO + POLES EXTRAÍDAS DE HOJA1)
            # =========================================================================
            st.markdown("---")
            st.subheader("🏎️ Telemetría y Estadísticas de Rendimiento")
            
            posiciones_c1_por_piloto = {p: [] for p in pilotos_torneo}
            posiciones_c2_por_piloto = {p: [] for p in pilotos_torneo}
            poles_totales_por_piloto = {p: 0 for p in pilotos_torneo}
            efectividad_mangas_totales = {p: [] for p in pilotos_torneo}

            # 🛠️ 1. CONTEO DE POLES DESDE HOJA1
            for f_pole in filas_pole_hoja1:
                for piloto, col_idx in indices_pilotos_graf.items():
                    columna_puntos_idx = col_idx + 1
                    if columna_puntos_idx < df_hoja1_graf.shape[1]:
                        val_pole = df_hoja1_graf.iloc[f_pole, columna_puntos_idx]
                        if pd.notna(val_pole) and str(val_pole).strip() != "":
                            try:
                                texto_pole = str(val_pole).strip().upper().replace(",0", "").replace(".0", "")
                                if texto_pole in ["1", "POLE", "1°", "🥇"]:
                                    poles_totales_por_piloto[piloto] += 1
                            except: pass

            # 🛠️ 2. MOTOR HÍBRIDO AVANZADO
            try:
                df_tiempos_aux_resumen = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Carga Tiempos', header=None, engine='openpyxl')
                df_tiempos_aux_resumen.iloc[:, 0] = df_tiempos_aux_resumen.iloc[:, 0].ffill()
                col_sesiones_resumen = df_tiempos_aux_resumen.iloc[:, 1].astype(str).str.strip().str.upper().str.replace("Ó", "O", regex=False)
                indices_pilotos_fechas_resumen = {"Agus": 2, "Pablo": 3, "Juandi": 4, "Eze": 5}
                filas_clasif_tiempos = df_tiempos_aux_resumen[col_sesiones_resumen.str.contains("CLASIF|POLE", na=False)].index.tolist()

                for idx_est in range(len(filas_c1)):
                    poleman_fecha = None
                    if idx_est < len(filas_pole_hoja1):
                        f_pole_actual = filas_pole_hoja1[idx_est]
                        for piloto, col_idx in indices_pilotos_graf.items():
                            if col_idx + 1 < df_hoja1_graf.shape[1]:
                                val_p_celda = df_hoja1_graf.iloc[f_pole_actual, col_idx + 1]
                                if pd.notna(val_p_celda) and str(val_p_celda).strip() in ["1", "1.0"]:
                                    poleman_fecha = piloto
                                    break

                    grilla_c1_largada = {p: 4.0 for p in pilotos_torneo}
                    
                    if idx_est < len(filas_clasif_tiempos):
                        f_qualy = filas_clasif_tiempos[idx_est]
                        tiempos_fecha = {}
                        for p, col_idx in indices_pilotos_fechas_resumen.items():
                            seg = parse_tiempo_a_segundos(df_tiempos_aux_resumen.iloc[f_qualy, col_idx])
                            if seg is not None and seg > 30.0 and p != poleman_fecha:
                                tiempos_fecha[p] = seg
                        
                        if poleman_fecha:
                            grilla_c1_largada[poleman_fecha] = 1.0
                        
                        if tiempos_fecha:
                            pilotos_restantes_ordenados = sorted(tiempos_fecha, key=tiempos_fecha.get)
                            puesto_disponible = 2.0
                            for p_name in pilotos_restantes_ordenados:
                                grilla_c1_largada[p_name] = puesto_disponible
                                puesto_disponible += 1.0

                    for piloto, col_idx in indices_pilotos_graf.items():
                        val_c1 = df_hoja1_graf.iloc[filas_c1[idx_est], col_idx]
                        if pd.notna(val_c1):
                            try:
                                llegada_c1 = float(str(val_c1).upper().replace("P", "").strip())
                                if llegada_c1 > 0:
                                    posiciones_c1_por_piloto[piloto].append(llegada_c1)
                                    largada_c1 = grilla_c1_largada[piloto]
                                    
                                    if largada_c1 == llegada_c1:
                                        efec_c1 = 100.0
                                    elif largada_c1 > llegada_c1:
                                        efec_c1 = ((largada_c1 - llegada_c1) / (largada_c1 - 1.0)) * 100
                                    else:
                                        efec_c1 = (((4.0 - largada_c1) - (llegada_c1 - largada_c1)) / (4.0 - largada_c1)) * 100
                                    
                                    efectividad_mangas_totales[piloto].append(efec_c1)
                            except: pass

                    if idx_est < len(filas_c2):
                        for piloto, col_idx in indices_pilotos_graf.items():
                            val_c2 = df_hoja1_graf.iloc[filas_c2[idx_est], col_idx]
                            if pd.notna(val_c2):
                                try:
                                    llegada_c2 = float(str(val_c2).upper().replace("P", "").strip())
                                    if llegada_c2 > 0:
                                        posiciones_c2_por_piloto[piloto].append(llegada_c2)
                                        largada_c2 = 5.0 - grilla_c1_largada[piloto]
                                        
                                        if largada_c2 == llegada_c2:
                                            efec_c2 = 100.0
                                        elif largada_c2 > llegada_c2:
                                            efec_c2 = ((largada_c2 - llegada_c2) / (largada_c2 - 1.0)) * 100
                                        else:
                                            efec_c2 = (((4.0 - largada_c2) - (llegada_c2 - largada_c2)) / (4.0 - largada_c2)) * 100
                                        
                                        efectividad_mangas_totales[piloto].append(efec_c2)
                                except: pass
            except Exception as e_proc:
                st.warning(f"Aviso en cálculo de grillas: {e_proc}")

            # --- COMPILACIÓN DEL REPORTE FINAL ---
            reporte_tarjetas = []
            for piloto in pilotos_torneo:
                lista_c1 = posiciones_c1_por_piloto.get(piloto, [])
                lista_c2 = posiciones_c2_por_piloto.get(piloto, [])
                prom_c1 = sum(lista_c1) / len(lista_c1) if lista_c1 else 0.0
                prom_c2 = sum(lista_c2) / len(lista_c2) if lista_c2 else 0.0
                poles_reales = poles_totales_por_piloto.get(piloto, 0)
                
                lista_efec = efectividad_mangas_totales.get(piloto, [])
                prom_efec_carrera = sum(lista_efec) / len(lista_efec) if lista_efec else 0.0
                
                gps_disputados_c1 = len(lista_c1)
                porcentaje_efectividad_pole = (poles_reales / gps_disputados_c1) * 100 if gps_disputados_c1 > 0 else 0.0
                
                total_mangas = lista_c1 + lista_c2
                prom_general = sum(total_mangas) / len(total_mangas) if total_mangas else 0.0

                reporte_tarjetas.append({
                    "Piloto": piloto, "Promedio C1": prom_c1, "Promedio C2": prom_c2,
                    "Promedio General": prom_general, "Poles": poles_reales,
                    "Efectividad_Pole": porcentaje_efectividad_pole,
                    "Efectividad_Carrera": prom_efec_carrera,
                    "GPs": gps_disputados_c1
                })

            df_reporte_tarjetas = pd.DataFrame(reporte_tarjetas).sort_values(by="Promedio General")

            # --- RENDERIZADO DE LAS TARJETAS (ESTILO LASTRE) ---
            cols_grid = st.columns(4)
            for idx_c, row in df_reporte_tarjetas.reset_index(drop=True).iterrows():
                p_name = row["Piloto"]
                p_gen = f"P{row['Promedio General']:.1f}" if row["Promedio General"] > 0 else "-"
                p_c1 = f"P{row['Promedio C1']:.1f}" if row["Promedio C1"] > 0 else "-"
                p_c2 = f"P{row['Promedio C2']:.1f}" if row["Promedio C2"] > 0 else "-"
                p_poles = int(row["Poles"])
                p_efec_pole = row["Efectividad_Pole"]
                p_efec_carrera = row["Efectividad_Carrera"]
                p_gps = int(row["GPs"])
                
                color_borde_pista = "#00e676" if idx_c == 0 else "#e10600"
                
                with cols_grid[idx_c % 4]:
                    st.markdown(f"""
                        <div class="tarjeta-simulacion-f1" style="border-left: 5px solid {color_borde_pista};">
                            <p class="titulo-simulacion-f1">Rendimiento en Pista ({p_gps} GPs)</p>
                            <h3 class="piloto-simulacion-f1">{p_name}</h3>
                            <hr class="divisor-simulacion-f1">
                            <div class="bloque-valores-f1">
                                <div class="sub-metrica-f1">
                                    <p class="texto-gris-f1">Ritmo General:</p>
                                    <p class="texto-blanco-bold-f1" style="color: #00e676;">{p_gen}</p>
                                    <p class="texto-gris-f1" style="font-size:11px; margin-top:4px; color: #ff9100; font-weight:bold;">🏁 Efec. Race: {p_efec_carrera:.1f}%</p>
                                </div>
                                <div class="sub-metrica-der-f1">
                                    <p class="texto-gris-f1">Poles (Sábado):</p>
                                    <p class="texto-rojo-bold-f1" style="color: #00b0ff; font-size:22px;">🥇 {p_poles}</p>
                                    <p class="texto-gris-f1" style="font-size:11px; margin-top:4px; color: #9fa6b2;">⚡ Efec. Pole: {p_efec_pole:.1f}%</p>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            st.write("#### 📊 Tabla de Resumen Detallada")
            st.dataframe(
                df_reporte_tarjetas.assign(
                    **{
                        "Promedio General": lambda x: x["Promedio General"].apply(lambda v: f"P{v:.1f}" if v > 0 else "-"),
                        "Promedio C1": lambda x: x["Promedio C1"].apply(lambda v: f"P{v:.1f}" if v > 0 else "-"),
                        "Promedio C2": lambda x: x["Promedio C2"].apply(lambda v: f"P{v:.1f}" if v > 0 else "-"),
                        "Poles": lambda x: x["Poles"].apply(lambda v: f"🥇 {int(v)} Poles"),
                        "Efectividad_Pole": lambda x: x["Efectividad_Pole"].apply(lambda v: f"{v:.1f}%"),
                        "Efectividad_Carrera": lambda x: x["Efectividad_Carrera"].apply(lambda v: f"{v:.1f}%")
                    }
                ),
                use_container_width=True, hide_index=True
            )

            rey_pole = max(poles_totales_por_piloto, key=poles_totales_por_piloto.get)
            max_poles = poles_totales_por_piloto[rey_pole]
            if max_poles > 0:
                st.success(f"⏱️ **Rey de los Sábados:** El piloto con más Pole Positions es **{rey_pole}** con un total de **{max_poles} Poles**.")

        except Exception as e:
            st.error(f"Error procesando el archivo de Excel: {e}")
    else:
        st.error(f"No se encontró el archivo local '{ARCHIVO_EXCEL}'. Asegúrate de colocarlo en el directorio raíz.")

else:
    st.title(f"🛠️ {opcion}")
    st.info("Módulo en desarrollo o vista secundaria.")