import streamlit as st
import pandas as pd
import utilidades as util
import streamlit as st
from PIL import Image 
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt


st.set_page_config(
    page_title="TPM",
    page_icon="Logo.png",
    layout="wide"
)

def main():
    st.title("Informe de Ventas 2025")
if __name__=="__main__":
    main()



def generar_menu():
    # Agregar una imagen en la parte superior del menú (sin contorno blanco)
    st.sidebar.image("TPM.png", use_container_width=True)  

    st.sidebar.title("📌 Menú Principal")

    # Opciones del menú con emojis o iconos
    opciones = {
        "🏠 Inicio": "inicio",
        "👩‍🏭 Vendedores": "Vendedores",
        "ℹ️ Cliente": "clientes",
        "⚙️ Referencias":"Referencias",
        "💯TPM":"TPM"
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
    st.subheader("Ventas desde el 2022.")
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
        color="Crecimiento (%)",
        color_continuous_scale="greens"
    )
    fig.update_traces(textposition="outside")

    # Formato de eje X para valores enteros (cuando son años)
    if eje_x == "AÑO":
        fig.update_xaxes(tickformat="d", type="category")  # Formato entero y tratarlo como categoría

    st.plotly_chart(fig, use_container_width=True)

    # Mostrar el top 10 de "GRUPO TRES" SIN crecimiento
    df_top10 = df_top10.sort_values(by="TOTAL V", ascending=False).head(10)
    df_top10["TOTAL V"] = df_top10["TOTAL V"].apply(lambda x: f"${x:,.2f}")  # Formatear como moneda

    st.write(f"### Top 10 'GRUPO TRES' por Ventas en {año_seleccionado}")
    st.dataframe(df_top10[["GRUPO TRES", "TOTAL V"]], hide_index=True) 
    
