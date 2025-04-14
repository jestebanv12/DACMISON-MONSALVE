import streamlit as st
import pandas as pd
import utilidades as util
import streamlit as st
from PIL import Image 
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO 
import io
import xlsxwriter 



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
        "🗺️ Geolocalización":"Geolocalización",
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
        def formatear_tabla_miles(df_tabla):
            df_fmt = df_tabla.reset_index().copy()
            if 'index' in df_fmt.columns:
                df_fmt.rename(columns={'index': 'GRUPO TRES'}, inplace=True)

            for col in df_fmt.columns[1:]:
                df_fmt[col] = df_fmt[col].apply(lambda x: f"${x/1_000:,.0f}K")

            return df_fmt
    
        def formatear_tabla_miles(df_tabla):
                df_fmt = df_tabla.reset_index().copy()
                if 'index' in df_fmt.columns:
                    df_fmt.rename(columns={'index': 'GRUPO TRES'}, inplace=True)

                for col in df_fmt.columns[1:]:
                    df_fmt[col] = df_fmt[col].apply(lambda x: f"${x/1_000:,.0f}K")

                return df_fmt


        styled_top3 = formatear_tabla_miles(top_grupo3)
        styled_top4 = formatear_tabla_miles(top_grupo4)


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
    df_agrupado["TOTAL V (K)"] = df_agrupado["TOTAL V"] / 1_000

    fig = px.bar(
        df_agrupado,
        x=eje_x,
        y="TOTAL V (K)",
        title=titulo_grafica,
        text_auto=True,
        color_discrete_sequence=["#00CED1"]
    )

    # Formato de texto encima de cada barra
    fig.update_traces(
        text=df_agrupado["TOTAL V (K)"].apply(lambda x: f"{x:,.0f}K"),
        textposition="outside",
        textfont=dict(size=12)
)

    # Eje Y con sufijo fijo en millones
    fig.update_layout(
        yaxis_tickformat=",",              # Muestra números normales con coma
        yaxis_ticksuffix="",              # Siempre mostrar "M"
        yaxis_tickprefix="$",              # Agrega símbolo de dólar
        xaxis_title=eje_x,
        yaxis_title="Ventas (Miles $)"
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

    # Formato en miles (K)
    def formato_miles(x):
        return f"$ {x / 1_000:,.0f}K"

    def mostrar_top_personalizado(df_top, titulo, index_col, top_n=10):
        df_top["TOTAL"] = df_top.sum(axis=1)
        df_top = df_top.sort_values("TOTAL", ascending=False).drop(columns="TOTAL").head(top_n)
        df_top = df_top.applymap(lambda x: formato_miles(x))
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

        col1, col2 = st.columns([2, 1])
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
            orden_meses = [
                "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
            ]
            df_filtrado["MES"] = df_filtrado["MES"].str.strip().str.upper()
            df_filtrado["MES"] = pd.Categorical(df_filtrado["MES"], categories=orden_meses, ordered=True)

            df_grafico = df_filtrado.groupby("MES").agg({"TOTAL V": "sum"}).reset_index()
            x_axis = "MES"

        # Convertir TOTAL V a miles
        df_grafico["TOTAL K"] = df_grafico["TOTAL V"] / 1_000

        if df_grafico["TOTAL K"].sum() == 0:
            st.warning("No hay ventas registradas para esta selección.")
        else:
            fig_bar = px.bar(
                df_grafico,
                x=x_axis,
                y="TOTAL K",
                title="Ventas por Periodo",
                color_discrete_sequence=["green"]
            )

            # Eje Y en miles con símbolo $
            fig_bar.update_layout(
                yaxis_tickprefix="$",
                yaxis_ticksuffix="",
                yaxis_tickformat=",",
                xaxis_title=x_axis,
                yaxis_title="Ventas (Miles $)"
            )

            if x_axis == "AÑO":
                fig_bar.update_xaxes(type="category")

            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("🏆 Top 20 REFERENCIAS")

        # Determinar si agrupar por AÑO o MES
        agrupador = "MES" if año_seleccionado != "Todos" else "AÑO"

        # Asegurar orden de los meses si aplica
        orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        if agrupador == "MES":
            df_filtrado["MES"] = pd.Categorical(df_filtrado["MES"], categories=orden_meses, ordered=True)

        # Agrupar por REFERENCIA y el agrupador dinámico
        top_ref = df_filtrado.groupby(["REFERENCIA", agrupador])["TOTAL V"].sum().reset_index()

        # Pivotear para mostrar los años/meses como columnas
        pivot_ref = top_ref.pivot(index="REFERENCIA", columns=agrupador, values="TOTAL V").fillna(0)

        # Calcular total general por REFERENCIA y ordenar
        pivot_ref["TOTAL"] = pivot_ref.sum(axis=1)
        pivot_ref = pivot_ref.sort_values("TOTAL", ascending=False).drop(columns="TOTAL").head(20)

        # 👉 Formatear a miles (texto)
        # 👉 Formatear a miles (texto)
        def formato_miles(x):
            return f"$ {x / 1_000:,.0f}"

        pivot_ref_formateado = pivot_ref.applymap(formato_miles)

        # 👉 Función para resaltar en rojo los valores "$ 0"
        def resaltar_ceros(val):
            return 'color: red' if val == "$ 0" else ''

        # 👉 Aplicar estilo
        pivot_ref_estilado = pivot_ref_formateado.reset_index().style.applymap(resaltar_ceros)

        # 👉 Mostrar tabla estilizada sin índice
        st.dataframe(pivot_ref_estilado, use_container_width=True, hide_index=True)

        # Crear archivo Excel en memoria
        # Crear archivos Excel en memoria
        excel_buffer = io.BytesIO()
        excel_buffer_completo = io.BytesIO()

        # Guardar el Top 20 Referencias como tabla formateada
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_excel = pivot_ref.reset_index()
            df_excel.to_excel(writer, sheet_name="Top Referencias", index=False)
            
            # Dar formato de tabla
            workbook = writer.book
            worksheet = writer.sheets["Top Referencias"]
            
            # Crear un formato para encabezados
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Aplicar formato de encabezado
            for col_num, value in enumerate(df_excel.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-ajustar ancho de columnas
            for i, col in enumerate(df_excel.columns):
                column_width = max(df_excel[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)

        # Guardar el dataframe completo como tabla formateada
        with pd.ExcelWriter(excel_buffer_completo, engine='xlsxwriter') as writer:
            df_filtrado.to_excel(writer, sheet_name="Datos Completos", index=False)
            
            # Dar formato de tabla
            workbook = writer.book
            worksheet = writer.sheets["Datos Completos"]
            
            # Crear un formato para encabezados
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Aplicar formato de encabezado
            for col_num, value in enumerate(df_filtrado.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-ajustar ancho de columnas
            for i, col in enumerate(df_filtrado.columns):
                column_width = max(df_filtrado[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)

        # Mostrar ambos botones uno al lado del otro
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Descargar Top 20 Referencias",
                data=excel_buffer.getvalue(),
                file_name="top_20_referencias.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            st.download_button(
                label="📥 Descargar Datos Completos",
                data=excel_buffer_completo.getvalue(),
                file_name="dataframe_completos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_full_df"
            )


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

    columnas_requeridas = {"AÑO", "MES", "DIA", "TOTAL V", "RAZON SOCIAL", "REFERENCIA"}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"El archivo CSV debe contener las columnas exactas: {columnas_requeridas}")
    else:
        referencias = df["REFERENCIA"].dropna().unique()
        referencia_seleccionada = st.selectbox("🔍 Seleccione una Referencia (obligatorio):", [""] + sorted(referencias))

    if referencia_seleccionada:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            departamentos = df["DPTO"].dropna().unique()
            dpto_seleccionado = st.selectbox("📍 Departamento", ["Todos"] + sorted(departamentos))

        with col2:
            if dpto_seleccionado != "Todos":
                ciudades = df[df["DPTO"] == dpto_seleccionado]["CIUDAD"].dropna().unique()
            else:
                ciudades = df["CIUDAD"].dropna().unique()
            ciudad_seleccionada = st.selectbox("🏙️ Ciudad", ["Todos"] + sorted(ciudades))

        with col3:
            vendedores = df["VENDEDOR"].dropna().unique()
            vendedor_seleccionado = st.selectbox("🧑‍💼 Vendedor", ["Todos"] + sorted(vendedores))

        with col4:
            años = df["AÑO"].dropna().astype(int).unique()
            año_seleccionado = st.selectbox("📅 Año", ["Todos"] + sorted(años))

        razon_social_seleccionada = st.selectbox(
            "🏢 Buscar Razón Social",
            options=["Todos"] + sorted(df["RAZON SOCIAL"].dropna().unique()),
            index=0,
            placeholder="Escribe para buscar..."
        )

        df_filtrado = df[df["REFERENCIA"] == referencia_seleccionada].copy()

        if dpto_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["DPTO"] == dpto_seleccionado]

        if ciudad_seleccionada != "Todos":
            df_filtrado = df_filtrado[df_filtrado["CIUDAD"] == ciudad_seleccionada]

        if vendedor_seleccionado != "Todos":
            if ciudad_seleccionada != "Todos" and vendedor_seleccionado not in df_filtrado["VENDEDOR"].unique():
                st.warning("❌ El vendedor seleccionado no tiene registros en la ciudad seleccionada.")
            else:
                df_filtrado = df_filtrado[df_filtrado["VENDEDOR"] == vendedor_seleccionado]

        if razon_social_seleccionada != "Todos":
            df_filtrado = df_filtrado[df_filtrado["RAZON SOCIAL"] == razon_social_seleccionada]

        if año_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["AÑO"].astype(int) == int(año_seleccionado)]

        if df_filtrado.empty:
            st.warning("⚠️ No hay datos disponibles para los filtros seleccionados.")
        else:
            df_filtrado["VENTAS_K"] = df_filtrado["TOTAL V"] / 1_000
            eje_x = "AÑO" if año_seleccionado == "Todos" else "MES"

            df_grafico = df_filtrado.groupby(eje_x).agg({"VENTAS_K": "sum"}).reset_index()
            df_grafico[eje_x] = df_grafico[eje_x].astype(str)

            fig = px.bar(
                df_grafico,
                x=eje_x,
                y="VENTAS_K",
                text_auto=True,
                labels={"VENTAS_K": "Ventas (K)", eje_x: eje_x},
                color_discrete_sequence=["#2ecc71"],
                title=f"📈 Ventas de '{referencia_seleccionada}' por {eje_x}"
            )

            fig.update_traces(texttemplate="%{y:,.0f}K", textposition="outside")
            fig.update_layout(yaxis_title="Ventas (Miles $)", xaxis_title=eje_x)
            if eje_x == "AÑO":
                fig.update_xaxes(type="category")

            st.plotly_chart(fig, use_container_width=True)

            st.subheader(f"🏆 Top por {eje_x} - Ventas y Cantidad")
            df_top = df_filtrado.groupby(eje_x).agg({"TOTAL V": "sum", "CANT": "sum"}).reset_index()
            df_top["TOTAL V"] = df_top["TOTAL V"].apply(lambda x: f"${x/1_000:,.0f}K")
            df_top["CANT"] = df_top["CANT"].astype(int)
            st.dataframe(df_top, hide_index=True, use_container_width=True)

            def generar_excel(df_exportar):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df_exportar.to_excel(writer, index=False, sheet_name="Datos")
                    workbook = writer.book
                    worksheet = writer.sheets["Datos"]
                    (max_row, max_col) = df_exportar.shape
                    column_settings = [{"header": col} for col in df_exportar.columns]
                    worksheet.add_table(0, 0, max_row, max_col - 1, {
                        "columns": column_settings,
                        "style": "Table Style Medium 9",
                        "name": "TablaDatos"
                    })
                output.seek(0)
                return output

            st.download_button(
                label="📥 Descargar Top por Año/Mes",
                data=generar_excel(df_top),
                file_name=f"Top_{eje_x}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.divider()

            st.subheader("📌 Top 20 por Vendedor, Departamento, Ciudad y Cliente")

            def mostrar_top_con_descarga(columna, titulo, nombre_archivo):
                top_df = df_filtrado.groupby(columna).agg({"TOTAL V": "sum", "CANT": "sum"}).reset_index()
                top_df = top_df.sort_values("TOTAL V", ascending=False).head(20)
                top_df["TOTAL V"] = top_df["TOTAL V"].apply(lambda x: f"${x/1_000:,.0f}K")

                st.markdown(f"**🔹 {titulo}**")
                st.dataframe(top_df, hide_index=True, use_container_width=True)

                coln, colm = st.columns(2)
                with coln:
                    st.download_button(
                        label=f"📥 Descargar Top",
                        data=generar_excel(top_df),
                        file_name=f"{nombre_archivo}_Top20.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                with colm:
                    st.download_button(
                        label=f"📦 Descargar Todo",
                        data=generar_excel(df_filtrado),
                        file_name=f"{nombre_archivo}_Todo.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            mostrar_top_con_descarga("VENDEDOR", "Top Vendedores", "Top_Vendedores")
            mostrar_top_con_descarga("DPTO", "Top Departamentos", "Top_Departamentos")
            mostrar_top_con_descarga("CIUDAD", "Top Ciudades", "Top_Ciudades")
            mostrar_top_con_descarga("RAZON SOCIAL", "Top Clientes", "Top_Clientes")

    else:
        st.warning("⚠️ Por favor seleccione una Referencia para ver información.")



if pagina == "Geolocalización":
    # Cargar los datos
    import pydeck as pdk
    import numpy as np  # Añadida la importación de NumPy
    from streamlit_folium import folium_static
    import folium
    from folium.plugins import HeatMap
    
    # Cargar datos
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", dtype={"AÑO": str, "MES": str})
        df.columns = df.columns.str.upper().str.strip()
        return df

    @st.cache_data
    def cargar_geo():
        df_geo = pd.read_csv("geolocalizacion.csv", sep=";")
        df_geo.columns = df_geo.columns.str.upper().str.strip()
        df_geo["LATITUD"] = pd.to_numeric(df_geo["LATITUD"].astype(str).str.replace(',', '.'), errors="coerce")
        df_geo["LONGITUD"] = pd.to_numeric(df_geo["LONGITUD"].astype(str).str.replace(',', '.'), errors="coerce")
        return df_geo.dropna(subset=["LATITUD", "LONGITUD"])

    df = cargar_datos()
    df_geo = cargar_geo()
    df = df.merge(df_geo, how="left", on="CIUDAD")

    # ----------------- FILTROS EN PANTALLA PRINCIPAL -----------------
    st.subheader("📍 Segmentación del Mapa de Ventas")

    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)

    año_sel = col1.selectbox("Año", ["Todos"] + sorted(df["AÑO"].dropna().unique()))
    vendedor_sel = col2.selectbox("Vendedor", ["Todos"] + sorted(df["VENDEDOR"].dropna().unique()))
    referencia_sel = col3.selectbox("Referencia", ["Todos"] + sorted(df["REFERENCIA"].dropna().unique()))
    gr3_sel = col4.selectbox("Grupo Tres", ["Todos"] + sorted(df["GRUPO TRES"].dropna().unique()))
    gr4_sel = col5.selectbox("Grupo Cuatro", ["Todos"] + sorted(df["GRUPO CUATRO"].dropna().unique()))

    # ----------------- APLICAR FILTROS -----------------
    df_filtrado = df.copy()
    if año_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["AÑO"] == año_sel]
    if vendedor_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["VENDEDOR"] == vendedor_sel]
    if referencia_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["REFERENCIA"] == referencia_sel]
    if gr3_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["GRUPO TRES"] == gr3_sel]
    if gr4_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["GRUPO CUATRO"] == gr4_sel]

    # ----------------- MAPA -----------------
    if "LATITUD" in df_filtrado.columns and "LONGITUD" in df_filtrado.columns and not df_filtrado[["LATITUD", "LONGITUD"]].dropna().empty:
        df_mapa = df_filtrado.dropna(subset=["LATITUD", "LONGITUD"])
        df_mapa = df_mapa.groupby(["CIUDAD", "LATITUD", "LONGITUD"]).agg({
            "TOTAL V": "sum",
            "CANT": "sum"
        }).reset_index()

        df_mapa["TOTAL V"] = pd.to_numeric(df_mapa["TOTAL V"], errors="coerce")
        df_mapa["CANT"] = pd.to_numeric(df_mapa["CANT"], errors="coerce")

        if not df_mapa.empty:
            st.subheader("🗺️ Mapa de Ventas por Ciudad")
            total_ventas = df_mapa["TOTAL V"].sum()
            df_mapa["PORCENTAJE"] = (df_mapa["TOTAL V"] / total_ventas * 100).round(2)

            m = folium.Map(
                location=[df_mapa["LATITUD"].mean(), df_mapa["LONGITUD"].mean()],
                zoom_start=6,
                tiles='CartoDB positron'
            )

            for _, row in df_mapa.iterrows():
                radio = min(35, max(8, np.sqrt(row["PORCENTAJE"]) * 5))
                color = '#e74c3c' if row["PORCENTAJE"] > 10 else '#f39c12' if row["PORCENTAJE"] > 5 else '#3498db'

                popup_html = f"""
                <div style="font-family: Arial; width: 200px;">
                    <h4>{row['CIUDAD']}</h4>
                    <p><b>Ventas:</b> ${row['TOTAL V']:,.2f}</p>
                    <p><b>% del Total:</b> {row['PORCENTAJE']}%</p>
                    <p><b>Cantidad:</b> {row['CANT']}</p>
                </div>
                """

                folium.CircleMarker(
                    location=[row["LATITUD"], row["LONGITUD"]],
                    radius=radio,
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{row['CIUDAD']}: {row['PORCENTAJE']}%",
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    weight=2
                ).add_to(m)

            folium_static(m)

            st.markdown("""
            ### 🎯 Interpretación del Mapa:
            - 🔴 Rojo: Más del **10%** de ventas
            - 🟠 Naranja: Entre **5% y 10%**
            - 🔵 Azul: Menos del **5%**
            """)
        else:
            st.warning("⚠️ No hay datos válidos para mostrar en el mapa después de aplicar los filtros.")
    else:
        st.warning("⚠️ No se encontraron columnas de LATITUD y LONGITUD válidas.")


