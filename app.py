import streamlit as st
import pandas as pd
import altair as alt
from datetime import date

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Workout Tracker", layout="centered")
st.title("Workout Tracker")

# --- OCULTAR INTERFAZ NATIVA DE STREAMLIT ---
ocultar_menu = """
    <style>
    #MainMenu {display: none !important;}
    header {display: none !important;}
    footer {display: none !important;}
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {display: none !important;}
    </style>
    """
st.markdown(ocultar_menu, unsafe_allow_html=True)

ARCHIVO_CSV = 'historial.csv'

# --- FUNCIONES OPTIMIZADAS ---

def cargar_datos():
    """
    Intenta leer la base de datos CSV. Si el archivo no existe,
    crea un DataFrame vacío, genera el archivo físico y lo retorna.
    """
    try:
        return pd.read_csv(ARCHIVO_CSV)
    except FileNotFoundError:
        df_vacio = pd.DataFrame(columns=['fecha', 'ejercicio', 'peso', 'reps'])
        df_vacio.to_csv(ARCHIVO_CSV, index=False)
        return df_vacio

def guardar_datos(dataframe):
    """
    Sobrescribe el archivo CSV por completo con la tabla actual.
    """
    dataframe.to_csv(ARCHIVO_CSV, index=False)

def calcular_1rm(peso, reps):
    """
    Aplica la fórmula matemática de Brzycki para estimar la 1RM.
    """
    return peso * (36 / (37 - reps))

# --- INICIALIZACIÓN UNIFICADA ---
df = cargar_datos()
lista_ejercicios = sorted(df['ejercicio'].unique().tolist()) if not df.empty else []

# --- 1. REGISTRO Y GESTIÓN EN TIEMPO REAL ---
with st.container(border=True):
    opciones_menu = lista_ejercicios + ["➕ Agregar nuevo", "🗑️ Eliminar un ejercicio"]
    ejercicio_seleccionado = st.selectbox("Ejercicio", opciones_menu)
    
    # MODO ELIMINACIÓN
    if ejercicio_seleccionado == "🗑️ Eliminar un ejercicio":
        st.warning("⚠️ Al eliminar un ejercicio, se borrará todo su historial asociado y desaparecerá de la lista.")
        
        if not lista_ejercicios:
            st.info("No hay ejercicios registrados en la base de datos.")
        else:
            ej_a_borrar = st.selectbox("Selecciona el ejercicio a purgar:", lista_ejercicios)
            if st.button("❌ Confirmar Eliminación", use_container_width=True, type="primary"):
                df_limpio = df[df["ejercicio"] != ej_a_borrar]
                guardar_datos(df_limpio)
                st.success(f"Ejercicio '{ej_a_borrar}' eliminado por completo.")
                st.rerun()

    # MODO REGISTRO
    else:
        ejercicio_final = st.text_input("Escribe el nombre del nuevo ejercicio:") if ejercicio_seleccionado == "➕ Agregar nuevo" else ejercicio_seleccionado
        
        col1, col2, col3 = st.columns(3)
        fecha_input = col1.date_input("Fecha", value=date.today(), format="DD/MM/YYYY")
        peso = col2.number_input("Peso (kg)", min_value=0.0, step=2.5)
        reps = col3.number_input("Reps", min_value=1, step=1)
        
        if st.button("Guardar Serie", use_container_width=True, type="primary"):
            nombre_ejercicio = ejercicio_final.strip().title()
            
            if not nombre_ejercicio:
                st.error("Por favor, escribe un nombre válido para el ejercicio.")
            else:
                nueva_fila = pd.DataFrame([{
                    'fecha': fecha_input.strftime('%Y-%m-%d'), 
                    'ejercicio': nombre_ejercicio, 
                    'peso': peso, 
                    'reps': reps
                }])
                nueva_fila.to_csv(ARCHIVO_CSV, mode='a', header=False, index=False)
                st.success(f"Serie de {nombre_ejercicio} registrada.")
                st.rerun()

st.divider()

# --- 2. ANÁLISIS DE PROGRESO Y EDICIÓN ---
if not df.empty:
    st.subheader("Análisis de Progreso")
    ejercicio_filtro = st.selectbox("Ver progreso de:", df['ejercicio'].unique())
    df_filtrado = df[df['ejercicio'] == ejercicio_filtro].copy()
    
    if not df_filtrado.empty:
        df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'], format='mixed')
        
        max_peso = df_filtrado['peso'].max()
        limite_superior = max_peso + 20 if pd.notna(max_peso) else 100

        grafico = alt.Chart(df_filtrado).mark_line(point=alt.OverlayMarkDef(size=100)).encode(
            x=alt.X('fecha:T', title='Fecha', axis=alt.Axis(format='%d/%m/%y', labelAngle=0), scale=alt.Scale(padding=30)), 
            y=alt.Y('peso:Q', scale=alt.Scale(domain=[0, limite_superior]), title='Peso (kg)'),
            tooltip=[alt.Tooltip('fecha:T', format='%d/%m/%y', title='Fecha'), 'peso', 'reps']
        ).interactive()
        
        st.altair_chart(grafico, use_container_width=True)
        
        mejor_serie = df_filtrado.loc[df_filtrado['peso'].idxmax()]
        rm_estimado = calcular_1rm(mejor_serie['peso'], mejor_serie['reps'])
        st.info(f"**1RM Estimado Actual: {rm_estimado:.1f} kg**")
        
    st.divider()
    st.subheader("Modificar Historial")
    st.caption("Visualiza y modifica tu historial de entrenamiento.")
    
    df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("Guardar Cambios de la Tabla", use_container_width=True):
        guardar_datos(df_editado)
        st.success("Historial actualizado correctamente.")
        st.rerun()

    st.divider()
    csv_export = df.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
    st.download_button(
        label="📥 Descargar Historial (Para Excel)",
        data=csv_export,
        file_name='historial_entrenamiento.csv',
        mime='text/csv'
    )
else:
    st.write("Registra tu primera serie para comenzar.")