elif pagina == "Vendedores":
    st.title("👩‍🏭 Ventas por vendedor")
    
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
        # Formatear los valores como moneda
        df_agrupado["TOTAL V"] = pd.to_numeric(df_agrupado["TOTAL V"], errors="coerce")  # Asegurar que es numérico

        fig = px.bar(
            df_agrupado, 
            x=eje_x, 
            y="TOTAL V", 
            title=titulo_grafica, 
            text_auto=True
)

        # Formato de moneda en las etiquetas
        fig.update_traces(texttemplate="$%{y:,.2f} ", textposition="outside")

        # Formato de moneda en el eje Y
        fig.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",", xaxis_title=eje_x, yaxis_title="Ventas ($)")

        st.plotly_chart(fig, use_container_width=True)
    
        # Mostrar tablas Top 10 lado a lado
        col5, col6 = st.columns(2,gap="large")
    
        with col5:
            # Mostrar Top 10 de Departamentos o Ciudades debajo
            st.subheader("🏆 Top 10 por Ubicación")

            # Función para aplicar estilos en la tabla
            def estilo_dataframe(df):
                return df.style.set_properties(**{
                "text-align": "left",  # Alinear todo a la izquierda
                "white-space": "nowrap"  # Ajustar ancho de la primera columna
                }).format({"TOTAL V": "$ {:,.2f}"})  # Formato moneda

            if dpto_seleccionado == "Todos":
                df_top_dpto = df_filtrado.groupby("DPTO").agg({"TOTAL V": "sum"}).reset_index().sort_values(by="TOTAL V", ascending=False).head(10)
                st.dataframe(estilo_dataframe(df_top_dpto), hide_index=True, use_container_width=True)

            else:
                df_top_ciudades = df_filtrado.groupby("CIUDAD").agg({"TOTAL V": "sum"}).reset_index().sort_values(by="TOTAL V", ascending=False).head(10)
                st.dataframe(estilo_dataframe(df_top_ciudades), hide_index=True, use_container_width=True)   
        with col6:
            st.subheader("🏆 Top 10 REFERENCIA")

            # Agrupar y ordenar datos
            df_top_referencia = df_filtrado.groupby("REFERENCIA").agg({"TOTAL V": "sum"}).reset_index()
            df_top_referencia = df_top_referencia.sort_values(by="TOTAL V", ascending=False).head(10)

            # Formatear columna "TOTAL V" con signo de moneda adelante
            df_top_referencia["TOTAL V"] = df_top_referencia["TOTAL V"].apply(lambda x: f"${x:,.2f}")

            # Aplicar estilos para autoajustar columnas
            st.dataframe(
            df_top_referencia.set_index("REFERENCIA").style.set_properties(**{
            "text-align": "left",  # Alinear a la izquierda
            "white-space": "nowrap"  # Evitar saltos de línea
    }),
            hide_index=False,  # Mantener encabezado de "REFERENCIA"
            use_container_width=True  # Ajustar al ancho disponible
)
    
        # Mostrar Top 10 de Departamentos o Ciudades debajo
        st.markdown("<h3 style='text-align: center;'>🏆 Top 10 RAZON SOCIAL</h3>", unsafe_allow_html=True)    

        # Agrupar y ordenar datos
        df_top_razon = df_filtrado.groupby("RAZON SOCIAL").agg({"TOTAL V": "sum"}).reset_index()
        df_top_razon = df_top_razon.sort_values(by="TOTAL V", ascending=False).head(10)

        # Formatear columna "TOTAL V" con signo de moneda adelante
        df_top_razon["TOTAL V"] = df_top_razon["TOTAL V"].apply(lambda x: f"${x:,.2f}")

        # Aplicar estilos para autoajustar columnas y usar todo el ancho
        st.dataframe(
         df_top_razon.set_index("RAZON SOCIAL").style.set_properties(**{
        "text-align": "left",  # Alinear texto a la izquierda
        "white-space": "nowrap"  # Evitar saltos de línea
    }),
        hide_index=False,  # Mantener encabezado de "RAZON SOCIAL"
        use_container_width=True  # Ajustar al ancho disponible
) 
elif pagina == "clientes":
    st.title("ℹ️ Clientes")
    
    # Cargar datos
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", dtype={"AÑO": str, "MES": str, "DIA": str})
        df.columns = df.columns.str.strip()
        df.rename(columns=lambda x: x.strip(), inplace=True)
        return df

    df = cargar_datos()

    # Verificar que el archivo CSV tenga las columnas correctas
    columnas_requeridas = {"AÑO", "MES", "DIA", "TOTAL V", "RAZON SOCIAL", "REFERENCIA"}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"El archivo CSV debe contener las columnas exactas: {columnas_requeridas}")
    else:
        st.subheader("📊 Informe de Ventas", divider="blue")
    
        col1, col2 = st.columns([2,1])
        with col1:
            razon_social_seleccionada = st.selectbox("Buscar Razón Social", [""] + sorted(df["RAZON SOCIAL"].unique()), index=0)
        with col2:
            año_seleccionado = st.selectbox("Año", ["Todos"] + sorted(df["AÑO"].unique()))
    
        # Filtrar datos según selección
        df_filtrado = df.copy()
    
        if razon_social_seleccionada:
            df_filtrado = df_filtrado[df_filtrado["RAZON SOCIAL"].str.contains(razon_social_seleccionada, case=False, na=False)]
    
        if año_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["AÑO"] == año_seleccionado]
    
        # Mostrar Top 10 de Referencias
        st.subheader("🏆 Top 10 REFERENCIA")
        df_top_referencia = df_filtrado.groupby("REFERENCIA").agg({"TOTAL V": "sum"}).reset_index().sort_values(by="TOTAL V", ascending=False).head(10)
        df_top_referencia["TOTAL V"] = df_top_referencia["TOTAL V"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_top_referencia.set_index("REFERENCIA"), use_container_width=True)
    
        # Mostrar Gráficos si se selecciona Razón Social
