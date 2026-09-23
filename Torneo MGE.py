import os
import json
import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio

# --- 1. CONFIGURACIÓN Y ESTILOS MODERNOS (F1/Motorsport TV Style) ---
st.set_page_config(page_title="Campeonato TC", layout="wide")

pio.templates.default = "plotly_dark"

st.markdown("""
    <style>
    /* Fondo general de la página blanco */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 95% !important;
    }
    
    .stApp {
        background-color: #ffffff;
        color: #111827;
    }
    
    /* Títulos principales fuera de contenedores en tono oscuro */
    h1, h2, h3 {
        color: #111827 !important;
    }
    
    [data-testid="stSidebar"] { 
        background-color: #121620; 
        border-right: 1px solid #1f293d;
    }
    
    /* Textos del sidebar en blanco brillante */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #ffffff !important;
    }

    /* Botonera moderna estilo tarjeta en sidebar */
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
    
    /* Selectores y campos de entrada en la barra lateral */
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        background-color: #1a2233;
        color: #ffffff;
        border-color: #2d3b55;
    }
    
    /* Subida de archivos (Uploader) en la sidebar */
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background-color: #1a2233;
        border: 1px dashed #2d3b55;
        border-radius: 8px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Campeonato TC")

# ==========================================
# 2. MENÚ LATERAL CON BOTONES NATIVOS
# ==========================================
st.sidebar.markdown("## 🏁 Campeonato TC")
st.sidebar.markdown("##### Campeonato Interno")
st.sidebar.markdown("---")

if 'pagina_activa' not in st.session_state:
    st.session_state['pagina_activa'] = "Resumen General"

if st.sidebar.button("📊 Resumen General", use_container_width=True):
    st.session_state['pagina_activa'] = "Resumen General"
    st.rerun()
if st.sidebar.button("⏱️ Comparativa de Tiempos", use_container_width=True):
    st.session_state['pagina_activa'] = "Comparativa de Tiempos"
    st.rerun()
if st.sidebar.button("⚖️ Lastre", use_container_width=True):
    st.session_state['pagina_activa'] = "Lastre"
    st.rerun()
if st.sidebar.button("⚔️ Duelo H2H", use_container_width=True):
    st.session_state['pagina_activa'] = "Duelo H2H"
    st.rerun()
if st.sidebar.button("🎮 Simulador de Campeonato", use_container_width=True):
    st.session_state['pagina_activa'] = "Simulador de Campeonato"
    st.rerun()
if st.sidebar.button("📈 Estadísticas", use_container_width=True):
    st.session_state['pagina_activa'] = "Estadísticas"
    st.rerun()

seccion_menu = st.session_state['pagina_activa']

# Obtiene la ruta absoluta de la carpeta donde se encuentra este archivo de script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARPETA_DATOS = os.path.join(BASE_DIR, "resultados_json")
CARPETA_VUELTAS = os.path.join(BASE_DIR, "resultados_json", "Vueltas")

for c in [CARPETA_DATOS, CARPETA_VUELTAS]:
    if not os.path.exists(c):
        os.makedirs(c)

def convertir_ms_a_minutos(ms):
    if not ms or ms <= 0:
        return "-"
    total_segundos = ms // 1000
    milisegundos = ms % 1000
    minutos = total_segundos // 60
    segundos = total_segundos % 60
    return f"{minutos:02d}:{segundos:02d},{milisegundos:03d}"

def limpiar_nombre_circuito(nombre_archivo):
    nombre = nombre_archivo.rsplit('.', 1)[0]
    nombre = nombre.replace("_", " ").replace("-", " ")
    palabras_a_remover = ["clasificacion", "clasificación", "quali", "sprint", "carrera", "race", "vueltas"]
    for palabra in palabras_a_remover:
        nombre = re.sub(rf'\b{palabra}\b', '', nombre, flags=re.IGNORECASE)
    nombre = re.sub(r'\b[qsr]\b', '', nombre, flags=re.IGNORECASE)
    return nombre.strip() if nombre.strip() else nombre_archivo.rsplit('.', 1)[0]

PUNTOS_CARRERA = {1: 30, 2: 24, 3: 19, 4: 15, 5: 12, 6: 10, 7: 8, 8: 6, 9: 5, 10: 4, 11: 2, 12: 1}
PUNTOS_SPRINT = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
PTS_POLE = 3
PTS_FL = 1

CAR_MODEL_MAPPING = {
    'asm_m42026': 'BMW',
    'asm_camaro2026': 'Camaro',
    'asm_mustang2026': 'Mustang',
    'asm_challenger2026': 'Challenger',
    'asm_torino2026': 'Torino',
    'asm_mercedes2026': 'Mercedes',
    'asm_camry2026': 'Camry'
}

def obtener_modelo_legible(raw_model, nombre_piloto=""):
    if not raw_model:
        return 'BMW'
    return CAR_MODEL_MAPPING.get(raw_model, 'BMW')

# ==========================================
# 3. PANEL DE ADMINISTRACIÓN Y CARGA PROTEGIDA
# ==========================================
st.sidebar.divider()
st.sidebar.subheader("🔒 Panel de Administración")

if "admin_autenticado" not in st.session_state:
    st.session_state["admin_autenticado"] = False

if not st.session_state["admin_autenticado"]:
    password_input = st.sidebar.text_input("Contraseña de Admin", type="password")
    if st.sidebar.button("Ingresar"):
        clave_correcta = st.secrets.get("ADMIN_PASSWORD", "1234")
        if password_input == clave_correcta:
            st.session_state["admin_autenticado"] = True
            st.sidebar.success("¡Acceso concedido!")
            st.rerun()
        else:
            st.sidebar.error("Contraseña incorrecta")
else:
    st.sidebar.success("Modo Administrador Activo")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["admin_autenticado"] = False
        st.rerun()

    st.sidebar.subheader("📁 Subir Nuevos Archivos")
    archivos_subidos = st.sidebar.file_uploader(
        "Sube archivos JSON (Clasificacion, Sprint, Carrera, Vueltas)",
        type=["json"],
        accept_multiple_files=True
    )

    if archivos_subidos:
        for archivo in archivos_subidos:
            nombre_lower = archivo.name.lower()
            if "vueltas" in nombre_lower:
                ruta_archivo = os.path.join(CARPETA_VUELTAS, archivo.name)
            else:
                ruta_archivo = os.path.join(CARPETA_DATOS, archivo.name)
                
            with open(ruta_archivo, "wb") as f:
                f.write(archivo.getbuffer())
                
        st.sidebar.success("¡Archivos guardados correctamente!")
        st.rerun()

archivos_datos = [os.path.join(CARPETA_DATOS, f) for f in os.listdir(CARPETA_DATOS) if f.endswith(".json")]
archivos_v = [os.path.join(CARPETA_VUELTAS, f) for f in os.listdir(CARPETA_VUELTAS) if f.endswith(".json")]

archivos_existentes = [os.path.basename(f) for f in archivos_datos + archivos_v]

if st.session_state["admin_autenticado"] and archivos_existentes:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗑️ Eliminar Archivos Previos")
    archivo_a_borrar = st.sidebar.selectbox("Selecciona archivo a borrar:", archivos_existentes, key="borrar_file")
    if st.sidebar.button("Eliminar archivo seleccionado"):
        ruta_a_borrar_datos = os.path.join(CARPETA_DATOS, archivo_a_borrar)
        ruta_a_borrar_vueltas = os.path.join(CARPETA_VUELTAS, archivo_a_borrar)
        
        if os.path.exists(ruta_a_borrar_datos):
            os.remove(ruta_a_borrar_datos)
        elif os.path.exists(ruta_a_borrar_vueltas):
            os.remove(ruta_a_borrar_vueltas)
            
        st.sidebar.success(f"Eliminado: {archivo_a_borrar}")
        st.rerun()

archivos_vueltas_json = [f for f in os.listdir(CARPETA_VUELTAS) if f.endswith(".json")]
if archivos_vueltas_json:
    ruta_vueltas_activo = os.path.join(CARPETA_VUELTAS, archivos_vueltas_json[0])
    df_global = pd.read_json(ruta_vueltas_activo)
else:
    df_global = pd.DataFrame()


archivos_json = [f for f in os.listdir(CARPETA_DATOS) if f.endswith(".json")]
archivos_json.sort(key=lambda x: os.path.getmtime(os.path.join(CARPETA_DATOS, x)))

if archivos_json:
    circuitos = {}
    for arj in archivos_json:
        circuito = limpiar_nombre_circuito(arj)
        if circuito not in circuitos:
            circuitos[circuito] = []
        circuitos[circuito].append(os.path.join(CARPETA_DATOS, arj))
        
    todos_los_resultados = []
    datos_comparativa_tiempos = {}
    datos_h2h_sesiones = {}
    pilotos_detectados = set()

    for circuito, rutas in circuitos.items():
        archivo_quali = None
        archivo_sprint = None
        archivo_carrera = None
        
        for ruta in rutas:
            nombre_archivo_lower = os.path.basename(ruta).lower()
            
            # Detección precisa adaptada a tus nombres de archivos actuales
            if "clasificacion" in nombre_archivo_lower or "clasificación" in nombre_archivo_lower or "quali" in nombre_archivo_lower:
                archivo_quali = ruta
            elif "sprint" in nombre_archivo_lower:
                archivo_sprint = ruta
            else:
                # Todo lo que no sea quali o sprint (como 'Balcarce.json' o 'San Luis.json') se asigna a carrera
                archivo_carrera = ruta

        if circuito not in datos_comparativa_tiempos:
            datos_comparativa_tiempos[circuito] = {}
        if circuito not in datos_h2h_sesiones:
            datos_h2h_sesiones[circuito] = {}

        poleman = None
        lista_q = []
        if archivo_quali:
            try:
                with open(archivo_quali, "r", encoding="utf-8") as f:
                    datos_q = json.load(f)
                car_models_by_id = {car.get('CarId'): car.get('Model') for car in datos_q.get('Cars', []) if 'CarId' in car and 'Model' in car}
                res_q = datos_q.get("Result", []) or datos_q.get("Leaderboard", []) or datos_q.get("Cars", [])
                for item in res_q:
                    driver_info = item.get("Driver", {})
                    p_nombre = driver_info.get("Name", "").strip() if isinstance(driver_info, dict) else ""
                    if not p_nombre:
                        p_nombre = item.get("DriverName", "").strip()
                    car_id = item.get("CarId")
                    raw_modelo = item.get("Model", "") or item.get("CarModel", "") or car_models_by_id.get(car_id, "")
                    modelo = obtener_modelo_legible(raw_modelo, p_nombre)
                    if not p_nombre or "pacecar" in modelo.lower():
                        continue
                    pilotos_detectados.add(p_nombre)
                    best_l = item.get("BestLap", 0)
                    if best_l > 0:
                        lista_q.append({"Piloto": p_nombre, "_BestLap": int(best_l)})
            except Exception as e:
                st.error(f"Error al leer quali de {circuito}: {e}")

        if lista_q:
            df_q = pd.DataFrame(lista_q).sort_values(by="_BestLap", ascending=True).reset_index(drop=True)
            df_q["Posición"] = range(1, len(df_q) + 1)
            lider_tiempo_q = df_q.loc[0, "_BestLap"]
            poleman = df_q.loc[0, "Piloto"]
            
            items_q_comp = []
            dict_q_h2h = {}
            for idx, row in df_q.iterrows():
                dif = row["_BestLap"] - lider_tiempo_q
                dif_txt = "Líder" if idx == 0 else f"+{dif/1000:.3f}s"
                items_q_comp.append({
                    "Pos": f"#{row['Posición']} — {row['Piloto']}",
                    "Tiempo": convertir_ms_a_minutos(row["_BestLap"]),
                    "Dif": dif_txt
                })
                dict_q_h2h[row["Piloto"]] = row["Posición"]
            datos_comparativa_tiempos[circuito]["Clasificación"] = items_q_comp
            datos_h2h_sesiones[circuito]["Clasificación"] = dict_q_h2h

        if poleman:
            todos_los_resultados.append({
                "Fecha": circuito, "Circuito": circuito, "Piloto": poleman, "Auto": "BMW", "Vueltas": 0, "_Tiempo_ms": 0, 
                "Posición": 0, "Puntos": PTS_POLE, "Tipo": "Pole"
            })

        for tipo_tipo, archivo_path in [("Sprint", archivo_sprint), ("Carrera", archivo_carrera)]:
            if not archivo_path:
                continue
            try:
                with open(archivo_path, "r", encoding="utf-8") as f:
                    datos_c = json.load(f)
                car_models_by_id = {car.get('CarId'): car.get('Model') for car in datos_c.get('Cars', []) if 'CarId' in car and 'Model' in car}
                resultados_carrera = datos_c.get("Result", []) or datos_c.get("Leaderboard", []) or datos_c.get("Cars", [])
                
                lista_carrera = []
                for item in resultados_carrera:
                    driver_info = item.get("Driver", {})
                    nombre_piloto = driver_info.get("Name", "").strip() if isinstance(driver_info, dict) else ""
                    if not nombre_piloto:
                        nombre_piloto = item.get("DriverName", "").strip()
                    
                    car_id = item.get("CarId")
                    raw_modelo_auto = item.get("Model", "") or item.get("CarModel", "") or car_models_by_id.get(car_id, "")
                    modelo_auto = obtener_modelo_legible(raw_modelo_auto, nombre_piloto)
                    if not nombre_piloto or "pacecar" in modelo_auto.lower():
                        continue
                    
                    pilotos_detectados.add(nombre_piloto)
                    num_laps = item.get("NumLaps", 0) or item.get("LapsCount", 0) or item.get("Laps", 0)
                    if isinstance(num_laps, list):
                        num_laps = len(num_laps)
                    
                    total_time = item.get("TotalTime", 0) or item.get("TotalRaceTime", 0) or item.get("Total", 0)
                    best_lap = item.get("BestLap", 0)

                    lista_carrera.append({
                        "Piloto": nombre_piloto,
                        "Auto": modelo_auto,
                        "Vueltas": int(num_laps),
                        "_Tiempo_ms": int(total_time),
                        "_BestLap": int(best_lap)
                    })
                
                if lista_carrera:
                    df_c = pd.DataFrame(lista_carrera)
                    df_c["_tiempo_orden"] = df_c["_Tiempo_ms"].apply(lambda x: x if x > 0 else float('inf'))
                    df_c = df_c.sort_values(by=["Vueltas", "_tiempo_orden"], ascending=[False, True]).drop(columns=["_tiempo_orden"]).reset_index(drop=True)
                    df_c["Posición"] = range(1, len(df_c) + 1)

                    dict_sesion_h2h = {}
                    for idx, row in df_c.iterrows():
                        dict_sesion_h2h[row["Piloto"]] = row["Posición"]
                    datos_h2h_sesiones[circuito][tipo_tipo] = dict_sesion_h2h

                    valid_fl = df_c[df_c["_BestLap"] > 0]
                    piloto_fl = valid_fl.sort_values(by="_BestLap", ascending=True).iloc[0]["Piloto"] if not valid_fl.empty else None
                    
                    dict_vr_h2h = {}
                    if not valid_fl.empty:
                        df_vr_sorted = valid_fl.sort_values(by="_BestLap", ascending=True).reset_index(drop=True)
                        for idx_vr, row_vr in df_vr_sorted.iterrows():
                            dict_vr_h2h[row_vr["Piloto"]] = idx_vr + 1
                        datos_h2h_sesiones[circuito][f"VR {tipo_tipo}"] = dict_vr_h2h

                    df_c_comp = df_c[df_c["_BestLap"] > 0].sort_values(by="_BestLap", ascending=True).reset_index(drop=True)
                    items_c_comp = []
                    if not df_c_comp.empty:
                        lider_best_lap = df_c_comp.loc[0, "_BestLap"]
                        for idx, row in df_c_comp.iterrows():
                            dif = row["_BestLap"] - lider_best_lap
                            dif_txt = "Líder" if idx == 0 else f"+{dif/1000:.3f}s"
                            items_c_comp.append({
                                "Pos": f"#{idx + 1} — {row['Piloto']}",
                                "Tiempo": convertir_ms_a_minutos(row["_BestLap"]),
                                "Dif": dif_txt
                            })
                    datos_comparativa_tiempos[circuito][tipo_tipo] = items_c_comp

                    tabla_pts = PUNTOS_SPRINT if tipo_tipo == "Sprint" else PUNTOS_CARRERA
                    for idx, row in df_c.iterrows():
                        pos = row["Posición"]
                        pts = tabla_pts.get(pos, 0)
                        todos_los_resultados.append({
                            "Fecha": circuito,
                            "Circuito": circuito,
                            "Piloto": row["Piloto"],
                            "Auto": row["Auto"],
                            "Vueltas": row["Vueltas"],
                            "_Tiempo_ms": row["_Tiempo_ms"],
                            "Posición": pos,
                            "Puntos": pts,
                            "Tipo": tipo_tipo
                        })
                    
                    if piloto_fl:
                        todos_los_resultados.append({
                            "Fecha": circuito, "Circuito": circuito, "Piloto": piloto_fl, "Auto": "BMW", "Vueltas": 0, "_Tiempo_ms": 0,
                            "Posición": 0, "Puntos": PTS_FL, "Tipo": f"Vuelta Rápida ({tipo_tipo})"
                        })

            except Exception as e:
                st.error(f"Error al leer {tipo_tipo} de {circuito}: {e}")

    if todos_los_resultados:
        df_global = pd.DataFrame(todos_los_resultados)
    else:
        df_global = pd.DataFrame(columns=["Fecha", "Circuito", "Piloto", "Auto", "Vueltas", "_Tiempo_ms", "Posición", "Puntos", "Tipo"])

    fechas_reales = list(circuitos.keys())
    todos_pilotos = sorted(list(pilotos_detectados))

    lastre_por_piloto_por_fecha = {}
    lastre_actual_sim = {p: 0 for p in todos_pilotos}
    for idx_f, f_real in enumerate(fechas_reales):
        lastre_por_piloto_por_fecha[(idx_f + 1)] = lastre_actual_sim.copy()
        df_f = df_global[(df_global["Fecha"] == f_real) & (df_global["Tipo"] == "Carrera")]
        if not df_f.empty and "Posición" in df_f.columns:
            ganadores = df_f[df_f["Posición"] == 1]
            for _, g_row in ganadores.iterrows():
                p_g = g_row["Piloto"]
                if p_g in lastre_actual_sim:
                    lastre_actual_sim[p_g] = min(50, lastre_actual_sim[p_g] + 10)

datos_vueltas_detalle = []
archivos_vueltas_dir = [f for f in os.listdir(CARPETA_VUELTAS) if f.endswith(".json")]

if archivos_vueltas_dir:
    for archivo_v_name in archivos_vueltas_dir:
        ruta_archivo_vueltas = os.path.join(CARPETA_VUELTAS, archivo_v_name)
        circuito_vueltas = limpiar_nombre_circuito(archivo_v_name)
        if os.path.exists(ruta_archivo_vueltas):
            try:
                with open(ruta_archivo_vueltas, "r", encoding="utf-8") as f:
                    contenido_v = json.load(f)
                
                if isinstance(contenido_v, list):
                    for v_item in contenido_v:
                        p_nombre = v_item.get("Piloto") or v_item.get("Driver") or v_item.get("nombre") or v_item.get("DriverName")
                        n_vuelta = v_item.get("Vuelta") or v_item.get("LapNumber") or v_item.get("Lap") or v_item.get("vuelta")
                        t_milis = v_item.get("TiempoMs") or v_item.get("TimeMs") or v_item.get("LapTime") or v_item.get("tiempo_ms")
                        if p_nombre is not None and n_vuelta is not None and t_milis is not None:
                            datos_vueltas_detalle.append({
                                "Circuito": circuito_vueltas,
                                "Piloto": str(p_nombre),
                                "Vuelta": int(n_vuelta),
                                "TiempoMs": int(t_milis),
                                "Tipo": "Carrera"
                            })
                elif isinstance(contenido_v, dict):
                    tipo_v_detectado = "Sprint" if "sprint" in archivo_v_name.lower() else "Carrera"
                    vueltas_lista = (
                        contenido_v.get("laps", []) or 
                        contenido_v.get("vueltas", []) or 
                        contenido_v.get("Laps", []) or 
                        contenido_v.get("LapList", []) or 
                        contenido_v.get("Result", []) or 
                        contenido_v.get("Cars", [])
                    )
                    
                    for v_item in vueltas_lista:
                        if isinstance(v_item, dict) and ("Laps" in v_item or "vueltas" in v_item or "LapList" in v_item):
                            driver_info = v_item.get("Driver", {})
                            p_nombre = driver_info.get("Name") if isinstance(driver_info, dict) else None
                            if not p_nombre:
                                p_nombre = v_item.get("DriverName") or v_item.get("Piloto") or "Desconocido"
                            
                            sub_laps = v_item.get("Laps") or v_item.get("vueltas") or v_item.get("LapList") or []
                            for idx_l, lap_val in enumerate(sub_laps):
                                t_ms = lap_val if isinstance(lap_val, (int, float)) else (lap_val.get("LapTime") or lap_val.get("TiempoMs") or lap_val.get("TimeMs") or 0)
                                if t_ms > 0:
                                    datos_vueltas_detalle.append({
                                        "Circuito": circuito_vueltas,
                                        "Piloto": str(p_nombre),
                                        "Vuelta": idx_l + 1,
                                        "TiempoMs": int(t_ms),
                                        "Tipo": tipo_v_detectado
                                    })
                        else:
                            p_nombre = v_item.get("Piloto") or v_item.get("Driver") or v_item.get("nombre") or v_item.get("DriverName")
                            n_vuelta = v_item.get("Vuelta") or v_item.get("LapNumber") or v_item.get("Lap") or v_item.get("vuelta")
                            t_milis = v_item.get("TiempoMs") or v_item.get("TimeMs") or v_item.get("LapTime") or v_item.get("tiempo_ms")
                            if p_nombre is not None and n_vuelta is not None and t_milis is not None:
                                datos_vueltas_detalle.append({
                                    "Circuito": circuito_vueltas,
                                    "Piloto": str(p_nombre),
                                    "Vuelta": int(n_vuelta),
                                    "TiempoMs": int(t_milis),
                                    "Tipo": tipo_v_detectado
                                })
            except Exception as e:
                st.sidebar.error(f"Error al leer archivo de vueltas: {e}")

# --- CONVERSIÓN A DATAFRAME GLOBAL (ESTO ERA LO QUE FALTABA) ---
if datos_vueltas_detalle:
    df_vueltas_global = pd.DataFrame(datos_vueltas_detalle)
else:
    df_vueltas_global = pd.DataFrame(columns=["Circuito", "Piloto", "Vuelta", "TiempoMs", "Tipo"])
# --- VISTA: RESUMEN GENERAL ---
if seccion_menu == "Resumen General":
    with st.container():
        st.subheader("🏆 Resumen del Campeonato General")
        
        if not df_global.empty:
            def limpiar_modelo(nombre_modelo):
                if not isinstance(nombre_modelo, str):
                    return "-"
                m = nombre_modelo.lower()
                if "camaro" in m:
                    return "Camaro"
                elif "mustang" in m:
                    return "Mustang"
                elif "challenger" in m:
                    return "Challenger"
                elif "torino" in m:
                    return "Torino"
                elif "m4" in m or "bmw" in m:
                    return "BMW"
                elif "mercedes" in m or "amg" in m:
                    return "Mercedes"
                else:
                    return nombre_modelo

            if "Auto" in df_global.columns:
                df_global["Auto"] = df_global["Auto"].apply(limpiar_modelo)
                df_autos = df_global.groupby("Piloto")["Auto"].agg(lambda x: x.mode()[0] if not x.mode().empty else "-").reset_index()
            else:
                df_autos = pd.DataFrame({"Piloto": df_global["Piloto"].unique(), "Auto": "-"})

            tabla_campeonato = df_global.groupby("Piloto")["Puntos"].sum().reset_index()
            tabla_campeonato = pd.merge(tabla_campeonato, df_autos, on="Piloto", how="left")
            tabla_campeonato = tabla_campeonato.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
            tabla_campeonato["Lastre Acumulado"] = tabla_campeonato["Piloto"].map(lambda p: f"{lastre_actual_sim.get(p, 0)} Kg")
            tabla_campeonato.insert(0, "Pos", range(1, len(tabla_campeonato) + 1))
            
            html_table = '<div style="overflow-x: auto; background-color: #111827; padding: 20px; border-radius: 12px; border: 1px solid #1f2937;">'
            html_table += '<table style="width: 100%; border-collapse: collapse; color: #ffffff; font-family: sans-serif; font-size: 14px;">'
            html_table += '<thead><tr style="border-bottom: 2px solid #374151; text-align: left; background-color: #1f2937;">'
            html_table += '<th style="padding: 12px; font-weight: 600;">Pos</th>'
            html_table += '<th style="padding: 12px; font-weight: 600;">Piloto</th>'
            html_table += '<th style="padding: 12px; font-weight: 600;">Modelo</th>'
            html_table += '<th style="padding: 12px; font-weight: 600;">Puntos</th>'
            html_table += '<th style="padding: 12px; font-weight: 600;">Lastre Acumulado</th>'
            html_table += '</tr></thead><tbody>'
            
            for idx, row in tabla_campeonato.iterrows():
                bg_color = "#111827" if idx % 2 == 0 else "#1a2332"
                html_table += f'<tr style="border-bottom: 1px solid #1f2937; background-color: {bg_color};">'
                html_table += f'<td style="padding: 12px;">#{row["Pos"]}</td>'
                html_table += f'<td style="padding: 12px; font-weight: 500;">{row["Piloto"]}</td>'
                html_table += f'<td style="padding: 12px; color: #94a3b8;">{row["Auto"]}</td>'
                html_table += f'<td style="padding: 12px; font-weight: bold; color: #3b82f6;">{row["Puntos"]}</td>'
                html_table += f'<td style="padding: 12px;">{row["Lastre Acumulado"]}</td>'
                html_table += '</tr>'
            
            html_table += '</tbody></table></div>'
            st.markdown(html_table, unsafe_allow_html=True)
        else:
            st.info("Sube archivos de resultados para ver el campeonato.")

# --- EVOLUCIÓN DEL CAMPEONATO EN VIVO (PUNTOS) ---
    if 'todos_pilotos' in locals() and todos_pilotos and 'fechas_reales' in locals() and fechas_reales:
        st.markdown("---")
        with st.container():
            st.subheader("📈 Evolución del Campeonato en Vivo")
            
            datos_evolucion_limpios = []
            puntos_acumulados_carrera = {p: 0.0 for p in todos_pilotos}
            max_puntaje_detectado = 50.0

            mapa_autos_df = df_global.groupby("Piloto")["Auto"].agg(lambda x: x.iloc[0] if not x.empty else "-").to_dict() if "Auto" in df_global.columns else {}

            # 1. Punto de partida común en el 0 absoluto (Numérico para anclarlo a la izquierda)
            for p in todos_pilotos:
                auto_p = mapa_autos_df.get(p, "-")
                datos_evolucion_limpios.append({
                    "Piloto": p, 
                    "FechaNum": 0, 
                    "Gran Premio": "0. Inicio",
                    "Puntos Acumulados": 0.0,
                    "Circuito": "Inicio", 
                    "Resultado": "-", 
                    "LastreInicial": "0 Kg", 
                    "Auto": auto_p,
                    "TextoPuntos": ""
                })

            cantidad_fechas_disputadas = len(fechas_reales)

            # 2. Recorremos las fechas reales disputadas con índice numérico (1 a 10)
            for idx, f_real in enumerate(fechas_reales):
                num_fecha = idx + 1
                nombre_fecha_eje_x = f"Fecha {num_fecha}"
                df_f = df_global[df_global["Fecha"] == f_real]
                
                for piloto in todos_pilotos:
                    df_piloto_f = df_f[df_f["Piloto"] == piloto]
                    if not df_piloto_f.empty:
                        puntos_fecha = float(df_piloto_f["Puntos"].sum())
                        res_carrera = df_piloto_f[df_piloto_f["Tipo"] == "Carrera"]
                        resultado_txt = f"P{int(res_carrera['Posición'].values[0])}" if not res_carrera.empty else "Puntos extra"
                    else:
                        puntos_fecha = 0.0
                        resultado_txt = "-"
                    
                    puntos_acumulados_carrera[piloto] += puntos_fecha
                    total_actual = puntos_acumulados_carrera[piloto]
                    
                    if total_actual > max_puntaje_detectado:
                        max_puntaje_detectado = total_actual
                    
                    lastre_val = lastre_por_piloto_por_fecha.get(num_fecha, {}).get(piloto, 0) if 'lastre_por_piloto_por_fecha' in locals() else 0
                    auto_p = mapa_autos_df.get(piloto, "-")
                    
                    datos_evolucion_limpios.append({
                        "Piloto": piloto, 
                        "FechaNum": num_fecha,
                        "Gran Premio": nombre_fecha_eje_x, 
                        "Puntos Acumulados": total_actual,
                        "Circuito": f_real, 
                        "Resultado": resultado_txt, 
                        "LastreInicial": f"{lastre_val} Kg",
                        "Auto": auto_p,
                        "TextoPuntos": str(int(total_actual)) if total_actual > 0 else ""
                    })

            # 3. Rellenar fechas futuras (hasta la 10) con valores nulos para completar el horizonte del Eje X
            for i in range(cantidad_fechas_disputadas + 1, 11):
                nombre_fecha_eje_x = f"Fecha {i}"
                for piloto in todos_pilotos:
                    auto_p = mapa_autos_df.get(piloto, "-")
                    datos_evolucion_limpios.append({
                        "Piloto": piloto, 
                        "FechaNum": i,
                        "Gran Premio": nombre_fecha_eje_x, 
                        "Puntos Acumulados": None, 
                        "Circuito": "Pendiente", 
                        "Resultado": "-", 
                        "LastreInicial": "0 Kg", 
                        "Auto": auto_p,
                        "TextoPuntos": ""
                    })

            df_melted_evolucion = pd.DataFrame(datos_evolucion_limpios)
            
            # Definimos las marcas y textos personalizados para el Eje X numérico
            tickvals_x = list(range(0, 11))
            ticktext_x = ["0. Inicio"] + [f"Fecha {i}" for i in range(1, 11)]
            
            if not df_melted_evolucion.empty:
                fig_evolucion = px.line(
                    df_melted_evolucion, x="FechaNum", y="Puntos Acumulados", color="Piloto",
                    template="plotly_dark", markers=True, 
                    text="TextoPuntos",
                    custom_data=["Circuito", "Resultado", "LastreInicial", "Piloto", "Auto"]
                )
                
                fig_evolucion.update_traces(
                    mode="lines+markers+text",
                    textposition="top center",
                    textfont=dict(size=10, color="white"),
                    line=dict(width=1.0), 
                    marker=dict(size=5),
                    hovertemplate="<br><b>Piloto:</b> %{customdata[3]}<br>🚗 <b>Modelo:</b> %{customdata[4]}<br>📍 <b>Circuito:</b> %{customdata[0]}<br>🏁 <b>Resultado:</b> %{customdata[1]}<br>⚖️ <b>Lastre:</b> %{customdata[2]} <br>🏆 <b>Puntos Acumulados:</b> %{y} pts<extra></extra>"
                )
                
                fig_evolucion.update_layout(
                    hovermode="closest", 
                    plot_bgcolor="#111827", 
                    paper_bgcolor="#111827", 
                    margin=dict(l=20, r=140, t=30, b=20), 
                    height=500,
                    xaxis=dict(
                        tickmode="array",
                        tickvals=tickvals_x,
                        ticktext=ticktext_x,
                        range=[-0.1, 10.2], # Fuerza a que inicie pegado al borde izquierdo
                        showgrid=True,
                        gridcolor='rgba(255, 255, 255, 0.08)'
                    ),
                    yaxis=dict(
                        range=[0, max(50, int(max_puntaje_detectado * 1.15))], 
                        autorange=False,
                        showgrid=True,
                        gridcolor='rgba(255, 255, 255, 0.08)'
                    ),
                    legend=dict(
                        title=dict(text="<b>Pilotos</b>", font=dict(size=13, color="white")),
                        font=dict(size=12, color="white"),
                        bgcolor="rgba(17, 24, 39, 0.8)",
                        bordercolor="rgba(255, 255, 255, 0.2)",
                        borderwidth=1,
                        x=1.02, y=1, xanchor="left", yanchor="top"
                    )
                )
                st.plotly_chart(fig_evolucion, use_container_width=True)
            else:
                st.info("No hay datos disponibles para mostrar en el gráfico de evolución del campeonato.")

    # --- DESGLOSE POR FECHA / CIRCUITO (RECUPERADO) ---
    if 'df_global' in locals() and not df_global.empty:
        st.markdown("---")
        st.subheader("📅 Desglose por Fecha / Circuito")
        
        circuitos_disponibles = sorted(circuitos) if 'circuitos' in locals() and circuitos else (sorted(df_global["Circuito"].unique()) if "Circuito" in df_global.columns else [])
        
        if circuitos_disponibles:
            circuito_elegido_fecha = st.selectbox("🏁 Seleccionar Fecha / Circuito para ver detalles:", circuitos_disponibles, key="select_circuito_desglose_general")
            
            col_sprint, col_carrera = st.columns(2)
            
            def consolidar_sesion_fecha(df_sub, es_carrera_principal=False):
                if df_sub.empty:
                    return pd.DataFrame()
                
                agrupados = []
                pilotos_en_sesion = df_sub["Piloto"].unique()
                
                for pil in pilotos_en_sesion:
                    df_p = df_sub[df_sub["Piloto"] == pil]
                    
                    reg_pos = df_p[~df_p["Tipo"].astype(str).str.lower().str.contains("pole|vuelta|vr", na=False)]
                    if not reg_pos.empty:
                        pos_val = reg_pos["Posición"].values[0]
                        auto_val = reg_pos["Auto"].values[0] if "Auto" in reg_pos.columns else "-"
                    else:
                        pos_val = 999
                        auto_val = df_p["Auto"].values[0] if "Auto" in df_p.columns else "-"

                    pos_salida_val = "-"
                    if es_carrera_principal and 'df_global' in locals():
                        df_clasif_piloto = df_global[
                            (df_global["Circuito"] == circuito_elegido_fecha) & 
                            (df_global["Piloto"] == pil) & 
                            (
                                df_global["Tipo"].astype(str).str.lower().str.contains("clasif|quali|q1|q2|q3", na=False) |
                                (df_global["Sesion"].astype(str).str.lower().str.contains("clasif|quali", na=False) if "Sesion" in df_global.columns else False)
                            )
                        ]
                        if not df_clasif_piloto.empty:
                            p_sal = df_clasif_piloto["Posición"].min()
                            if not pd.isna(p_sal):
                                pos_salida_val = f"P{int(p_sal)}"

                    extras_txt = []
                    for _, row_r in df_p.iterrows():
                        tipo_str = str(row_r.get("Tipo", "")).lower()
                        pts_r = float(row_r.get("Puntos", 0))
                        
                        if "pole" in tipo_str or "clasif" in tipo_str:
                            if pts_r > 0 and "pole" in tipo_str:
                                extras_txt.append(f"P: +{int(pts_r) if pts_r.is_integer() else pts_r}")
                        if "vuelta" in tipo_str or "vr" in tipo_str:
                            if pts_r > 0:
                                extras_txt.append(f"Vr: +{int(pts_r) if pts_r.is_integer() else pts_r}")

                    puntos_totales_sesion = df_p["Puntos"].sum()
                    detalles_extras_str = f" ({', '.join(extras_txt)})" if extras_txt else ""
                    
                    try:
                        pos_int = int(pos_val)
                    except:
                        pos_int = 999

                    item_dict = {
                        "Pos_Sort": pos_int,
                        "Posición": pos_int if pos_int != 999 else "-",
                        "Piloto": pil,
                        "Auto": auto_val,
                    }
                    if es_carrera_principal:
                        item_dict["Clasificación (Salida)"] = pos_salida_val
                    
                    item_dict["Puntos"] = f"{int(puntos_totales_sesion) if puntos_totales_sesion.is_integer() else puntos_totales_sesion}{detalles_extras_str}"
                    agrupados.append(item_dict)
                
                df_res = pd.DataFrame(agrupados)
                if not df_res.empty:
                    df_res = df_res.sort_values(by="Pos_Sort", ascending=True).drop(columns=["Pos_Sort"]).reset_index(drop=True)
                return df_res

            with col_sprint:
                st.markdown("#### ⚡ Sprint")
                try:
                    df_sprint_fecha = df_global[(df_global["Circuito"] == circuito_elegido_fecha) & (df_global["Tipo"].str.lower().str.contains("sprint", na=False))]
                    df_sprint_cons = consolidar_sesion_fecha(df_sprint_fecha, es_carrera_principal=False)
                    if not df_sprint_cons.empty:
                        st.dataframe(df_sprint_cons, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No hay registros de Sprint para este circuito.")
                except Exception as e_sprint:
                    st.caption(f"Error al cargar Sprint: {e_sprint}")
                    
            with col_carrera:
                st.markdown("#### 🏎️ Carrera")
                try:
                    df_carrera_fecha = df_global[(df_global["Circuito"] == circuito_elegido_fecha) & (~df_global["Tipo"].str.lower().str.contains("sprint|clasif|quali", na=False))]
                    df_carrera_cons = consolidar_sesion_fecha(df_carrera_fecha, es_carrera_principal=True)
                    if not df_carrera_cons.empty:
                        st.dataframe(df_carrera_cons, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No hay registros de Carrera para este circuito.")
                except Exception as e_carrera:
                    st.caption(f"Error al cargar Carrera: {e_carrera}")

# --- EVOLUCIÓN DE POSICIONES DE CLASIFICACIÓN (SALIDA - 10 FECHAS) ---
    if 'datos_comparativa_tiempos' in locals() and datos_comparativa_tiempos and 'todos_pilotos' in locals() and todos_pilotos:
        st.markdown("---")
        with st.container():
            st.subheader("📈 Evolución de Posiciones de Clasificación (Salida - 10 Fechas)")
            
            datos_clasif_evolucion = []
            
            # Definimos la posición base inferior común para que todas arranquen juntas abajo (ej. P13)
            posicion_vertice_inferior = len(todos_pilotos) if len(todos_pilotos) > 0 else 13
            
            circuitos_disponibles = list(datos_comparativa_tiempos.keys())
            
            # 1. Creamos el punto "0. Inicio": TODOS nacen exactamente en la misma esquina inferior
            for piloto in todos_pilotos:
                auto_p = mapa_autos_df.get(piloto, "-") if 'mapa_autos_df' in locals() else "-"
                datos_clasif_evolucion.append({
                    "Piloto": piloto,
                    "Gran Premio": "0. Inicio",
                    "Posición Salida": posicion_vertice_inferior, # <--- Todas nacen abajo del todo
                    "Circuito": "Inicio",
                    "Auto": auto_p,
                    "TextoPos": "" # Sin texto en el inicio para mantenerlo limpio
                })
            
            # 2. Recorremos hasta 10 fechas/circuitos
            for i in range(1, 11):
                nombre_fecha_eje_x = f"Fecha {i}"
                
                circuito_actual = None
                if len(circuitos_disponibles) >= i:
                    circuito_actual = circuitos_disponibles[i - 1]
                
                registros_clasif = []
                circuito_nombre = f"Fecha {i} (Pendiente)"
                
                if circuito_actual is not None:
                    circuito_nombre = circuito_actual
                    registros_clasif = datos_comparativa_tiempos[circuito_actual].get("Clasificación", [])
                
                # Mapeamos las posiciones de este circuito para cada piloto
                posiciones_circuito = {}
                for reg in registros_clasif:
                    texto_pos = str(reg.get("Pos", ""))
                    if "—" in texto_pos:
                        partes = texto_pos.split("—")
                        nombre_p = partes[-1].strip()
                        import re
                        nums = re.findall(r'\d+', partes[0])
                        if nums:
                            p_num = int(nums[0])
                            posiciones_circuito[nombre_p.lower()] = p_num

                for piloto in todos_pilotos:
                    pos_val = None
                    for p_key, p_val in posiciones_circuito.items():
                        if p_key == piloto.lower():
                            pos_val = p_val
                            break
                    
                    auto_p = mapa_autos_df.get(piloto, "-") if 'mapa_autos_df' in locals() else "-"
                    
                    datos_clasif_evolucion.append({
                        "Piloto": piloto,
                        "Gran Premio": nombre_fecha_eje_x,
                        "Posición Salida": pos_val,
                        "Circuito": circuito_nombre,
                        "Auto": auto_p,
                        "TextoPos": str(pos_val) if pos_val is not None else ""
                    })

            df_melted_clasif = pd.DataFrame(datos_clasif_evolucion)
            lista_10_fechas_clasif = ["0. Inicio"] + [f"Fecha {i}" for i in range(1, 11)]
            
            if not df_melted_clasif.empty:
                fig_clasif_ev = px.line(
                    df_melted_clasif, x="Gran Premio", y="Posición Salida", color="Piloto",
                    template="plotly_dark", markers=True,
                    text="TextoPos",
                    custom_data=["Circuito", "Piloto", "Auto", "Posición Salida"],
                    category_orders={"Gran Premio": lista_10_fechas_clasif}
                )
                
                fig_clasif_ev.update_traces(
                    mode="lines+markers+text",
                    textposition="top center",
                    textfont=dict(size=10, color="white"),
                    line=dict(width=1.0), 
                    marker=dict(size=5),
                    hovertemplate="<br><b>Piloto:</b> %{customdata[1]}<br>🚗 <b>Modelo:</b> %{customdata[2]}<br>📍 <b>Circuito:</b> %{customdata[0]}<br>🏁 <b>Posición de Salida:</b> P%{y}<extra></extra>"
                )
                
                fig_clasif_ev.update_layout(
                    hovermode="closest",
                    plot_bgcolor="#111827",
                    paper_bgcolor="#111827",
                    margin=dict(l=20, r=140, t=30, b=20),
                    height=500,
                    xaxis=dict(categoryorder="array", categoryarray=lista_10_fechas_clasif),
                    yaxis=dict(
                        autorange="reversed",
                        dtick=1,
                        showgrid=True,
                        gridcolor='rgba(255, 255, 255, 0.08)'
                    ),
                    legend=dict(
                        title=dict(text="<b>Pilotos</b>", font=dict(size=13, color="white")),
                        font=dict(size=12, color="white"),
                        bgcolor="rgba(17, 24, 39, 0.8)",
                        bordercolor="rgba(255, 255, 255, 0.2)",
                        borderwidth=1,
                        x=1.02, y=1, xanchor="left", yanchor="top"
                    )
                )
                st.plotly_chart(fig_clasif_ev, use_container_width=True)
            else:
                st.info("No hay datos disponibles para mostrar en el gráfico de clasificación.")
# --- VISTA: COMPARATIVA DE TIEMPOS ---
elif seccion_menu == "Comparativa de Tiempos":
        st.subheader("📊 Comparativa Global de Tiempos por Evento")
        if datos_comparativa_tiempos:
            circuito_sel = st.selectbox("Seleccionar Circuito / Evento:", list(datos_comparativa_tiempos.keys()))
            eventos_data = datos_comparativa_tiempos[circuito_sel]
            
            cols = st.columns(3)
            tipos_sesion = ["Clasificación", "Sprint", "Carrera"]
            for i, tipo in enumerate(tipos_sesion):
                with cols[i]:
                    st.markdown(f"### 📄 {tipo}")
                    registros = eventos_data.get(tipo, [])
                    if registros:
                        for reg in registros:
                            st.info(f"**{reg['Pos']}**\n\n⏱️ `{reg['Tiempo']}` | 🕒 {reg['Dif']}")
                    else:
                        st.info(f"No hay datos de {tipo} cargados.")
        else:
            st.info("Sube archivos de Clasificación, Sprint o Carrera para ver la comparativa.")


    # --- VISTA: LASTRE ---
elif seccion_menu == "Lastre":
        st.subheader("⚖️ Lastre Actual para la Siguiente Fecha")
        if fechas_reales and not df_global.empty:
            df_lastre_view = pd.DataFrame(list(lastre_actual_sim.items()), columns=["Piloto", "Lastre (Kg)"])
            df_lastre_view = df_lastre_view.sort_values(by="Lastre (Kg)", ascending=False).reset_index(drop=True)
            
            html_lastre = '<div style="overflow-x: auto; background-color: #111827; padding: 20px; border-radius: 12px; border: 1px solid #1f2937;">'
            html_lastre += '<table style="width: 100%; border-collapse: collapse; color: #ffffff; font-family: sans-serif; font-size: 14px;">'
            html_lastre += '<thead><tr style="border-bottom: 2px solid #374151; text-align: left; background-color: #1f2937;">'
            html_lastre += '<th style="padding: 12px; font-weight: 600;">Piloto</th>'
            html_lastre += '<th style="padding: 12px; font-weight: 600;">Lastre (Kg)</th>'
            html_lastre += '</tr></thead><tbody>'
            
            for idx, row in df_lastre_view.iterrows():
                bg_color = "#111827" if idx % 2 == 0 else "#1a2332"
                html_lastre += f'<tr style="border-bottom: 1px solid #1f2937; background-color: {bg_color};">'
                html_lastre += f'<td style="padding: 12px; font-weight: 500;">{row["Piloto"]}</td>'
                html_lastre += f'<td style="padding: 12px; color: #10b981; font-weight: bold;">{row["Lastre (Kg)"]} Kg</td>'
                html_lastre += '</tr>'
            
            html_lastre += '</tbody></table></div>'
            st.markdown(html_lastre, unsafe_allow_html=True)
        else:
            st.info("No hay suficientes datos para calcular el lastre.")

    # --- VISTA: DUELO H2H ---
elif seccion_menu == "Duelo H2H":
        st.subheader("⚔️ Duelo Head-to-Head (H2H)")
        st.write("Comparativa directa y cara a cara entre dos pilotos del torneo")
        
        if len(todos_pilotos) >= 2:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p1 = st.selectbox("Selecciona Piloto 1:", todos_pilotos, index=0)
            with col_p2:
                p2 = st.selectbox("Selecciona Piloto de Referencia (Piloto 2):", todos_pilotos, index=1 if len(todos_pilotos) > 1 else 0)
            
            st.markdown("---")
            st.markdown("### 🏆 Puntos en el Campeonato")
            
            puntos_totales_p1 = float(df_global[df_global["Piloto"] == p1]["Puntos"].sum()) if not df_global.empty else 0.0
            puntos_totales_p2 = float(df_global[df_global["Piloto"] == p2]["Puntos"].sum()) if not df_global.empty else 0.0
            brecha = abs(puntos_totales_p1 - puntos_totales_p2)
            
            col_pts1, col_brecha, col_pts2 = st.columns(3)
            with col_pts1:
                st.write(f"Puntos {p1}")
                st.markdown(f"### {puntos_totales_p1:.2f} pts")
            with col_brecha:
                st.write("Brecha")
                st.markdown(f"### {brecha:.2f} pts")
                if puntos_totales_p1 > puntos_totales_p2:
                    st.caption(f"🟢 Lider {p1}")
                elif puntos_totales_p2 > puntos_totales_p1:
                    st.caption(f"🟢 Lider {p2}")
                else:
                    st.caption("Empate")
            with col_pts2:
                st.write(f"Puntos {p2}")
                st.markdown(f"### {puntos_totales_p2:.2f} pts")

            st.markdown("---")
            st.markdown("### 🏁 Historial de Duelos Directos en Pista")
            st.write("Frecuencia acumulada de quién superó a quién en cada sesión:")

            conteo_sesiones = {}
            for circ, sesiones in datos_h2h_sesiones.items():
                for nombre_sesion, pos_dict in sesiones.items():
                    if p1 in pos_dict and p2 in pos_dict:
                        if nombre_sesion not in conteo_sesiones:
                            conteo_sesiones[nombre_sesion] = {p1: 0, p2: 0}
                        if pos_dict[p1] < pos_dict[p2]:
                            conteo_sesiones[nombre_sesion][p1] += 1
                        elif pos_dict[p2] < pos_dict[p1]:
                            conteo_sesiones[nombre_sesion][p2] += 1

            if conteo_sesiones:
                items_sesiones = list(conteo_sesiones.items())
                for i in range(0, len(items_sesiones), 3):
                    cols_sesiones = st.columns(3)
                    for j in range(3):
                        if i + j < len(items_sesiones):
                            sesion_nombre, marcador = items_sesiones[i + j]
                            with cols_sesiones[j]:
                                v1 = marcador[p1]
                                v2 = marcador[p2]
                                st.info(f"**{sesion_nombre}**\n\n### {v1} — {v2}")
            else:
                st.info("No hay suficientes eventos comunes en pista para comparar entre estos dos pilotos.")
        else:
            st.info("Se necesitan al menos 2 pilotos para realizar el duelo H2H.")

    # --- VISTA: SIMULADOR DE CAMPEONATO ---
elif seccion_menu == "Simulador de Campeonato":
        st.subheader("🎮 Simulador de Campeonato")
        st.write("Simula futuras fechas o proyecta resultados.")

# --- VISTA: ESTADÍSTICAS ---
elif seccion_menu == "Estadísticas":
    st.subheader("☑️ Live Timing Pro — Análisis de Ritmo y Posiciones")
    
    tiene_datos_comp = 'datos_comparativa_tiempos' in locals() and datos_comparativa_tiempos
    df_analisis_global = df_vueltas_global if 'df_vueltas_global' in locals() and not df_vueltas_global.empty else pd.DataFrame()
    
    if tiene_datos_comp or (not df_analisis_global.empty and "Piloto" in df_analisis_global.columns):
        
        # --- 1. SELECTOR DE CIRCUITO ---
        if tiene_datos_comp:
            circuitos_disponibles = sorted(list(datos_comparativa_tiempos.keys()))
        else:
            circuitos_disponibles = sorted(df_analisis_global["Circuito"].unique()) if "Circuito" in df_analisis_global.columns else ["General"]
            
        circuito_seleccionado = st.selectbox("🏁 Seleccionar Circuito:", circuitos_disponibles, key="select_circuito_stats")
        
        # --- 2. SELECTOR DE TIPO DE SESIÓN (SOLO CARRERA Y SPRINT) ---
        tipos_disponibles = []
        if tiene_datos_comp and circuito_seleccionado in datos_comparativa_tiempos:
            eventos_data = datos_comparativa_tiempos[circuito_seleccionado]
            for t in ["Sprint", "Carrera"]:
                if t in eventos_data and eventos_data[t]:
                    tipos_disponibles.append(t)
        
        if not tipos_disponibles:
            tipos_disponibles = ["Carrera", "Sprint"]

        if len(tipos_disponibles) > 1:
            sesion_elegida_ui = st.radio("📋 Seleccionar Sesión:", tipos_disponibles, horizontal=True, key="radio_sesion_stats")
        elif len(tipos_disponibles) == 1:
            sesion_elegida_ui = tipos_disponibles[0]
            st.caption(f"ℹ️ Sesión única detectada para este circuito: **{sesion_elegida_ui}**")
        else:
            sesion_elegida_ui = "Carrera"

        # --- OBTENCIÓN Y FILTRADO DEL DATAFRAME ---
        df_analisis = pd.DataFrame()
        if not df_analisis_global.empty:
            if "Circuito" in df_analisis_global.columns:
                df_analisis = df_analisis_global[df_analisis_global["Circuito"] == circuito_seleccionado]
            else:
                df_analisis = df_analisis_global.copy()
            
            # FILTRADO EXCLUSIVO PARA CARRERA O SPRINT (IGNORANDO CLASIFICACIÓN)
            if "Tipo" in df_analisis.columns:
                if sesion_elegida_ui == "Sprint":
                    df_filtrado_tipo = df_analisis[df_analisis["Tipo"].astype(str).str.lower().str.contains("sprint", na=False)]
                else:
                    df_filtrado_tipo = df_analisis[~df_analisis["Tipo"].astype(str).str.lower().str.contains("clasif|qualy|q1|q2|q3|sprint", na=False)]
                
                if not df_filtrado_tipo.empty:
                    df_analisis = df_filtrado_tipo

        pilotos_disponibles = sorted(df_analisis["Piloto"].unique()) if not df_analisis.empty and "Piloto" in df_analisis.columns else []
        
        if len(pilotos_disponibles) >= 1 and "TiempoMs" in df_analisis.columns:
            def convertir_a_min_seg(ms):
                if pd.isna(ms):
                    return "-"
                m = int(ms // 60000)
                s = int((ms % 60000) // 1000)
                ms_resto = int(ms % 1000)
                return f"{m:02d}:{s:02d},{ms_resto:03d}"
            
            # --- DETECCIÓN DE PACE CAR ---
            vueltas_pace_car = []
            mediana_general = df_analisis["TiempoMs"].median()
            umbral_lento = mediana_general * 1.35  
            total_pilotos = df_analisis["Piloto"].nunique()
            conteo_lentos_por_vuelta = df_analisis[df_analisis["TiempoMs"] > umbral_lento].groupby("Vuelta")["Piloto"].nunique()
            vueltas_pace_car = conteo_lentos_por_vuelta[conteo_lentos_por_vuelta > (total_pilotos / 2)].index.tolist()

            # --- CALCULAR MÉTRICAS PARA TODOS LOS PILOTOS ---
            resumen_pilotos = []
            for p in pilotos_disponibles:
                df_p = df_analisis[df_analisis["Piloto"] == p]
                df_reg_p = df_p[(df_p["Vuelta"] > 2) & (~df_p["Vuelta"].isin(vueltas_pace_car))]
                
                mejor_p = df_p["TiempoMs"].min() if not df_p.empty else float('inf')
                prom_p = df_p["TiempoMs"].mean() if not df_p.empty else float('inf')
                reg_p = df_reg_p["TiempoMs"].std() if not df_reg_p.empty and len(df_reg_p) > 1 else 0.0
                if pd.isna(reg_p): reg_p = 0.0
                
                resumen_pilotos.append({
                    "Piloto": p,
                    "MejorMs": mejor_p,
                    "PromMs": prom_p,
                    "RegMs": reg_p
                })
            
            df_resumen = pd.DataFrame(resumen_pilotos)
            
            df_resumen_ritmo = df_resumen[df_resumen["PromMs"] != float('inf')].sort_values(by="PromMs", ascending=True).reset_index(drop=True)
            df_resumen_reg = df_resumen[df_resumen["RegMs"] != float('inf')].sort_values(by="RegMs", ascending=True).reset_index(drop=True)

            ganador_record = df_resumen.loc[df_resumen["MejorMs"].idxmin()] if not df_resumen.empty and df_resumen["MejorMs"].min() != float('inf') else None
            ganador_ritmo = df_resumen_ritmo.iloc[0] if not df_resumen_ritmo.empty else None
            ganador_reg = df_resumen_reg.iloc[0] if not df_resumen_reg.empty else None

            # --- TRES TARJETAS PRINCIPALES ---
            col_t1, col_t2, col_t3 = st.columns(3)
            
            piloto_rec = ganador_record['Piloto'] if ganador_record is not None else '-'
            tiempo_rec = convertir_a_min_seg(ganador_record['MejorMs']) if ganador_record is not None else '-'

            piloto_rit = ganador_ritmo['Piloto'] if ganador_ritmo is not None else '-'
            tiempo_rit = convertir_a_min_seg(ganador_ritmo['PromMs']) if ganador_ritmo is not None else '-'

            piloto_reg = ganador_reg['Piloto'] if ganador_reg is not None else '-'
            val_reg = f"±{ganador_reg['RegMs']/1000:.3f}s" if ganador_reg is not None else "N/A"
            ref_reg = convertir_a_min_seg(ganador_reg['PromMs']) if ganador_reg is not None else '-'

            with col_t1:
                st.markdown(f"""
                    <div style="background-color: #1e1e2f; padding: 18px; border-radius: 10px; border-left: 5px solid #ffc107; text-align: center;">
                        <span style="font-size: 13px; color: #ffecb3; font-weight: bold;">🏁 RÉCORD DE VUELTA</span>
                        <div style="color: #ffffff; font-size: 22px; font-weight: bold; margin: 12px 0 6px 0;">{piloto_rec}</div>
                        <div style="color: #ffc107; font-size: 18px; font-weight: bold;">{tiempo_rec}</div>
                        <div style="color: #94a3b8; font-size: 11px; margin-top: 6px; line-height: 1.2;">Vuelta más rápida absoluta de la sesión.</div>
                    </div>
                """, unsafe_allow_html=True)
                
            with col_t2:
                st.markdown(f"""
                    <div style="background-color: #1e1e2f; padding: 18px; border-radius: 10px; border-left: 5px solid #28a745; text-align: center;">
                        <span style="font-size: 13px; color: #d4edda; font-weight: bold;">⏱️ MEJOR RITMO (VELOCIDAD)</span>
                        <div style="color: #ffffff; font-size: 22px; font-weight: bold; margin: 12px 0 6px 0;">{piloto_rit}</div>
                        <div style="color: #28a745; font-size: 18px; font-weight: bold;">{tiempo_rit}</div>
                        <div style="color: #94a3b8; font-size: 11px; margin-top: 6px; line-height: 1.2;">Mide la <b>velocidad pura (promedio de todos los tiempos de vuelta validos)</b>.</div>
                    </div>
                """, unsafe_allow_html=True)
                
            with col_t3:
                st.markdown(f"""
                    <div style="background-color: #1e1e2f; padding: 18px; border-radius: 10px; border-left: 5px solid #17a2b8; text-align: center;">
                        <span style="font-size: 13px; color: #d1ecf1; font-weight: bold;">📊 MEJOR REGULARIDAD (CONSISTENCIA)</span>
                        <div style="color: #ffffff; font-size: 22px; font-weight: bold; margin: 12px 0 6px 0;">{piloto_reg}</div>
                        <div style="color: #17a2b8; font-size: 18px; font-weight: bold;">{val_reg}</div>
                        <div style="color: #94a3b8; font-size: 11px; margin-top: 4px;">Ref: {ref_reg}</div>
                        <div style="color: #94a3b8; font-size: 11px; margin-top: 4px; line-height: 1.2;">Mide la <b>estabilidad (menor variacion/desvío entre vueltas)</b>.</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- DESPLEGABLES DEBAJO DE LAS TARJETAS ---
            col_d1, col_d2, col_d3 = st.columns(3)
            
            with col_d2:
                with st.expander("📋 Ver tabla completa de Ritmo"):
                    if not df_resumen_ritmo.empty:
                        ref_ritmo_ms = df_resumen_ritmo.iloc[0]["PromMs"]
                        for idx, row in df_resumen_ritmo.iterrows():
                            dif_ms = row["PromMs"] - ref_ritmo_ms
                            dif_str = f"+{dif_ms/1000:.3f}s" if idx > 0 else "Líder"
                            st.markdown(f"**{idx+1}. {row['Piloto']}** — {convertir_a_min_seg(row['PromMs'])} <span style='color: #94a3b8; font-size: 12px;'>({dif_str})</span>", unsafe_allow_html=True)
                            
            with col_d3:
                with st.expander("📋 Ver tabla de Regularidad"):
                    if not df_resumen_reg.empty:
                        for idx, row in df_resumen_reg.iterrows():
                            st.markdown(f"**{idx+1}. {row['Piloto']}** — ±{row['RegMs']/1000:.3f}s <span style='color: #94a3b8; font-size: 12px;'>(Ref: {convertir_a_min_seg(row['PromMs'])})</span>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- GRÁFICO DE EVOLUCIÓN DE RITMO ---
            import plotly.express as px

            st.markdown("### 📈 Gráfico de Evolución de Ritmo")
            
            fil_pc = st.checkbox("🧹 Filtrar vueltas de Pace Car", value=True, key="filtro_pace_car_stats")
            st.caption("💡 Detecta y oculta las vueltas neutralizadas por Pace Car.")

            df_grafico = df_analisis.copy()
            if fil_pc and vueltas_pace_car:
                df_grafico = df_grafico[~df_grafico["Vuelta"].isin(vueltas_pace_car)]

            df_grafico["Tiempo_Formateado"] = df_grafico["TiempoMs"].apply(convertir_a_min_seg)

            q_max = df_grafico["TiempoMs"].quantile(0.95) * 1.15 if not df_grafico.empty else 100000
            q_min = df_grafico["TiempoMs"].min() * 0.95

            fig = px.line(
                df_grafico, 
                x="Vuelta", 
                y="TiempoMs", 
                color="Piloto",
                markers=True,
                hover_data={"TiempoMs": False, "Tiempo_Formateado": True, "Vuelta": True}
            )

            paso_ms = 5000  
            inicio_ticks = int((q_min // paso_ms) * paso_ms)
            fin_ticks = int((q_max // paso_ms + 1) * paso_ms)
            valores_ticks = list(range(inicio_ticks, fin_ticks + paso_ms, paso_ms))
            labels_ticks = [f"{t//60000:02d}:{(t%60000)//1000:02d},000" for t in valores_ticks]

            fig.update_layout(
                xaxis_title="Número de Vuelta",
                yaxis_title="Tiempo de Vuelta",
                legend_title="Pilotos",
                hovermode="x unified",
                template="plotly_dark",
                height=550,
                xaxis=dict(dtick=1, showgrid=True, gridcolor='rgba(255, 255, 255, 0.1)'),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(255, 255, 255, 0.1)', 
                    range=[q_min, q_max],
                    tickmode='array',
                    tickvals=valores_ticks,
                    ticktext=labels_ticks
                )
            )
            fig.update_traces(
                line=dict(width=2.5), 
                marker=dict(size=6),
                hovertemplate="<b>%{customdata[1]}</b><br>Vuelta %{x}<br>Tiempo: <b>%{customdata[0]}</b><extra></extra>"
            )

            st.plotly_chart(fig, use_container_width=True, key="plotly_evolucion_ritmo_stats")
        else:
            st.warning("No hay suficientes datos o pilotos cargados para esta sesión.")
    else:
        st.info("No hay datos de comparativa ni de vueltas cargados.")

    # =========================================================================
    # 🕸️ PERFIL COMPARATIVO MULTIVARIABLE (GRÁFICO DE ARAÑA)
    # =========================================================================
    st.markdown("---")
    st.subheader("🕸️ Perfil Comparativo Multivariable")
    st.caption("Haz clic en los nombres de los pilotos en la leyenda para activar o desactivar su perfil.")

    # Desplegable integrado en la app con la explicación de cada arista
    with st.expander("ℹ️ ¿Cómo leer este gráfico? (Explicación de las métricas)"):
        st.markdown("""
        * **% Podios**: Mide la constancia en los puestos de vanguardia (porcentaje de fechas finalizadas entre los tres primeros).
        * **% Victorias**: Representa la efectividad de triunfo puro (porcentaje de fechas ganadas).
        * **Promedio de Puntos**: Evalúa la cosecha global a lo largo del campeonato (puntos promedio sumados por fecha).
        * **Ganancia de Posiciones**: Destaca la capacidad combativa y de avance en pista a lo largo de las competencias.
        * **% Ritmo Carrera**: Analiza la velocidad y el posicionamiento sostenido en base a la posición final promedio.
        """)

    try:
        if 'df_global' in locals() and not df_global.empty and 'todos_pilotos' in locals() and todos_pilotos:
            
            datos_radar = []
            total_fechas_torneo = len(fechas_reales) if 'fechas_reales' in locals() and len(fechas_reales) > 0 else 1

            for piloto in todos_pilotos:
                df_p = df_global[df_global["Piloto"] == piloto]
                df_p_carreras = df_p[df_p["Tipo"] == "Carrera"] if "Tipo" in df_p.columns else df_p

                posiciones = []
                puntos_totales_piloto = 0.0
                if "Posición" in df_p_carreras.columns:
                    for p_val in df_p_carreras["Posición"]:
                        try:
                            posiciones.append(int(p_val))
                        except (ValueError, TypeError):
                            pass
                
                if "Puntos" in df_p.columns:
                    puntos_totales_piloto = float(df_p["Puntos"].sum())

                cant_podios = sum(1 for p in posiciones if p in [1, 2, 3])
                cant_victorias = sum(1 for p in posiciones if p == 1)
                
                promedio_puntos = (puntos_totales_piloto / total_fechas_torneo) if total_fechas_torneo > 0 else 0.0
                pct_promedio_puntos = min(100.0, (promedio_puntos / 30.0) * 100.0)

                pos_prom = (sum(posiciones) / len(posiciones)) if posiciones else 15.0
                pct_ritmo = max(0.0, min(100.0, ((15.0 - pos_prom) / 14.0) * 100.0))
                ganancia_neta_pos = max(0.0, min(100.0, 50.0 + (15.0 - pos_prom) * 2.5)) 

                pct_podios = (cant_podios / total_fechas_torneo) * 100.0
                pct_victorias = (cant_victorias / total_fechas_torneo) * 100.0

                datos_radar.append({
                    "Piloto": piloto,
                    "pct_podios": pct_podios,
                    "cant_podios": cant_podios,
                    "pct_victorias": pct_victorias,
                    "cant_victorias": cant_victorias,
                    "pct_promedio_puntos": pct_promedio_puntos,
                    "promedio_puntos": promedio_puntos,
                    "ganancia_neta_pos": ganancia_neta_pos,
                    "pct_ritmo": pct_ritmo,
                    "pos_prom": pos_prom,
                    "total_fechas": total_fechas_torneo
                })

            filas_plotly = []
            for d in datos_radar:
                piloto_name = d["Piloto"]
                metricas = [
                    ("% Podios", d["pct_podios"], f"{d['pct_podios']:.1f}% ({d['cant_podios']}/{d['total_fechas']} fechas)"),
                    ("% Victorias", d["pct_victorias"], f"{d['pct_victorias']:.1f}% ({d['cant_victorias']}/{d['total_fechas']} fechas)"),
                    ("Promedio de Puntos", d["pct_promedio_puntos"], f"{d['promedio_puntos']:.1f} pts/fecha"),
                    ("Ganancia de Posiciones", d["ganancia_neta_pos"], f"Ritmo competitivo global"),
                    ("% Ritmo Carrera", d["pct_ritmo"], f"P{d['pos_prom']:.1f} Promedio")
                ]
                for eje, val_real_pct, txt_hover in metricas:
                    filas_plotly.append({
                        "Piloto": piloto_name,
                        "Métrica": eje,
                        "Valor_Norm": max(0.0, min(100.0, float(val_real_pct))),
                        "Valor_Real": txt_hover
                    })

            df_radar = pd.DataFrame(filas_plotly)

            listas_cerradas = []
            for piloto_name in todos_pilotos:
                df_p_radar = df_radar[df_radar["Piloto"] == piloto_name].copy()
                if not df_p_radar.empty:
                    primera_fila = df_p_radar.iloc[[0]].copy()
                    df_p_radar = pd.concat([df_p_radar, primera_fila], ignore_index=True)
                    listas_cerradas.append(df_p_radar)

            if listas_cerradas:
                df_radar = pd.concat(listas_cerradas, ignore_index=True)

            col_izq_r, col_centro_r, col_der_r = st.columns([0.2, 3, 0.2])

            with col_centro_r:
                fig_radar = px.line_polar(
                    df_radar,
                    r="Valor_Norm",
                    theta="Métrica",
                    color="Piloto",
                    line_close=True,
                    template="plotly_dark",
                    custom_data=["Valor_Real", "Piloto"]
                )

                fig_radar.update_traces(
                    fill='toself',
                    opacity=0.35,
                    line=dict(width=3),
                    marker=dict(size=8),
                    hoveron='points+fills', 
                    hovertemplate="🏎️ <b>%{customdata[1]}</b><br>📌 <b>%{theta}:</b> %{customdata[0]}<extra></extra>"
                )

                fig_radar.update_layout(
                    paper_bgcolor="#111827",
                    plot_bgcolor="#111827",
                    hovermode="closest",
                    polar=dict(
                        bgcolor="#111827",
                        radialaxis=dict(
                            visible=True,
                            range=[0, 105],
                            showticklabels=False,
                            linecolor="#374151",
                            gridcolor="#374151"
                        ),
                        angularaxis=dict(
                            gridcolor="#374151",
                            linecolor="#374151",
                            tickfont=dict(size=12, color="#ffffff")
                        )
                    ),
                    margin=dict(l=40, r=40, t=20, b=30),
                    height=450,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.25,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=12, color="#ffffff")
                    )
                )

                st.plotly_chart(fig_radar, use_container_width=True, key="radar_actualizado_campeonato_con_expander")
        else:
            st.info("ℹ️ Sube archivos de resultados para habilitar el perfil comparativo multivariable.")

    except Exception as e_radar:
        st.warning(f"Error generando el gráfico de radar: {e_radar}")