if pagina == "TPM":
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", dtype={"AÑO": str, "MES": str})
        df.columns = df.columns.str.strip()
        df.rename(columns=lambda x: x.strip(), inplace=True)

        df = df.drop_duplicates()

        # Diccionario para convertir meses
        meses_dict = {
            "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
            "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
        }

        if df["MES"].dtype == object:
            df["MES"] = df["MES"].str.upper().map(meses_dict)

        df["AÑO"] = df["AÑO"].astype(float).astype(int)

        df["TOTAL C"] = df["TOTAL C"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        df["TOTAL C"] = pd.to_numeric(df["TOTAL C"], errors="coerce")

        df["MES"] = pd.to_numeric(df["MES"], errors="coerce").fillna(0).astype(int)
        df = df[df["MES"].between(1, 12)]

        return df

    df = cargar_datos()

    # Verificar columnas requeridas
    columnas_requeridas = {"AÑO", "MES", "TOTAL V", "TOTAL C"}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"El archivo CSV debe contener las columnas exactas: {columnas_requeridas}")
    else:
        st.subheader("📊 Ventas y Costos Totales", divider="blue")

        # Segmentadores
        col1, col2, col3, col4 = st.columns(4)
        año_sel = col1.selectbox("Año", ["Todos"] + sorted(df["AÑO"].unique()))
        ref_sel = col2.selectbox("Referencia", ["Todos"] + sorted(df["REFERENCIA"].dropna().unique()))
        dep_sel = col3.selectbox("Departamento", ["Todos"] + sorted(df["DPTO"].dropna().unique()))
        ciudad_sel = col4.selectbox("Ciudad", ["Todos"] + sorted(df["CIUDAD"].dropna().unique()))

        col5, col6, col7 = st.columns(3)
        g2_sel = col5.selectbox("Grupo 2", ["Todos"] + sorted(df["GRUPO DOS"].dropna().unique()))
        g3_sel = col6.selectbox("Grupo 3", ["Todos"] + sorted(df["GRUPO TRES"].dropna().unique()))
        g4_sel = col7.selectbox("Grupo 4", ["Todos"] + sorted(df["GRUPO CUATRO"].dropna().unique()))

        # Aplicar filtros
        df_filtrado = df.copy()
        if año_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["AÑO"] == int(año_sel)]
        if ref_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["REFERENCIA"] == ref_sel]
        if dep_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["DPTO"] == dep_sel]
        if ciudad_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["CIUDAD"] == ciudad_sel]
        if g2_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["GRUPO DOS"] == g2_sel]
        if g3_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["GRUPO TRES"] == g3_sel]
        if g4_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["GRUPO CUATRO"] == g4_sel]

        if df_filtrado.empty:
            st.warning("⚠️ No hay datos disponibles para esta combinación de filtros.")
        else:
            # Mapear meses
            meses_map = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            df_filtrado["MES"] = df_filtrado["MES"].map(meses_map)

            # Agrupación
            x_axis = "AÑO" if año_sel == "Todos" else "MES"
            df_grafico = df_filtrado.groupby(x_axis).agg({"TOTAL V": "sum", "TOTAL C": "sum"}).reset_index()

            # Ordenar meses
            if x_axis == "MES":
                df_grafico["MES"] = pd.Categorical(df_grafico["MES"], categories=meses_map.values(), ordered=True)
                df_grafico = df_grafico.sort_values("MES")

            # Gráfico de áreas
            # Escalar valores a miles
            df_grafico["TOTAL V"] = df_grafico["TOTAL V"] / 1000
            df_grafico["TOTAL C"] = df_grafico["TOTAL C"] / 1000

            # Gráfico de áreas
            fig_area = px.area(df_grafico, x=x_axis, y=["TOTAL C", "TOTAL V"],
                            title="Ventas y Costos Totales", labels={"value": "Monto ($ Miles)"},
                            color_discrete_sequence=["#5F9EA0","#006400"])

            fig_area.update_xaxes(tickmode="array", tickvals=df_grafico[x_axis].unique(), tickformat=".0f")
            fig_area.update_layout(
                yaxis=dict(
                    tickformat=",.0f",
                    title="Monto ($ Miles)"
                )
            )

            st.plotly_chart(fig_area, use_container_width=True)

    