if razon_social_seleccionada:
    st.subheader("📈 Ventas de la Razón Social")

    if df_filtrado.empty:
        st.warning("No hay datos para mostrar en la gráfica.")
    else:
        if año_seleccionado == "Todos":
            df_grafico = df_filtrado.groupby("AÑO").agg({"TOTAL V": "sum"}).reset_index()
            df_grafico["AÑO"] = df_grafico["AÑO"].astype(str)
            x_axis = "AÑO"
        else:
            # Ordenar meses
            orden_meses = [
                "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
            ]
            # Normalizar nombres de meses
            df_filtrado["MES"] = df_filtrado["MES"].str.strip().str.upper()
            df_filtrado["MES"] = pd.Categorical(df_filtrado["MES"], categories=orden_meses, ordered=True)

            df_grafico = df_filtrado.groupby("MES").agg({"TOTAL V": "sum"}).reset_index()
            x_axis = "MES"

        # Verificamos si hay datos reales para graficar
        if df_grafico["TOTAL V"].sum() == 0:
            st.warning("No hay ventas registradas para esta selección.")
        else:
            fig_bar = px.bar(
                df_grafico,
                x=x_axis,
                y="TOTAL V",
                title="Ventas por Periodo",
                text_auto=True,
                color_discrete_sequence=["green"]
            )
            fig_bar.update_traces(texttemplate="$%{y:,.2f}", textposition="outside")
            fig_bar.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
            st.plotly_chart(fig_bar, use_container_width=True)


            # Asegurar que el eje X de los años no tenga valores intermedios
            if x_axis == "AÑO":
                fig_bar.update_xaxes(type="category")  # Forzar eje X como categórico
    
                st.plotly_chart(fig_bar, use_container_width=True)


if pagina == "Referencias":
    st.title("⚙️ Referencias")
    # Cargar datos
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", dtype={"AÑO": str, "MES": str, "DIA": str})
        df.columns = df.columns.str.strip()
        df.rename(columns=lambda x: x.strip(), inplace=True)
        return df

    df = cargar_datos()

    # Verificar que el archivo CSV tenga las columnas correctas
    columnas_requeridas = {"AÑO", "MES", "DIA", "TOTAL V", "RAZON SOCIAL", "REFERENCIA"}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"El archivo CSV debe contener las columnas exactas: {columnas_requeridas}")
    else:
        st.subheader("📊 Informe de Ventas", divider="blue")
    
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            referencia_seleccionada = st.selectbox("Buscar Referencia", [""] + sorted(df["REFERENCIA"].unique()), index=0)
        with col2:
            razon_social_seleccionada = st.selectbox("Buscar Razón Social", [""] + sorted(df["RAZON SOCIAL"].unique()), index=0)
        with col3:
            año_seleccionado = st.selectbox("Año", ["Todos"] + sorted(df["AÑO"].astype(int).unique()))
    
        # Filtrar datos según selección
        df_filtrado = df.copy()
    
        if referencia_seleccionada:
            df_filtrado = df_filtrado[df_filtrado["REFERENCIA"].str.contains(referencia_seleccionada, case=False, na=False)]
    
        if razon_social_seleccionada:
            df_filtrado = df_filtrado[df_filtrado["RAZON SOCIAL"].str.contains(razon_social_seleccionada, case=False, na=False)]
    
        if año_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["AÑO"].astype(int) == int(año_seleccionado)]
    
        # Si se selecciona una referencia y un año, mostrar tabla
        if referencia_seleccionada and año_seleccionado != "Todos":
            st.subheader("📊 Ventas de la Referencia en el Año")
            df_ref_año = df_filtrado.groupby(["AÑO", "MES"]).agg({"TOTAL V": "sum"}).reset_index()
            df_ref_año["TOTAL V"] = df_ref_año["TOTAL V"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df_ref_año, use_container_width=True)
    
        # Si no se selecciona referencia, mostrar Top 10
        else:
            st.subheader("🏆 Top 10 REFERENCIA")
            df_top_referencia = df_filtrado.groupby("REFERENCIA").agg({"TOTAL V": "sum"}).reset_index().sort_values(by="TOTAL V", ascending=False).head(10)
            df_top_referencia["TOTAL V"] = df_top_referencia["TOTAL V"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df_top_referencia.set_index("REFERENCIA"), use_container_width=True)
    
        # Mostrar gráficos si se selecciona Razón Social
        if razon_social_seleccionada:
            st.subheader("📊 Ventas de la Razón Social")
            df_filtrado["AÑO"] = df_filtrado["AÑO"].astype(int)
            df_grafico = df_filtrado.groupby("AÑO" if año_seleccionado == "Todos" else "MES").agg({"TOTAL V": "sum"}).reset_index()
            x_axis = "AÑO" if año_seleccionado == "Todos" else "MES"
    
            # Convert to string to treat as category
            df_grafico[x_axis] = df_grafico[x_axis].astype(str)
    
            fig = px.bar(df_grafico, x=x_axis, y="TOTAL V", color_discrete_sequence=['blue'])
    
            # Force categorical axis
            fig.update_xaxes(type='category')
    
            st.plotly_chart(fig, use_container_width=True)
