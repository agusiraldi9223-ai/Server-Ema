import streamlit as st
import json
import pandas as pd

st.set_page_config(page_title="Gestor de Torneo AC", layout="wide")
st.title("🏎️ Clasificación Oficial y Lastres - Assetto Corsa")

# Subir el archivo JSON de resumen de la carrera
archivo_json = st.file_uploader("Sube el archivo JSON de la sesión de carrera", type=["json"])

if archivo_json is not None:
    try:
        datos = json.load(archivo_json)
        autos = datos.get("Cars", [])
        
        lista_resultados = []
        
        for auto in autos:
            nombre_piloto = auto.get("DriverName", "").strip()
            modelo_auto = auto.get("CarModel", "")
            
            # FILTRO: Ignorar al Pace Car o entradas sin nombre
            if not nombre_piloto or "pacecar" in modelo_auto.lower():
                continue
                
            num_laps = auto.get("NumLaps", 0)
            total_time = auto.get("TotalTime", 0)
            best_lap = auto.get("BestLap", 0)
            lastre_actual = auto.get("BallastKG", 0)
            
            lista_resultados.append({
                "Piloto": nombre_piloto,
                "Auto": modelo_auto,
                "Vueltas": num_laps,
                "Tiempo Total (ms)": total_time,
                "Mejor Vuelta (ms)": best_lap,
                "Lastre Actual (kg)": lastre_actual
            })
            
        if lista_resultados:
            df = pd.DataFrame(lista_resultados)
            
            # ORDENAMIENTO OFICIAL DE CARRERA:
            # 1. Más cantidad de vueltas (descendente)
            # 2. Menor tiempo total de carrera en caso de empate en vueltas (ascendente)
            df_ordenado = df.sort_values(
                by=["Vueltas", "Tiempo Total (ms)"], 
                ascending=[False, True]
            ).reset_index(drop=True)
            
            # Asignar posición final oficial
            df_ordenado.insert(0, "Pos", range(1, len(df_ordenado) + 1))
            
            # Convertir milisegundos a formato legible de minutos/segundos para el tiempo total
            def formatear_tiempo(ms):
                if ms == 0:
                    return "Sin tiempo"
                seg = ms / 1000.0
                m = int(seg // 60)
                s = seg % 60
                return f"{m:02d}:{s:06.3f}".replace(".", ",")

            df_ordenado["Tiempo Formateado"] = df_ordenado["Tiempo Total (ms)"].apply(formatear_tiempo)
            df_ordenado["Mejor Vuelta Formateada"] = df_ordenado["Mejor Vuelta (ms)"].apply(formatear_tiempo)
            
            st.success("¡Resultados de la carrera procesados con éxito!")
            
            # Mostrar tabla oficial de resultados
            st.subheader("🏆 Clasificación Oficial de la Carrera")
            columnas_visibles = ["Pos", "Piloto", "Auto", "Vueltas", "Tiempo Formateado", "Mejor Vuelta Formateada", "Lastre Actual (kg)"]
            st.dataframe(df_ordenado[columnas_visibles], use_container_width=True)
            
        else:
            st.warning("No se encontraron pilotos válidos en el archivo JSON.")
            
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo JSON: {e}")
else:
    st.info("Sube el archivo `.json` de la carrera para generar la clasificación.")