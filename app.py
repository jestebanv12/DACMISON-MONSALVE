import streamlit as st
import pandas as pd
import utilidades as util
import streamlit as st
from PIL import Image 
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="TPM",
    page_icon="Logo.png",
    layout="wide"
)

def main():
    st.title("Informe de Ventas 2024")
if __name__=="__main__":
    main()



def generar_menu():
    # Agregar una imagen en la parte superior del menú (sin contorno blanco)
    st.sidebar.image("TPM.png", use_container_width=True)  

    st.sidebar.title("📌 Menú Principal")

    # Opciones del menú con emojis o iconos
    opciones = {
        "🏠 Inicio": "inicio",
        "⚙️ Vendedores": "Vendedores",
        "ℹ️ Acerca de": "acerca"
    }

    # Crear botones en la barra lateral
    for nombre, clave in opciones.items():
        if st.sidebar.button(nombre):
            st.session_state["pagina"] = clave

    # Si no hay página seleccionada, establecer "inicio" por defecto
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "inicio"

    return st.session_state["pagina"]

# Uso en la aplicación
pagina = generar_menu()

if pagina == "inicio":
    st.title("🏠 Base de datos General")
    st.subheader("Ventas desde el 2021.")
    # Cargar datos desde CSV con limpieza de nombres
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python",index_col=None)  # Detectar separador automáticamente
        df.columns = df.columns.str.strip()  # Eliminar espacios antes y después en los nombres
        df.rename(columns=lambda x: x.strip(), inplace=True)  # Asegurar que no haya espacios oculto
        return df
    df = cargar_datos()
    # Verificar que el CSV tenga las columnas correctas
    columnas_requeridas = {"AÑO", "MES", "DIA", "TOTAL V","GRUPO TRES",}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"⚠️ El archivo CSV debe contener las columnas: {columnas_requeridas}")
    else:  
        # Convertir año a tipo entero para evitar problemas en los filtros
        df["AÑO"] = df["AÑO"].astype(int)

         # Seleccionar el año
        años_disponibles = sorted(df["AÑO"].dropna().unique(), reverse=True)
        año_seleccionado = st.selectbox("Selecciona un año:", ["Todos"] + list(map(str, años_disponibles)))

        if año_seleccionado == "Todos":
            df_filtrado = df.groupby("AÑO").agg({"TOTAL V": "sum"}).reset_index()
            df_filtrado["Crecimiento (%)"] = df_filtrado["TOTAL V"].pct_change() * 100
            df_filtrado["Crecimiento (%)"] = df_filtrado["Crecimiento (%)"].round(2)
            eje_x = "AÑO"
            titulo_grafica = "Ventas Anuales con Crecimiento (%)" 
            # Top 10 de GRUPO TRES
            df_top10 = df.groupby("GRUPO TRES").agg({"TOTAL V": "sum"}).reset_index()
        else:
            orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", 
                       "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            df["MES"] = df["MES"].str.upper()
            df["MES"] = pd.Categorical(df["MES"], categories=orden_meses, ordered=True)

            df_filtrado = df[df["AÑO"] == int(año_seleccionado)].groupby("MES").agg({"TOTAL V": "sum"}).reset_index()
            df_filtrado["Crecimiento (%)"] = df_filtrado["TOTAL V"].pct_change() * 100
            df_filtrado["Crecimiento (%)"] = df_filtrado["Crecimiento (%)"].round(2)
            titulo_grafica = f"Ventas Mensuales en {año_seleccionado} con Crecimiento (%)"
            eje_x = "MES"
            # Filtrar y obtener el Top 10 de GRUPO TRES
            df_top10 = df[df["AÑO"] == int(año_seleccionado)].groupby("GRUPO TRES").agg({"TOTAL V": "sum"}).reset_index()
        # Crear el gráfico con crecimiento incluido
        fig = px.bar(
            df_filtrado, 
            x=eje_x, 
            y="TOTAL V",
            text_auto="$,.0f",
            labels={"TOTAL V": "Total Ventas ($)", eje_x: eje_x},
            title=titulo_grafica,
            color="Crecimiento (%)",  # Solo la gráfica lo mostrará
            color_continuous_scale="Blues"
        )

        fig.update_traces(textposition="outside")

        # Mostrar gráfico en Streamlit
        st.plotly_chart(fig, use_container_width=True)

        # Mostrar el top 10 de "GRUPO TRES" SIN crecimiento
        df_top10 = df_top10.sort_values(by="TOTAL V", ascending=False).head(10)
        st.write(f"### Top 10 'GRUPO TRES' por Ventas en {año_seleccionado}")
        st.dataframe(df_top10[["GRUPO TRES", "TOTAL V"]],hide_index=True)  # Excluir "Crecimiento (%)"
    
