import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import date

# Configuración
st.set_page_config(page_title="Workout Tracker", layout="centered")
st.title("Workout Tracker")

# Motor de Base de Datos Local (CSV Estándar)
ARCHIVO_CSV = 'historial.csv'

if not os.path.exists(ARCHIVO_CSV):
    df_vacio = pd.DataFrame(columns=['fecha', 'ejercicio', 'peso', 'reps'])
    df_vacio.to_csv(ARCHIVO_CSV, index=False)

# Memoria dinámica de ejercicios (CORREGIDO: Ahora lee estrictamente del CSV)
df_actual = pd.read_csv(ARCHIVO_CSV)
lista_ejercicios = sorted(df_actual['ejercicio'].unique().tolist()) if not df_actual.empty else []

# --- INTERFAZ EN TIEMPO REAL ---
with st.container(border=True):
    opciones_menu = lista_ejercicios + ["➕ Agregar nuevo", "🗑️ Eliminar un ejercicio"]
    ejercicio_seleccionado = st.selectbox("Ejercicio", opciones_menu)
    
    # 1. MODO ELIMINAR EJERCICIO
    if ejercicio_seleccionado == "🗑️ Eliminar un ejercicio":
        st.warning("⚠️ Al eliminar un ejercicio, se borrará todo su historial asociado y desaparecerá de la lista.")
        if len(lista_ejercicios) == 0:
            st.info("No hay ejercicios registrados en la base de datos.")
        else:
            ej_a_borrar = st.selectbox("Selecciona el ejercicio a purgar:", lista_ejercicios)
            if st.button("❌ Confirmar Eliminación", use_container_width=True, type="primary"):
                df_limpio = df_actual[df_actual["ejercicio"] != ej_a_borrar]
                df_limpio.to_csv(ARCHIVO_CSV, index=False)
                st.success(f"Ejercicio '{ej_a_borrar}' eliminado por completo.")
                st.rerun()

    # 2. MODO REGISTRO (Agregar nuevo o seleccionar existente)
    else:
        ejercicio_final = ""
        if ejercicio_seleccionado == "➕ Agregar nuevo":
            ejercicio_final = st.text_input("Escribe el nombre del nuevo ejercicio:")
        else:
            ejercicio_final = ejercicio_seleccionado
        
        col1, col2, col3 = st.columns(3)
        fecha_input = col1.date_input("Fecha", value=date.today(), format="DD/MM/YYYY")
        peso = col2.number_input("Peso (kg)", min_value=0.0, step=2.5)
        reps = col3.number_input("Reps", min_value=1, step=1)
        
        if st.button("Guardar Serie", use_container_width=True, type="primary"):
            nombre_ejercicio = ejercicio_final.strip().title()
            
            if nombre_ejercicio == "":
                st.error("Por favor, escribe un nombre válido para el ejercicio.")
            else:
                nueva_fila = pd.DataFrame({
                    'fecha': [fecha_input.strftime('%Y-%m-%d')], 
                    'ejercicio': [nombre_ejercicio], 
                    'peso': [peso], 
                    'reps': [reps]
                })
                nueva_fila.to_csv(ARCHIVO_CSV, mode='a', header=False, index=False)
                st.success(f"Serie de {nombre_ejercicio} registrada.")
                st.rerun()

st.divider()

# Extracción de Datos para Gráficos y Tabla
df = pd.read_csv(ARCHIVO_CSV)

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
        rm_estimado = mejor_serie['peso'] * (36 / (37 - mejor_serie['reps']))
        st.info(f"**1RM Estimado Actual: {rm_estimado:.1f} kg**")
        
    st.divider()
    st.subheader("Modificar Historial")
    st.caption("Haz doble clic para editar celdas. En PC selecciona la fila y pulsa Suprimir; en celular marca la casilla izquierda de la fila y usa la papelera superior. Guarda para aplicar.")
    
    df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("Guardar Cambios de la Tabla", use_container_width=True):
        df_editado.to_csv(ARCHIVO_CSV, index=False)
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