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
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", index_col=None)
        df.columns = df.columns.str.strip()
        df.rename(columns=lambda x: x.strip(), inplace=True)
        return df

    df = cargar_datos()

    columnas_requeridas = {"AÑO", "MES", "DIA", "TOTAL V", "GRUPO TRES", "GRUPO CUATRO"}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"⚠️ El archivo CSV debe contener las columnas: {columnas_requeridas}")
    else:
        df["AÑO"] = df["AÑO"].astype(int)

        años_disponibles = sorted(df["AÑO"].dropna().unique(), reverse=True)
        año_seleccionado = st.selectbox("Selecciona un año:", ["Todos"] + list(map(str, años_disponibles)))

        if año_seleccionado == "Todos":
            df_filtrado = df.groupby("AÑO").agg({"TOTAL V": "sum"}).reset_index()
            df_filtrado["Crecimiento (%)"] = df_filtrado["TOTAL V"].pct_change() * 100
            df_filtrado["Crecimiento (%)"] = df_filtrado["Crecimiento (%)"].round(2)
            eje_x = "AÑO"
            titulo_grafica = "Ventas Anuales con Crecimiento (%)"

            top_grupo3 = df.groupby(["GRUPO TRES", "AÑO"]).agg({"TOTAL V": "sum"}).reset_index()
            top_grupo3 = top_grupo3.pivot(index="GRUPO TRES", columns="AÑO", values="TOTAL V").fillna(0)
            top_grupo3 = top_grupo3.assign(TOTAL=top_grupo3.sum(axis=1)).nlargest(10, "TOTAL").drop(columns="TOTAL")

            top_grupo4 = df.groupby(["GRUPO CUATRO", "AÑO"]).agg({"TOTAL V": "sum"}).reset_index()
            top_grupo4 = top_grupo4.pivot(index="GRUPO CUATRO", columns="AÑO", values="TOTAL V").fillna(0)
            top_grupo4 = top_grupo4.assign(TOTAL=top_grupo4.sum(axis=1)).nlargest(20, "TOTAL").drop(columns="TOTAL")

        else:
            df["MES"] = df["MES"].str.upper()
            orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                       "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            df["MES"] = pd.Categorical(df["MES"], categories=orden_meses, ordered=True)

            df_filtrado = df[df["AÑO"] == int(año_seleccionado)].groupby("MES").agg({"TOTAL V": "sum"}).reset_index()
            df_filtrado["Crecimiento (%)"] = df_filtrado["TOTAL V"].pct_change() * 100
            df_filtrado["Crecimiento (%)"] = df_filtrado["Crecimiento (%)"].round(2)
            titulo_grafica = f"Ventas Mensuales en {año_seleccionado} con Crecimiento (%)"
            eje_x = "MES"

            df_filtrado_ano = df[df["AÑO"] == int(año_seleccionado)]
            top_grupo3 = df_filtrado_ano.groupby(["GRUPO TRES", "MES"]).agg({"TOTAL V": "sum"}).reset_index()
            top_grupo3 = top_grupo3.pivot(index="GRUPO TRES", columns="MES", values="TOTAL V").fillna(0)
            top_grupo3 = top_grupo3.assign(TOTAL=top_grupo3.sum(axis=1)).nlargest(10, "TOTAL").drop(columns="TOTAL")

            top_grupo4 = df_filtrado_ano.groupby(["GRUPO CUATRO", "MES"]).agg({"TOTAL V": "sum"}).reset_index()
            top_grupo4 = top_grupo4.pivot(index="GRUPO CUATRO", columns="MES", values="TOTAL V").fillna(0)
            top_grupo4 = top_grupo4.assign(TOTAL=top_grupo4.sum(axis=1)).nlargest(20, "TOTAL").drop(columns="TOTAL")

        # Crear gráfico
        fig = px.bar(
            df_filtrado,
            x=eje_x,
            y="TOTAL V",
            text=df_filtrado["Crecimiento (%)"].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else ""),
            labels={"TOTAL V": "Total Ventas ($)", eje_x: eje_x},
            title=titulo_grafica,
            color_discrete_sequence=["#2ecc71"]
        )

        fig.update_traces(
            textposition="inside",
            textfont=dict(color="white", size=12)
        )

        fig.update_xaxes(
            type="category",
            title_text=eje_x,
            tickfont=dict(size=12)
        )

        # Formato del eje Y: miles en formato "100M"
        max_y = df_filtrado["TOTAL V"].max()
        tick_step = 500_000_000 if max_y > 1_000_000_000 else 100_000_000
        tick_vals = list(range(0, int(max_y + tick_step), int(tick_step)))
        tick_texts = [f"{int(val/1_000_000)}M" for val in tick_vals]

        fig.update_yaxes(
            title_text="Total Ventas ($)",
            tickvals=tick_vals,
            ticktext=tick_texts
        )

        fig.update_layout(
            uniformtext_minsize=8,
            uniformtext_mode="hide",
            plot_bgcolor="#f9f9f9",
            title_font_size=18
        )

        st.plotly_chart(fig, use_container_width=True)

        # ---------- Tablas de top formateadas ----------
        def formatear_tabla_moneda(df_tabla):
            df_fmt = df_tabla.reset_index().copy()
            # Renombrar la columna del índice si es necesario
            if 'index' in df_fmt.columns:
                df_fmt.rename(columns={'index': 'GRUPO TRES'}, inplace=True)
    
            # Formatear valores como moneda
            for col in df_fmt.columns[1:]:
                df_fmt[col] = df_fmt[col].apply(lambda x: f"${x:,.0f}")
    
            return df_fmt

        styled_top3 = formatear_tabla_moneda(top_grupo3)
        styled_top4 = formatear_tabla_moneda(top_grupo4)

        # CSS personalizado para insertar en la página
        css = """
        <style>
            .dataframe th {
                text-align: center !important;
                font-weight: bold !important;
                background-color: #f0f2f6 !important;
            }
            .dataframe td {
                text-align: right !important;
            }
            .dataframe td:first-child {
                text-align: left !important;
            }
        </style>
        """

        # Inyectar CSS personalizado
        st.markdown(css, unsafe_allow_html=True)

        st.subheader(f"\U0001F3C6 Top 10 'GRUPO TRES' por Ventas en {año_seleccionado}")
        st.dataframe(styled_top3, hide_index=True, use_container_width=True)

        st.subheader(f"\U0001F3C5 Top 20 'GRUPO CUATRO' por Ventas en {año_seleccionado}")
        st.dataframe(styled_top4, hide_index=True, use_container_width=True)
    