elif pagina == "Vendedores":
    st.title("⚙️ Ventas por vendedor")
    
    # Cargar datos
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", dtype={"AÑO": str, "MES": str, "DIA": str})
        df.columns = df.columns.str.strip()
        df.rename(columns=lambda x: x.strip(), inplace=True)
        return df

    df = cargar_datos()

    # Verificar que el archivo CSV tenga las columnas correctas
    columnas_requeridas = {"AÑO", "MES", "DIA", "TOTAL V", "VENDEDOR", "DPTO", "CIUDAD", "RAZON SOCIAL", "REFERENCIA"}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"El archivo CSV debe contener las columnas exactas: {columnas_requeridas}")
    else:
        st.subheader("📊 Informe de Ventas")
    
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            vendedor_seleccionado = st.selectbox("Vendedor", ["Todos"] + sorted(df["VENDEDOR"].dropna().unique().tolist()))
        with col2:
            año_seleccionado = st.selectbox("Año", ["Todos"] + sorted(df["AÑO"].unique()))
        with col3:
            dpto_seleccionado = st.selectbox("Departamento", ["Todos"] + sorted(df["DPTO"].dropna().unique().tolist()))
        with col4:
            ciudades_disponibles = df[df["DPTO"] == dpto_seleccionado]["CIUDAD"].dropna().unique().tolist() if dpto_seleccionado != "Todos" else sorted(df["CIUDAD"].dropna().unique().tolist())
            ciudad_seleccionada = st.selectbox("Ciudad", ["Todos"] + sorted(ciudades_disponibles))
    
        # Filtrar datos según selección
        df_filtrado = df.copy()
    
        if vendedor_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["VENDEDOR"] == vendedor_seleccionado]
    
        if año_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["AÑO"] == año_seleccionado]
    
        if dpto_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["DPTO"] == dpto_seleccionado]
    
        if ciudad_seleccionada != "Todos":
            df_filtrado = df_filtrado[df_filtrado["CIUDAD"] == ciudad_seleccionada]
    
        # Definir agrupación según selección
        if vendedor_seleccionado == "Todos":
            df_agrupado = df_filtrado.groupby("AÑO").agg({"TOTAL V": "sum"}).reset_index()
            eje_x = "AÑO"
            titulo_grafica = "Ventas Totales de la Empresa"
        elif año_seleccionado == "Todos":
            df_agrupado = df_filtrado.groupby("AÑO").agg({"TOTAL V": "sum"}).reset_index()
            eje_x = "AÑO"
            titulo_grafica = f"Ventas de {vendedor_seleccionado} por Año"
        else:
            orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            df_filtrado["MES"] = pd.Categorical(df_filtrado["MES"], categories=orden_meses, ordered=True)
            df_agrupado = df_filtrado.groupby("MES").agg({"TOTAL V": "sum"}).reset_index()
            eje_x = "MES"
            titulo_grafica = f"Ventas de {vendedor_seleccionado} en {año_seleccionado}"
    
        # Mostrar gráfico
        fig = px.bar(df_agrupado, x=eje_x, y="TOTAL V", title=titulo_grafica, text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
    
        # Mostrar tablas Top 10 lado a lado
        col5, col6 = st.columns(2)
    
        with col5:
            st.subheader("🏆 Top 10 RAZON SOCIAL")
            df_top_razon = df_filtrado.groupby("RAZON SOCIAL").agg({"TOTAL V": "sum"}).reset_index().sort_values(by="TOTAL V", ascending=False).head(10)
            st.write(df_top_razon.set_index("RAZON SOCIAL"))
    
        with col6:
            st.subheader("🏆 Top 10 REFERENCIA")
            df_top_referencia = df_filtrado.groupby("REFERENCIA").agg({"TOTAL V": "sum"}).reset_index().sort_values(by="TOTAL V", ascending=False).head(10)
            st.write(df_top_referencia.set_index("REFERENCIA"))
    
        # Mostrar Top 10 de Departamentos o Ciudades debajo
        st.subheader("🏆 Top 10 por Ubicación")
    
        if dpto_seleccionado == "Todos":
            df_top_dpto = df_filtrado.groupby("DPTO").agg({"TOTAL V": "sum"}).reset_index().sort_values(by="TOTAL V", ascending=False).head(10)
            st.write(df_top_dpto.set_index("DPTO"))
        else:
            df_top_ciudades = df_filtrado.groupby("CIUDAD").agg({"TOTAL V": "sum"}).reset_index().sort_values(by="TOTAL V", ascending=False).head(10)
            st.write(df_top_ciudades.set_index("CIUDAD"))
elif pagina == "acerca":
    st.title("ℹ️ Acerca de")
    st.write("Aplicación creada con Streamlit.")





