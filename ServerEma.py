import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Campeonato - Otro Grupo",
    page_icon="🏎️",
    layout="wide"
)

# Nombre de tu nuevo archivo Excel
ARCHIVO_EXCEL = "Server Ema.xlsx"  # Cambia esto por el nombre real de tu archivo

# Funciones auxiliares de conversión de tiempos
def tiempo_a_segundos(t_val):
    if pd.isna(t_val) or t_val is None:
        return None
    if isinstance(t_val, (int, float)):
        return float(t_val)
    
    t_str = str(t_val).strip()
    try:
        if ":" in t_str:
            partes = t_str.replace(",", ".").split(":")
            minutos = float(partes[0])
            segundos = float(partes[1])
            return (minutos * 60) + segundos
        else:
            return float(t_str.replace(",", "."))
    except:
        return None

def segundos_a_tiempo(segundos):
    if segundos is None or pd.isna(segundos):
        return "-"
    m = int(segundos // 60)
    s = segundos % 60
    if m > 0:
        return f"{m:02d}:{s:06.3f}".replace(".", ",")
    else:
        return f"{s:06.3f}".replace(".", ",")

def diferencia_a_str(dif_seg):
    if dif_seg is None or pd.isna(dif_seg):
        return ""
    if abs(dif_seg) < 0.001:
        return "Líder"
    return f"+{dif_seg:.3f}s".replace(".", ",")

# Menú de Navegación Lateral
st.sidebar.title("🏁 Menú de Navegación")
opcion = st.sidebar.selectbox(
    "Selecciona una sección:",
    ["Records", "Comparativa de Tiempos"]
)

# -------------------------------------------------------------
# 1. RECORDS (Clasificación y Carrera en columnas)
# -------------------------------------------------------------
if opcion == "Records":
    st.markdown("### 🏆 Records de la Tanda")
    
    col_rec1, col_rec2 = st.columns(2)
    
    # --- COLUMNA IZQUIERDA: CLASIFICACIÓN (POLES) ---
    with col_rec1:
        st.markdown("""
        <div style="background-color: #161925; border: 1px solid #30363d; border-radius: 8px; padding: 10px 15px; margin-bottom: 15px;">
            <h4 style="color: #ffffff; margin: 0;">📜 Clasificación (Poles)</h4>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            df_clasif = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Clasificacion', header=None, engine='openpyxl')
            
            poles_data = []
            # Recorremos desde la fila 2 en adelante (asumiendo fila 0 título, fila 1 cabeceras 'Nombre'/'Tiempo')
            for r in range(2, len(df_clasif)):
                nombre_c = df_clasif.iloc[r, 0]
                t_c = df_clasif.iloc[r, 1]
                if pd.notna(nombre_c) and pd.notna(t_c):
                    t_seg_c = tiempo_a_segundos(t_c)
                    if t_seg_c and t_seg_c > 20:
                        poles_data.append({"Piloto": str(nombre_c).strip(), "MejorTiempo": t_seg_c})
            
            if poles_data:
                df_poles = pd.DataFrame(poles_data).sort_values(by="MejorTiempo").reset_index(drop=True)
                t_lider_c = df_poles.iloc[0]["MejorTiempo"]
                
                for idx, row in df_poles.iterrows():
                    pos = idx + 1
                    p_name = row["Piloto"]
                    t_str = segundos_a_tiempo(row["MejorTiempo"])
                    
                    if pos == 1:
                        badge = '<span style="color: #00e676; float: right; font-weight: bold; font-size: 13px;">Líder</span>'
                        border_color = "#00e676"
                    else:
                        diff = row["MejorTiempo"] - t_lider_c
                        badge = f'<span style="color: #ff9800; float: right; font-weight: bold; font-size: 13px;">+{diff:.3f}s</span>'
                        border_color = "#e10600"
                        
                    st.markdown(f"""
                    <div style="background-color: #161925; border-left: 5px solid {border_color}; border-radius: 6px; padding: 12px 15px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                        <b style="color: #ffffff; font-size: 15px;">#{pos} — {p_name}</b> {badge}<br>
                        <span style="color: #00e676; font-size: 14px; font-family: monospace;">⏱️ {t_str}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hay datos de clasificación.")
        except Exception as e:
            st.error(f"Error al leer Clasificación: {e}")

    # --- COLUMNA DERECHA: CARRERA ---
    with col_rec2:
        st.markdown("""
        <div style="background-color: #161925; border: 1px solid #30363d; border-radius: 8px; padding: 10px 15px; margin-bottom: 15px;">
            <h4 style="color: #ffffff; margin: 0;">📜 Carrera Record</h4>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            df_carrera_rec = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Carrera', header=None, engine='openpyxl')
            
            carrera_data = []
            max_cols_r = df_carrera_rec.shape[1]
            r_idx = 0
            while r_idx < max_cols_r:
                piloto_r = df_carrera_rec.iloc[0, r_idx]
                if pd.notna(piloto_r) and str(piloto_r).strip() != "":
                    nombre_r = str(piloto_r).strip()
                    tiempos_r = []
                    for r in range(2, len(df_carrera_rec)):
                        t_r = df_carrera_rec.iloc[r, r_idx + 1]
                        if pd.notna(t_r):
                            t_seg_r = tiempo_a_segundos(t_r)
                            if t_seg_r and t_seg_r > 20:
                                tiempos_r.append(t_seg_r)
                    if tiempos_r:
                        carrera_data.append({"Piloto": nombre_r, "MejorTiempo": min(tiempos_r)})
                r_idx += 3
            
            if carrera_data:
                df_carr = pd.DataFrame(carrera_data).sort_values(by="MejorTiempo").reset_index(drop=True)
                t_lider_r = df_carr.iloc[0]["MejorTiempo"]
                
                for idx, row in df_carr.iterrows():
                    pos = idx + 1
                    p_name = row["Piloto"]
                    t_str = segundos_a_tiempo(row["MejorTiempo"])
                    
                    if pos == 1:
                        badge = '<span style="color: #00e676; float: right; font-weight: bold; font-size: 13px;">Líder</span>'
                        border_color = "#00e676"
                    else:
                        diff = row["MejorTiempo"] - t_lider_r
                        badge = f'<span style="color: #ff9800; float: right; font-weight: bold; font-size: 13px;">+{diff:.3f}s</span>'
                        border_color = "#e10600"
                        
                    st.markdown(f"""
                    <div style="background-color: #161925; border-left: 5px solid {border_color}; border-radius: 6px; padding: 12px 15px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                        <b style="color: #ffffff; font-size: 15px;">#{pos} — {p_name}</b> {badge}<br>
                        <span style="color: #00e676; font-size: 14px; font-family: monospace;">⏱️ {t_str}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hay datos de carrera.")
        except Exception as e:
            st.error(f"Error al leer Carrera: {e}")

# -------------------------------------------------------------
# 2. COMPARATIVA DE TIERMPOS (CARRERA)
# -------------------------------------------------------------
elif opcion == "Comparativa de Tiempos":
    st.markdown("### 📈 Live Timing Pro — Análisis de Ritmo")

    try:
        df_carrera = pd.read_excel(ARCHIVO_EXCEL, sheet_name='Carrera', header=None, engine='openpyxl')
        
        datos_carrera = {}
        max_cols = df_carrera.shape[1]
        col_idx = 0
        
        while col_idx < max_cols:
            piloto = df_carrera.iloc[0, col_idx]
            if pd.notna(piloto) and str(piloto).strip() != "":
                piloto_nombre = str(piloto).strip()
                vueltas = []
                tiempos_seg = []
                
                for r in range(2, len(df_carrera)):
                    nro_vuelta = df_carrera.iloc[r, col_idx]
                    t_vuelta = df_carrera.iloc[r, col_idx + 1]
                    
                    if pd.notna(nro_vuelta) and pd.notna(t_vuelta):
                        t_seg = tiempo_a_segundos(t_vuelta)
                        if t_seg is not None and t_seg > 20:
                            vueltas.append(int(nro_vuelta))
                            tiempos_seg.append(t_seg)
                
                if vueltas:
                    datos_carrera[piloto_nombre] = pd.DataFrame({
                        "Vuelta": vueltas,
                        "Tiempo": tiempos_seg,
                        "Piloto": piloto_nombre
                    })
            col_idx += 3

        if datos_carrera:
            pilotos_disponibles = list(datos_carrera.keys())
            
            # Selector de 2 pilotos para comparar en tarjetas detalladas
            st.write("---")
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                p1_sel = st.selectbox("Piloto 1:", pilotos_disponibles, index=0)
            with col_sel2:
                p2_sel = st.selectbox("Piloto 2:", pilotos_disponibles, index=min(1, len(pilotos_disponibles)-1))

            if p1_sel and p2_sel:
                df1 = datos_carrera[p1_sel]
                df2 = datos_carrera[p2_sel]

                # Función auxiliar para calcular regularidad limpia
                def calcular_regularidad(df):
                    if len(df) <= 1:
                        return 0.0
                    t_best = df["Tiempo"].min()
                    df_limpio = df[df["Tiempo"] <= t_best * 1.35]
                    return df_limpio["Tiempo"].std() if len(df_limpio) > 1 else df["Tiempo"].std()

                # Métricas Piloto 1
                rec1 = df1["Tiempo"].min()
                prom1 = df1["Tiempo"].mean()
                reg1 = calcular_regularidad(df1)

                # Métricas Piloto 2
                rec2 = df2["Tiempo"].min()
                prom2 = df2["Tiempo"].mean()
                reg2 = calcular_regularidad(df2)

                diff_rec = rec2 - rec1
                diff_prom = prom2 - prom1

                col_card1, col_card2 = st.columns(2)
                
                with col_card1:
                    st.markdown(f"""
                    <div style="background-color: #161925; border: 1px solid #30363d; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                        <p style="color: #9fa6b2; font-size: 12px; margin: 0; text-transform: uppercase; letter-spacing: 1px;">🏁 Piloto 1</p>
                        <h3 style="color: #ffffff; margin: 5px 0 15px 0;">{p1_sel}</h3>
                        <p style="color: #9fa6b2; font-size: 14px; margin: 4px 0;">⏱️ Récord: <b style="color: #00e676;">{segundos_a_tiempo(rec1)}</b></p>
                        <p style="color: #9fa6b2; font-size: 14px; margin: 4px 0;">📊 Promedio: <b style="color: #38bdf8;">{segundos_a_tiempo(prom1)}</b></p>
                        <p style="color: #9fa6b2; font-size: 14px; margin: 4px 0;">📈 Regularidad: <b style="color: #e10600;">±{reg1:.3f}s</b></p>
                    </div>
                    """, unsafe_allow_html=True)

                with col_card2:
                    st.markdown(f"""
                    <div style="background-color: #161925; border: 1px solid #30363d; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                        <p style="color: #9fa6b2; font-size: 12px; margin: 0; text-transform: uppercase; letter-spacing: 1px;">🏁 Piloto 2</p>
                        <h3 style="color: #ffffff; margin: 5px 0 15px 0;">{p2_sel}</h3>
                        <p style="color: #9fa6b2; font-size: 14px; margin: 4px 0;">⏱️ Récord: <b style="color: #00e676;">{segundos_a_tiempo(rec2)}</b></p>
                        <p style="color: #9fa6b2; font-size: 14px; margin: 4px 0;">📊 Promedio: <b style="color: #38bdf8;">{segundos_a_tiempo(prom2)}</b></p>
                        <p style="color: #9fa6b2; font-size: 14px; margin: 4px 0;">📈 Regularidad: <b style="color: #e10600;">±{reg2:.3f}s</b></p>
                    </div>
                    """, unsafe_allow_html=True)

                v_rrap_txt = f"{p1_sel} ({diff_rec:+.3f}s vs {p2_sel})" if rec1 <= rec2 else f"{p2_sel} ({-diff_rec:+.3f}s vs {p1_sel})"
                v_glob_txt = f"{p1_sel} ({diff_prom:+.3f}s vs {p2_sel})" if prom1 <= prom2 else f"{p2_sel} ({-diff_prom:+.3f}s vs {p1_sel})"

                col_inf1, col_inf2 = st.columns(2)
                with col_inf1:
                    st.markdown(f"""
                    <div style="background-color: #11141d; border: 1px solid #30363d; border-radius: 8px; padding: 12px; text-align: center; margin-top: 10px;">
                        <span style="font-size: 12px; color: #9fa6b2;">⚡ VUELTA RÁPIDA DE LA TANDA</span><br>
                        <b style="color: #00e676; font-size: 15px;">🏆 {v_rrap_txt}</b>
                    </div>
                    """, unsafe_allow_html=True)
                with col_inf2:
                    st.markdown(f"""
                    <div style="background-color: #11141d; border: 1px solid #30363d; border-radius: 8px; padding: 12px; text-align: center; margin-top: 10px;">
                        <span style="font-size: 12px; color: #9fa6b2;">👑 LÍDER DE RITMO GLOBAL</span><br>
                        <b style="color: #38bdf8; font-size: 15px;">👑 {v_glob_txt}</b>
                    </div>
                    """, unsafe_allow_html=True)

            st.write("---")
            st.markdown("### 📈 Gráfico de Evolución de Ritmo")
            
            # Checkbox de filtrado de Pace Car / Vueltas lentas
            filtrar_pace_car = st.checkbox("🧹 Filtrar vueltas lentas / Pace Car")
            st.caption("💡 ¿Para qué sirve? Detecta y remueve vueltas con incidentes o Pace Car para hacer 'zoom' en el eje Y y analizar el ritmo limpio de carrera.")

            pilotos_seleccionados = st.multiselect(
                "Selecciona los pilotos a graficar:",
                options=pilotos_disponibles,
                default=pilotos_disponibles[:min(3, len(pilotos_disponibles))]
            )

            if pilotos_seleccionados:
                lista_dfs = []
                for p in pilotos_seleccionados:
                    df_p = datos_carrera[p].copy()
                    if filtrar_pace_car and len(df_p) > 0:
                        t_best = df_p["Tiempo"].min()
                        df_p = df_p[df_p["Tiempo"] <= t_best * 1.30]
                    
                    # Creamos una columna con el formato de tiempo legible para el gráfico
                    df_p["TiempoFormateado"] = df_p["Tiempo"].apply(segundos_a_tiempo)
                    lista_dfs.append(df_p)
                
                df_plot = pd.concat(lista_dfs)
                
                # Gráfico indicando que use la columna formateada en el hover
                fig = px.line(
                    df_plot,
                    x="Vuelta",
                    y="Tiempo",
                    color="Piloto",
                    markers=True,
                    hover_data={"Tiempo": False, "TiempoFormateado": True} # Oculta los segundos sucios y muestra el formato mm:ss,000
                )
                
                # Ajustes de diseño
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font_color="#4a4a4a",
                    margin=dict(l=40, r=40, t=40, b=40),
                    xaxis=dict(
                        showgrid=True, 
                        gridcolor="#a0a0a0",
                        tickmode='linear',
                        dtick=1,
                        title="Número de Vuelta"
                    ),
                    yaxis=dict(
                        showgrid=True, 
                        gridcolor="#a0a0a0",
                        title="Segundos de Carrera"
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                fig.update_traces(line=dict(width=2))
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ Selecciona al menos un piloto para ver el gráfico.")
        else:
            st.warning("⚠️ No se encontraron datos de carrera estructurados en columnas.")

    except Exception as e:
        st.error(f"❌ Error al procesar la solapa Carrera: {e}")
# -------------------------------------------------------------
# 3. ESTADÍSTICAS
# -------------------------------------------------------------