if pagina == "TPM":
    # Cargar datos
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", dtype={"AÑO": str, "MES": str})
        df.columns = df.columns.str.strip()
        df.rename(columns=lambda x: x.strip(), inplace=True)

        # Convertir nombres de meses a números si es necesario
        meses_dict = {
            "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
            "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
        }

        # Normalizar nombres de meses a números si están en texto
        if df["MES"].dtype == object:
            df["MES"] = df["MES"].str.upper().map(meses_dict)

        # Convertir columnas numéricas correctamente
        df["AÑO"] = df["AÑO"].astype(float).astype(int)
        df["MES"] = pd.to_numeric(df["MES"], errors="coerce").fillna(0).astype(int)
        df["TOTAL V"] = pd.to_numeric(df["TOTAL V"], errors="coerce").fillna(0)
        df["TOTAL C"] = pd.to_numeric(df["TOTAL C"], errors="coerce").fillna(0)

        # Filtrar meses válidos
        df = df[df["MES"].between(1, 12)]

        return df

    df = cargar_datos()

    # Verificar columnas
    columnas_requeridas = {"AÑO", "MES", "TOTAL V", "TOTAL C"}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"El archivo CSV debe contener las columnas exactas: {columnas_requeridas}")
    else:
        st.subheader("📊 Ventas y Costos Totales", divider="blue")

        # Selector de año
        opciones_año = ["Todos"] + sorted(df["AÑO"].unique())
        año_seleccionado = st.selectbox("Seleccione un año", opciones_año)

        # Filtrar datos
        df_filtrado = df if año_seleccionado == "Todos" else df[df["AÑO"] == int(año_seleccionado)]

        # Verificar si hay datos después del filtrado
        if df_filtrado.empty:
            st.warning("No hay datos disponibles para esta selección.")
        else:
            # Mapear meses de números a nombres
            meses_map = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
            df_filtrado["MES"] = df_filtrado["MES"].map(meses_map)

            # Agrupar datos
            x_axis = "AÑO" if año_seleccionado == "Todos" else "MES"
            df_grafico = df_filtrado.groupby(x_axis).agg({"TOTAL V": "sum", "TOTAL C": "sum"}).reset_index()

            # Ordenar los meses correctamente si se elige un solo año
            if x_axis == "MES":
                df_grafico["MES"] = pd.Categorical(df_grafico["MES"], categories=meses_map.values(), ordered=True)
                df_grafico = df_grafico.sort_values("MES")

            # Gráfico de áreas con ventas por encima de costos
        # Gráfico de áreas
    # Gráfico de áreas con orden corregido (ventas encima de costos)
    fig_area = px.area(df_grafico, x=x_axis, y=["TOTAL C", "TOTAL V"],  # Invertimos el orden
                   title="Ventas y Costos Totales", labels={"value": "Monto ($)"},
                   color_discrete_sequence=["#ff7f0e", "#1f77b4"])  # Colores personalizados

    # Forzar años enteros en el eje X
    fig_area.update_xaxes(tickmode="array", tickvals=df_grafico[x_axis].unique(), tickformat=".0f")
    # Formatear el eje Y para mostrar valores en millones con "M"
    fig_area.update_layout(
    yaxis=dict(
        tickformat=",.0f",  # Formato de número entero sin decimales
        title="Monto ($ Millones)"  # Etiqueta del eje Y
    )
    )

    st.plotly_chart(fig_area, use_container_width=True)