elif pagina == "Vendedores":
    st.title("👩‍🏭 Ventas por vendedor")
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python")
        df.columns = df.columns.str.strip()
        df["TOTAL V"] = pd.to_numeric(df["TOTAL V"], errors="coerce")
        df["AÑO"] = pd.to_numeric(df["AÑO"], errors="coerce")
        return df

    df = cargar_datos()
    df["MES"] = df["MES"].astype(str).str.strip().str.upper()
    # Validar columnas necesarias
    columnas_requeridas = {"AÑO", "MES", "DIA", "TOTAL V", "GRUPO TRES"}
    if not columnas_requeridas.issubset(df.columns):
        st.error(f"Faltan columnas requeridas: {columnas_requeridas - set(df.columns)}")
        st.stop()

    # Filtros
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        vendedor_seleccionado = st.selectbox("Vendedor", ["Todos"] + sorted(df["VENDEDOR"].dropna().unique()))

    with col2:
        años_disponibles = sorted(df["AÑO"].dropna().unique())
        año_seleccionado = st.selectbox("Año", ["Todos"] + list(map(str, años_disponibles)))

    with col3:
        dpto_seleccionado = st.selectbox("Departamento", ["Todos"] + sorted(df["DPTO"].dropna().unique()))

    with col4:
        ciudades_disponibles = (
            df[df["DPTO"] == dpto_seleccionado]["CIUDAD"].dropna().unique().tolist()
            if dpto_seleccionado != "Todos"
            else sorted(df["CIUDAD"].dropna().unique().tolist())
        )
        ciudad_seleccionada = st.selectbox("Ciudad", ["Todos"] + sorted(ciudades_disponibles))
    # Checkbox para excluir a TPM EQUIPOS S.A.S
    excluir_tpm = st.checkbox("Excluir TPM EQUIPOS S.A.S", value=False)
    df["VENDEDOR"] = df["VENDEDOR"].str.strip()
    df["AÑO"] = pd.to_numeric(df["AÑO"], errors="coerce")
    df["TOTAL V"] = pd.to_numeric(df["TOTAL V"], errors="coerce")

    
    # Aplicar filtros
    df_filtrado = df.copy()

    if vendedor_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["VENDEDOR"].str.strip() == vendedor_seleccionado.strip()]


    if año_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["AÑO"] == int(año_seleccionado)]

    if dpto_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["DPTO"] == dpto_seleccionado]

    if ciudad_seleccionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado["CIUDAD"] == ciudad_seleccionada]
    if excluir_tpm:
        df_filtrado = df_filtrado[df_filtrado["RAZON SOCIAL"].str.upper().str.strip() != "TPM EQUIPOS S.A.S"]    
    
    if df_filtrado.empty:
        st.warning("No hay datos para los filtros seleccionados.")

        # Agrupación para la gráfica
    if vendedor_seleccionado == "Todos" or año_seleccionado == "Todos":
            df_agrupado = df_filtrado.groupby("AÑO")["TOTAL V"].sum().reset_index()
            eje_x = "AÑO"
            titulo_grafica = "Ventas Totales de la Empresa" if vendedor_seleccionado == "Todos" else f"Ventas de {vendedor_seleccionado} por Año"
    else:
            orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            df_filtrado["MES"] = pd.Categorical(df_filtrado["MES"], categories=orden_meses, ordered=True)
            df_agrupado = df_filtrado.groupby("MES")["TOTAL V"].sum().reset_index()
            eje_x = "MES"
            titulo_grafica = f"Ventas de {vendedor_seleccionado} en {año_seleccionado}"

      # Mostrar gráfico
    # Convertir ventas a millones
    df_agrupado["TOTAL V (M)"] = df_agrupado["TOTAL V"] / 1_000_000

    fig = px.bar(
        df_agrupado,
        x=eje_x,
        y="TOTAL V (M)",
        title=titulo_grafica,
        text_auto=True,
        color_discrete_sequence=["#00CED1"]
    )

    # Formato de texto encima de cada barra
    fig.update_traces(
        texttemplate="%{y:.0f}M",  # Texto como "250M"
        textposition="outside"
    )

    # Eje Y con sufijo fijo en millones
    fig.update_layout(
        yaxis_tickformat=",",              # Muestra números normales con coma
        yaxis_ticksuffix="M",              # Siempre mostrar "M"
        yaxis_tickprefix="$",              # Agrega símbolo de dólar
        xaxis_title=eje_x,
        yaxis_title="Ventas (Millones $)"
    )

    # Eje X como categoría si es por AÑO
    if eje_x == "AÑO":
        fig.update_xaxes(type="category")

    st.plotly_chart(fig, use_container_width=True)

        # Tablas Top 10
   

    # Determinar si agrupar por AÑO o MES
    agrupador = "MES" if año_seleccionado != "Todos" else "AÑO"
    orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    if agrupador == "MES":
        df_filtrado["MES"] = pd.Categorical(df_filtrado["MES"], categories=orden_meses, ordered=True)

    def formato_millones(x):
        return f"$ {x/1_000_000:,.0f}M"

    def mostrar_top_personalizado(df_top, titulo, index_col, top_n=10):
        df_top["TOTAL"] = df_top.sum(axis=1)
        df_top = df_top.sort_values("TOTAL", ascending=False).drop(columns="TOTAL").head(top_n)
        df_top = df_top.applymap(lambda x: formato_millones(x))
        st.markdown(f"<h3 style='text-align: center;'>{titulo}</h3>", unsafe_allow_html=True)
        st.dataframe(df_top.reset_index(), use_container_width=True, hide_index=True)

    # Top Ubicación
    st.subheader("🏆 Top 10 por Ubicación")
    if dpto_seleccionado == "Todos":
        top = df_filtrado.groupby(["DPTO", agrupador])["TOTAL V"].sum().reset_index()
        top = top.pivot(index="DPTO", columns=agrupador, values="TOTAL V").fillna(0)
        mostrar_top_personalizado(top, "🏙️ Top por Departamento", "DPTO")
    else:
        top = df_filtrado.groupby(["CIUDAD", agrupador])["TOTAL V"].sum().reset_index()
        top = top.pivot(index="CIUDAD", columns=agrupador, values="TOTAL V").fillna(0)
        mostrar_top_personalizado(top, "🏙️ Top por Ciudad", "CIUDAD")

    # Top Referencia
    top_ref = df_filtrado.groupby(["REFERENCIA", agrupador])["TOTAL V"].sum().reset_index()
    top_ref = top_ref.pivot(index="REFERENCIA", columns=agrupador, values="TOTAL V").fillna(0)
    mostrar_top_personalizado(top_ref, "📦 Top 20 Referencias", "REFERENCIA", top_n=20)

    # Top Razón Social
    top_razon = df_filtrado.groupby(["RAZON SOCIAL", agrupador])["TOTAL V"].sum().reset_index()
    top_razon = top_razon.pivot(index="RAZON SOCIAL", columns=agrupador, values="TOTAL V").fillna(0)
    mostrar_top_personalizado(top_razon, "🏢 Top 10 Razón Social", "RAZON SOCIAL", top_n=10)

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
    
            fig = px.bar(df_grafico, x=x_axis, y="TOTAL V", color_discrete_sequence=['#5F9EA0'])
    
            # Force categorical axis
            fig.update_xaxes(type='category')
            

    
            st.plotly_chart(fig, use_container_width=True)
if pagina == "TPM":
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", dtype={"AÑO": str, "MES": str})
        df.columns = df.columns.str.strip()
        df.rename(columns=lambda x: x.strip(), inplace=True)

        # Eliminar filas duplicadas
        df = df.drop_duplicates()

        # Diccionario para convertir meses en texto a número
        meses_dict = {
            "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
            "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
        }

        # Normalizar nombre de los meses
        if df["MES"].dtype == object:
            df["MES"] = df["MES"].str.upper().map(meses_dict)

        # Convertir años
        df["AÑO"] = df["AÑO"].astype(float).astype(int)

        df["TOTAL C"] = df["TOTAL C"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        df["TOTAL C"] = pd.to_numeric(df["TOTAL C"], errors="coerce")

        # Asegurarse de que el mes esté entre 1 y 12
        df["MES"] = pd.to_numeric(df["MES"], errors="coerce").fillna(0).astype(int)
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

  