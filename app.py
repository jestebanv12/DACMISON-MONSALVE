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
        "🔢 Comparativos":"Comparativos",
        "👩‍🏭 Vendedores": "Vendedores",
        "ℹ️ Cliente": "clientes",
        "⚙️ Referencias":"Referencias",
        "🔢 Comparativo Ref.":"Comparativo Ref",
        "🔢 Comparativo por Grupo.":"Comparativo por Grupo",
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
    st.subheader("Ventas desde el 2021.")
    # Cargar datos desde CSV con limpieza de nombres
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", index_col=None)
        df.columns = df.columns.str.strip()
        df.rename(columns=lambda x: x.strip(), inplace=True)
        return df

    def formato_miles(x):
        return f"${x/1_000:,.0f}K"

    def generar_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Top", index=True)  # Mantener el índice en el Excel
        return output.getvalue()

    df = cargar_datos()
    df['TOTAL V'] = df['TOTAL V'].astype('int64')

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
            df_filtrado_ano = df  # Usar el DataFrame completo cuando se selecciona "Todos"

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
            df_filtrado_ano = df[df["AÑO"] == int(año_seleccionado)]  # Usar el DataFrame filtrado por año

        # Calcular top_grupo3 y top_grupo4 después de definir df_filtrado_ano
        grupo3_col = "GRUPO TRES"
        if año_seleccionado == "Todos":
            top_grupo3 = df.groupby([grupo3_col, "AÑO"]).agg({"TOTAL V": "sum"}).reset_index()
            top_grupo3 = top_grupo3.pivot(index=grupo3_col, columns="AÑO", values="TOTAL V").fillna(0)
        else:
            top_grupo3 = df_filtrado_ano.groupby([grupo3_col, "MES"]).agg({"TOTAL V": "sum"}).reset_index()
            top_grupo3 = top_grupo3.pivot(index=grupo3_col, columns="MES", values="TOTAL V").fillna(0)
        top_grupo3 = top_grupo3.assign(TOTAL=top_grupo3.sum(axis=1)).nlargest(10, "TOTAL").drop(columns="TOTAL")

        grupo4_col = "GRUPO CUATRO"
        if año_seleccionado == "Todos":
            top_grupo4 = df.groupby([grupo4_col, "AÑO"]).agg({"TOTAL V": "sum"}).reset_index()
            top_grupo4 = top_grupo4.pivot(index=grupo4_col, columns="AÑO", values="TOTAL V").fillna(0)
        else:
            top_grupo4 = df_filtrado_ano.groupby([grupo4_col, "MES"]).agg({"TOTAL V": "sum"}).reset_index()
            top_grupo4 = top_grupo4.pivot(index=grupo4_col, columns="MES", values="TOTAL V").fillna(0)
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
        fig.update_traces(textposition="inside", textfont=dict(color="white", size=12))
        fig.update_xaxes(type="category", title_text=eje_x, tickfont=dict(size=12))

        max_y = df_filtrado["TOTAL V"].max()
        tick_step = 500_000_000 if max_y > 1_000_000_000 else 100_000_000
        tick_vals = list(range(0, int(max_y + tick_step), int(tick_step)))
        tick_texts = [f"{int(val/1_000_000)}M" for val in tick_vals]

        fig.update_yaxes(title_text="Total Ventas ($)", tickvals=tick_vals, ticktext=tick_texts)
        fig.update_layout(uniformtext_minsize=8, uniformtext_mode="hide", plot_bgcolor="#f9f9f9", title_font_size=18)
        st.plotly_chart(fig, use_container_width=True)

        # -------- FORMATO VISUAL PARA STREAMLIT --------
        def formatear_con_k_y_color(df_tabla, nombre_indice):
            df_copy = df_tabla.copy()
            df_copy.index.name = None  # Quitar el nombre del índice para que no aparezca como fila

            # Construir la tabla HTML manualmente para controlar el encabezado
            html = "<table border=\"1\" class=\"dataframe\">"
            html += "  <thead>"
            html += "    <tr style=\"text-align: center;\">"
            html += f"      <th>{nombre_indice}</th>"  # Encabezado para la primera columna (índice)
            for col in df_copy.columns:
                html += f"      <th>{col}</th>"
            html += "    </tr>"
            html += "  </thead>"
            html += "  <tbody>"
            for index, row in df_copy.iterrows():
                html += "    <tr>"
                html += f"      <th>{index}</th>"  # Valor del índice
                for col in df_copy.columns:
                    value = row[col]
                    # Modificado para eliminar !important y usar solo color rojo
                    formatted_value = f'<span style="color: red; font-weight: bold;">{formato_miles(value)}</span>' if value == 0 else formato_miles(value)
                    html += f"      <td>{formatted_value}</td>"
                html += "    </tr>"
            html += "  </tbody>"
            html += "</table>"
            return html

        # -------- DESCARGA EN EXCEL --------
        def generar_excel_sin_formato(df_original):
            return generar_excel(df_original)  # No resetear el índice para la descarga "Todo"

        # Mostrar y descargar top GRUPO TRES
        st.subheader(f"🏆 Top 10 'GRUPO TRES' por Ventas en {año_seleccionado}")
        html_tabla3 = formatear_con_k_y_color(top_grupo3, grupo3_col)
        st.markdown(html_tabla3, unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.download_button("⬇️ Descargar Top", data=generar_excel(top_grupo3), file_name="Top Grupo 3.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            st.download_button("⬇️ Descargar Todo", data=generar_excel_sin_formato(top_grupo3), file_name="Todo Grupo 3.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Mostrar y descargar top GRUPO CUATRO
        st.subheader(f"🥇 Top 20 'GRUPO CUATRO' por Ventas en {año_seleccionado}")
        html_tabla4 = formatear_con_k_y_color(top_grupo4, grupo4_col)
        st.markdown(html_tabla4, unsafe_allow_html=True)
        col3, col4 = st.columns([1, 1])
        with col3:
            st.download_button("⬇️ Descargar Top", data=generar_excel(top_grupo4), file_name="Top Grupo 4.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col4:
            st.download_button("⬇️ Descargar Todo", data=generar_excel_sin_formato(top_grupo4), file_name="Todo Grupo 4.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif pagina=="Comparativos":
    st.title("🔢 Comparativos por mes")
    # Cargar datos
    @st.cache_data
    def cargar_datos():
        try:
            df = pd.read_csv("Informe ventas.csv", sep=";")
        except:
            df = pd.read_csv("Informe ventas.csv", sep=",")
        df.columns = df.columns.str.strip()
        df["AÑO"] = df["AÑO"].astype(int)
        df["MES"] = df["MES"].str.upper()
        orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        df["MES"] = pd.Categorical(df["MES"], categories=orden_meses, ordered=True)
        return df

    def tabla_html_centrada(df, formato_columnas=None, nombre_indice=""):
        df_copy = df.copy()
        df_copy.index.name = None
        if nombre_indice:
            df_copy.index.name = nombre_indice

        html = '<table style="width: 100%; border-collapse: collapse; text-align: center;">'
        html += '<thead><tr style="background-color: #f0f0f0;">'
        if df_copy.index.name:
            html += f'<th>{df_copy.index.name}</th>'
        else:
            html += '<th></th>'
        for col in df_copy.columns:
            html += f'<th>{col}</th>'
        html += '</tr></thead><tbody>'

        for idx, row in df_copy.iterrows():
            html += '<tr>'
            html += f'<td><b>{idx}</b></td>'
            for col in df_copy.columns:
                val = row[col]
                if formato_columnas and col in formato_columnas:
                    val = formato_columnas[col](val)
                html += f'<td>{val}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        return html

    df = cargar_datos()
    años_disponibles = sorted(df["AÑO"].unique())

    col1, col2 = st.columns(2)
    with col1:
        año1 = st.selectbox("Selecciona AÑO 1:", ["Todos"] + años_disponibles)
    with col2:
        año2 = st.selectbox("Selecciona AÑO 2:", ["Todos"] + años_disponibles)

    if (año1 != "Todos" and año2 == "Todos") or (año2 != "Todos" and año1 == "Todos"):
        st.warning("⚠️ Si seleccionas un año específico, debes seleccionar otro para comparar.")
    else:
        if año1 == "Todos" and año2 == "Todos":
            df_group = df.groupby(["MES", "AÑO"])["TOTAL V"].sum().reset_index()
            df_group["TOTAL V"] = df_group["TOTAL V"] / 1_000
            df_group = df_group.sort_values(by=["MES", "AÑO"])

            st.subheader("📊 Comparación de ventas por MES para todos los años")

            fig = go.Figure()
            años = sorted(df_group["AÑO"].unique())
            colores = px.colors.qualitative.Set2[:len(años)]
            for i, año in enumerate(años):
                df_año = df_group[df_group["AÑO"] == año]
                fig.add_trace(go.Bar(
                    x=df_año["MES"],
                    y=df_año["TOTAL V"],
                    name=str(año),
                    marker_color=colores[i % len(colores)]
                ))
            fig.update_layout(
                barmode='group',
                yaxis_title="Ventas ($K)",
                xaxis_title="Mes",
                plot_bgcolor="#fafafa",
                bargap=0.3,
                bargroupgap=0.1,
                xaxis={'categoryorder': 'array', 'categoryarray': df["MES"].cat.categories}
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Tabla de ventas por MES y AÑO")
            tabla_pivot = df_group.pivot(index="MES", columns="AÑO", values="TOTAL V").fillna(0)
            html_tabla = tabla_html_centrada(tabla_pivot, formato_columnas={col: lambda x: f"${x:,.0f}K" for col in tabla_pivot.columns})
            st.markdown(html_tabla, unsafe_allow_html=True)

            buffer = BytesIO()
            tabla_pivot.to_excel(buffer, index=True)
            st.download_button(
                label="📥 Descargar Excel",
                data=buffer.getvalue(),
                file_name="ventas_todos_los_años.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            df_comp = df[df["AÑO"].isin([año1, año2])]
            tabla = df_comp.groupby(["AÑO", "MES"])["TOTAL V"].sum().reset_index()
            tabla["TOTAL V"] = tabla["TOTAL V"] / 1_000
            tabla["MES"] = pd.Categorical(tabla["MES"], categories=df["MES"].cat.categories, ordered=True)
            tabla = tabla.sort_values(by=["MES", "AÑO"])

            tabla_pivot = tabla.pivot(index="MES", columns="AÑO", values="TOTAL V").fillna(0)
            tabla_pivot["% CRECIMIENTO"] = (
                (tabla_pivot[año2] - tabla_pivot[año1]) / tabla_pivot[año1].replace(0, 1)
            ) * 100
            tabla_pivot["% CRECIMIENTO"] = tabla_pivot["% CRECIMIENTO"].round(2)

            st.subheader(f"📊 Comparación de ventas mensuales entre {año1} y {año2}")

            fig = go.Figure()
            df_año1 = tabla[tabla["AÑO"] == año1]
            fig.add_trace(go.Bar(
                x=df_año1["MES"],
                y=df_año1["TOTAL V"],
                name=str(año1),
                marker_color="#2ecc71"
            ))
            df_año2 = tabla[tabla["AÑO"] == año2]
            fig.add_trace(go.Bar(
                x=df_año2["MES"],
                y=df_año2["TOTAL V"],
                name=str(año2),
                marker_color="#e74c3c"
            ))
            fig.update_layout(
                barmode='group',
                yaxis_title="Ventas ($K)",
                xaxis_title="Mes",
                plot_bgcolor="#fafafa",
                bargap=0.3,
                bargroupgap=0.1,
                xaxis={'categoryorder': 'array', 'categoryarray': df["MES"].cat.categories}
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Tabla comparativa de ventas y % crecimiento")

            def formato(x, col):
                if col == "% CRECIMIENTO":
                    color = "red !important;font-weight: bold" if x < 0 else "green!important;font-weight: bold"
                    return f'<span style="color:{color}">{x:+.2f}%</span>'
                else:
                    return f"${x:,.0f}K"

            html_tabla = tabla_html_centrada(
                tabla_pivot,
                formato_columnas={col: lambda x, col=col: formato(x, col) for col in tabla_pivot.columns}
            )
            st.markdown(html_tabla, unsafe_allow_html=True)
            st.markdown("""
                <style>
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        table-layout: fixed;
                    }
                    th, td {
                        text-align: center;
                        padding: 6px 8px;
                        max-width: 100px;
                        word-wrap: break-word;
                        font-size: 13px;
                    }
                    th {
                        background-color: #f0f0f0;
                    }
                    .title {
                        font-size: 1.4em;
                        font-weight: bold;
                        text-align: center;
                        margin-top: 1em;
                    }
                    .zero_value {
                        color: red !important;
                        font-weight: bold;
                    }
                </style>
            """, unsafe_allow_html=True)

            buffer2 = BytesIO()
            tabla_pivot.to_excel(buffer2, index=True)
            st.download_button(
                label="📥 Descargar Excel",
                data=buffer2.getvalue(),
                file_name=f"comparativa_{año1}_vs_{año2}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

                

elif pagina == "Vendedores":
    st.title("👩‍🏭 Ventas por vendedor")
    # Agrega estilos CSS para centrar encabezados de tabla
    # Estilos
    st.markdown("""
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
            }
            th, td {
                text-align: center;
                padding: 6px 8px;
                max-width: 100px;
                word-wrap: break-word;
                font-size: 13px;
            }
            th {
                background-color: #f0f0f0;
            }
            .title {
                font-size: 1.4em;
                font-weight: bold;
                text-align: center;
                margin-top: 1em;
            }
            .zero_value {
                color: red !important;
                font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)
    # Carga de datos
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python")
        df.columns = df.columns.str.strip()
        df["TOTAL V"] = pd.to_numeric(df["TOTAL V"], errors="coerce")
        df["AÑO"] = pd.to_numeric(df["AÑO"], errors="coerce")
        return df

    df = cargar_datos()
    df["MES"] = df["MES"].astype(str).str.strip().str.upper()
    columnas_requeridas = {"AÑO", "MES", "DIA", "TOTAL V", "GRUPO TRES"}
    if not columnas_requeridas.issubset(df.columns):
        st.error(f"Faltan columnas requeridas: {columnas_requeridas - set(df.columns)}")
        st.stop()

    # Segmentadores
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

    excluir_tpm = st.checkbox("Excluir TPM EQUIPOS S.A.S", value=False)

    # Filtros
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
        st.stop()

    # Gráfico
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

    df_agrupado["TOTAL V (K)"] = df_agrupado["TOTAL V"] / 1_000
    fig = px.bar(
        df_agrupado,
        x=eje_x,
        y="TOTAL V (K)",
        title=titulo_grafica,
        text_auto=True,
        color_discrete_sequence=["#00CED1"]
    )
    fig.update_traces(
        text=df_agrupado["TOTAL V (K)"].apply(lambda x: f"{x:,.0f}K"),
        textposition="outside",
        textfont=dict(size=12)
    )
    fig.update_layout(
        yaxis_tickformat=",",
        yaxis_tickprefix="$",
        xaxis_title=eje_x,
        yaxis_title="Ventas (Miles $)"
    )
    if eje_x == "AÑO":
        fig.update_xaxes(type="category")

    st.plotly_chart(fig, use_container_width=True)

    # Funciones auxiliares
    def formato_miles(x):
        if isinstance(x, (int, float)):
            if x == 0:
                return '<span class="zero_value">$ 0K</span>'
            else:
                return f"$ {x / 1_000:,.0f}K"
        return x

    def generar_excel(df, index_col=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("TablaTop")
        
        # Formatos
        formato_bold = workbook.add_format({'bold': True, 'align': 'center'})
        formato_normal = workbook.add_format({'align': 'right'})
        formato_rojo = workbook.add_format({'font_color': 'red', 'underline': True, 'align': 'right'})
        
        # Usar el nombre de la columna correcto para el primer encabezado
        headers = list(df.columns)
        if index_col and df.index.name:
            headers[0] = df.index.name
        
        # Escribir encabezados
        for col_num, col_name in enumerate(headers):
            worksheet.write(0, col_num, col_name, formato_bold)
        
        # Escribir datos
        for row_num, row in enumerate(df.itertuples(index=False), start=1):
            for col_num, value in enumerate(row):
                if isinstance(value, str) and "$ 0K" in value:
                    worksheet.write(row_num, col_num, "$ 0K", formato_rojo)
                else:
                    # Eliminar etiquetas HTML si están presentes
                    if isinstance(value, str) and '<span class="zero_value">' in value:
                        value = "$ 0K"
                        worksheet.write(row_num, col_num, value, formato_rojo)
                    else:
                        worksheet.write(row_num, col_num, value, formato_normal)
        
        # Ajustes adicionales
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
        worksheet.freeze_panes(1, 1)
        for col_num in range(len(df.columns)):
            worksheet.set_column(col_num, col_num, 15)  # Ancho de columna
        
        workbook.close()
        output.seek(0)
        return output

    def mostrar_top(df, index_col, titulo, top_n=10):
        agrupador = "MES" if año_seleccionado != "Todos" else "AÑO"

        if agrupador == "MES":
            orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            df["MES"] = pd.Categorical(df["MES"], categories=orden_meses, ordered=True)

        # Agrupar y pivotear
        pivot = df.groupby([index_col, agrupador])["TOTAL V"].sum().reset_index()
        pivot = pivot.pivot(index=index_col, columns=agrupador, values="TOTAL V").fillna(0)

        # Ordenar y limitar
        pivot["TOTAL"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("TOTAL", ascending=False)
        pivot_top = pivot.head(top_n).drop(columns="TOTAL")

        # Formateo
        pivot_top_formateado = pivot_top.applymap(formato_miles)
        
        # Renombrar el índice con el nombre de la categoría
        pivot_top_formateado.index.name = index_col
        
        # Crear tabla HTML manualmente para controlar completamente el formato
        html = f"""
        <table>
            <tr>
                <th>{index_col}</th>
                {' '.join([f'<th>{col}</th>' for col in pivot_top_formateado.columns])}
            </tr>
        """
        
        # Añadir filas de datos
        for idx, row in pivot_top_formateado.iterrows():
            html += f"<tr><td>{idx}</td>"
            for col in pivot_top_formateado.columns:
                html += f"<td>{row[col]}</td>"
            html += "</tr>"
        
        html += "</table>"

        # Mostrar tabla
        st.markdown(f'<div class="title">{titulo}</div>', unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

        # Descargas
        col1, col2 = st.columns([1, 1])
        with col1:
            st.download_button(
                "⬇️ Descargar Top",
                data=generar_excel(pivot_top_formateado.reset_index()),
                file_name=f"{titulo} - Top.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            pivot_completo_formateado = pivot.drop(columns="TOTAL").applymap(formato_miles)
            st.download_button(
                "⬇️ Descargar Todo",
                data=generar_excel(pivot_completo_formateado.reset_index()),
                file_name=f"{titulo} - Todo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Mostrar los tops
    st.subheader("🏆 Top 10 por Ubicación")
    if dpto_seleccionado == "Todos":
        mostrar_top(df_filtrado, "DPTO", "🏙️ Top por Departamento")
    elif ciudad_seleccionada == "Todos":
        mostrar_top(df_filtrado, "CIUDAD", "🏙️ Top por Ciudad")

    mostrar_top(df_filtrado, "REFERENCIA", "📦 Top 20 Referencias", top_n=20)
    mostrar_top(df_filtrado, "RAZON SOCIAL", "🏢 Top 10 Razón Social", top_n=10)
elif pagina == "clientes":
    st.title("ℹ️ Clientes")
    
    # Agregar CSS personalizado para centralizar títulos de tablas
    # Agregar CSS personalizado para centralizar títulos de tablas
    st.markdown("""
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th {
                text-align: center !important;
                background-color: #f0f0f0;
                padding: 8px;
            }
            td {
                text-align: center;
                padding: 5px 10px;
            }
            .title {
                font-size: 1.5em;
                font-weight: bold;
                text-align: center;
                margin-top: 1em;
            }
            .tabla-centrada {
                width: 100%;
                border-collapse: collapse;
            }
            .tabla-centrada th {
                background-color: #f0f0f0;
                padding: 8px;
                text-align: center;
            }
            .tabla-centrada td {
                padding: 6px 10px;
                text-align: center;
            }
            .tabla-centrada tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .cero {
                color: red !important;
                font-weight: bold;
            }
            .stDownloadButton {
                text-align: center;
            }
        </style>
    """, unsafe_allow_html=True)

    # Cargar datos
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=None, engine="python", dtype={"AÑO": str, "MES": str, "DIA": str})
        df.columns = df.columns.str.strip()
        df.rename(columns=lambda x: x.strip(), inplace=True)
        return df

    df = cargar_datos()

    # Verificar columnas requeridas
    columnas_requeridas = {"AÑO", "MES", "DIA", "TOTAL V", "RAZON SOCIAL", "REFERENCIA"}
    if not columnas_requeridas.issubset(set(df.columns)):
        st.error(f"El archivo CSV debe contener las columnas exactas: {columnas_requeridas}")
    else:
        st.markdown("<h2 style='text-align:center;'>📊 Informe de Ventas</h2>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            razon_social_seleccionada = st.selectbox("Buscar Razón Social", [""] + sorted(df["RAZON SOCIAL"].unique()), index=0)
        with col2:
            año_seleccionado = st.selectbox("Año", ["Todos"] + sorted(df["AÑO"].unique()))

        df_filtrado = df.copy()

        if razon_social_seleccionada:
            df_filtrado = df_filtrado[df_filtrado["RAZON SOCIAL"].str.contains(razon_social_seleccionada, case=False, na=False)]

        if año_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["AÑO"] == año_seleccionado]

    if razon_social_seleccionada:
        st.markdown("<h2 style='text-align:center;'>📈 Ventas de la Razón Social</h2>", unsafe_allow_html=True)

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

            fig_bar.update_layout(
                yaxis_tickprefix="$",
                yaxis_ticksuffix="",
                yaxis_tickformat=",",
                xaxis_title=x_axis,
                yaxis_title="Ventas (Miles $)",
                title={
                    'text': "Ventas por Periodo",
                    'x': 0.5,  # Centrar el título
                    'xanchor': 'center'
                }
            )

            if x_axis == "AÑO":
                fig_bar.update_xaxes(type="category")

            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<h2 style='text-align:center;'>🏆 Top 20 REFERENCIAS</h2>", unsafe_allow_html=True)

        agrupador = "MES" if año_seleccionado != "Todos" else "AÑO"
        orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        if agrupador == "MES":
            df_filtrado["MES"] = pd.Categorical(df_filtrado["MES"], categories=orden_meses, ordered=True)

        top_ref = df_filtrado.groupby(["REFERENCIA", agrupador])["TOTAL V"].sum().reset_index()
        pivot_ref = top_ref.pivot(index="REFERENCIA", columns=agrupador, values="TOTAL V").fillna(0)
        pivot_ref["TOTAL"] = pivot_ref.sum(axis=1)
        pivot_ref = pivot_ref.sort_values("TOTAL", ascending=False).drop(columns="TOTAL").head(20)

        # Método 1: Usando HTML para mostrar la tabla con mejores estilos
        def formato_miles(x):
            return f"$ {x / 1_000:,.0f} K"

        # Crear una copia del dataframe para el formato HTML
        pivot_html = pivot_ref.copy().reset_index()
        
        # Guardar los valores originales para identificar ceros
        pivot_ceros = pivot_ref == 0
        
        # Formatear todos los valores
        for col in pivot_html.columns:
            if col != "REFERENCIA":
                pivot_html[col] = pivot_html[col].apply(lambda x: formato_miles(x))
        
        # Convertir a HTML
        html_table = "<table class='tabla-centrada'>"
        
        # Encabezados
        html_table += "<thead><tr>"
        for col in pivot_html.columns:
            html_table += f"<th>{col}</th>"
        html_table += "</tr></thead>"
        
        # Filas de datos
        html_table += "<tbody>"
        for i, row in pivot_html.iterrows():
            html_table += "<tr>"
            for j, col in enumerate(pivot_html.columns):
                value = row[col]
                if col != "REFERENCIA" and pivot_ceros.iloc[i, j-1]:  # -1 porque reset_index añade una columna
                    html_table += f"<td class='cero'>{value}</td>"
                else:
                    html_table += f"<td>{value}</td>"
            html_table += "</tr>"
        html_table += "</tbody></table>"
        
        # Mostrar la tabla con estilos aplicados
        st.markdown(html_table, unsafe_allow_html=True)

        # Método 2: Para la exportación usamos el pivot_ref original
        excel_buffer = io.BytesIO()
        excel_buffer_completo = io.BytesIO()

        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_excel = pivot_ref.reset_index()
            df_excel.to_excel(writer, sheet_name="Top Referencias", index=False)
            workbook = writer.book
            worksheet = writer.sheets["Top Referencias"]

            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1,
                'align': 'center'  # Centrar en el archivo Excel
            })

            for col_num, value in enumerate(df_excel.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Formato para celdas numéricas (alineadas a la derecha)
            number_format = workbook.add_format({
                'align': 'right',
                'num_format': '$ #,##0 K'
            })
            
            # Formato para celdas con ceros (texto en rojo)
            zero_format = workbook.add_format({
                'align': 'right',
                'num_format': '$ #,##0 K',
                'font_color': 'red',
                'bold': True
            })

            # Aplicar formatos según el valor
            for row_num in range(1, len(df_excel) + 1):
                for col_num in range(1, len(df_excel.columns)):  # Empezamos desde la segunda columna (después de REFERENCIA)
                    cell_value = df_excel.iloc[row_num-1, col_num] / 1000  # Convertir a miles
                    if df_excel.iloc[row_num-1, col_num] == 0:
                        worksheet.write_number(row_num, col_num, cell_value, zero_format)
                    else:
                        worksheet.write_number(row_num, col_num, cell_value, number_format)

            # Ajustar ancho de columnas
            for i, col in enumerate(df_excel.columns):
                column_width = max(df_excel[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)

        with pd.ExcelWriter(excel_buffer_completo, engine='xlsxwriter') as writer:
            df_filtrado.to_excel(writer, sheet_name="Datos Completos", index=False)
            workbook = writer.book
            worksheet = writer.sheets["Datos Completos"]

            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1,
                'align': 'center'  # Centrar en el archivo Excel
            })

            for col_num, value in enumerate(df_filtrado.columns.values):
                worksheet.write(0, col_num, value, header_format)

            for i, col in enumerate(df_filtrado.columns):
                column_width = max(df_filtrado[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)

        # Centrar los botones en columnas de igual ancho
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)

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

            # Título centrado para la primera tabla usando HTML
            st.markdown(f"""
            <h3 style='text-align: center;'>🏆 Top por {eje_x} - Ventas y Cantidad</h3>
            """, unsafe_allow_html=True)
            
            df_top = df_filtrado.groupby(eje_x).agg({"TOTAL V": "sum", "CANT": "sum"}).reset_index()
            df_top["TOTAL V"] = df_top["TOTAL V"].apply(lambda x: f"${x/1_000:,.0f}K")
            df_top["CANT"] = df_top["CANT"].astype(int)
            
            # Crear tabla HTML para el Top por Año/Mes con estilos
            html_table_top = """
            <table style="width:100%; border-collapse: collapse; margin: 10px auto;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
            """
            
            # Agregar encabezados
            for col in df_top.columns:
                html_table_top += f'<th style="padding: 10px; border: 1px solid #ddd; text-align: center;">{col}</th>'
            
            html_table_top += """
                    </tr>
                </thead>
                <tbody>
            """
            
            # Agregar filas de datos
            for _, row in df_top.iterrows():
                html_table_top += '<tr>'
                for col in df_top.columns:
                    html_table_top += f'<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{row[col]}</td>'
                html_table_top += '</tr>'
            
            html_table_top += """
                </tbody>
            </table>
            """
            
            # Mostrar la tabla HTML
            st.markdown(html_table_top, unsafe_allow_html=True)

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

            # Título centrado para la sección de Top 20
            st.markdown("""
            <h3 style='text-align: center;'>📌 Top 20 por Vendedor, Departamento, Ciudad y Cliente</h3>
            """, unsafe_allow_html=True)

            def mostrar_top_con_descarga(columna, titulo, nombre_archivo):
                top_df = df_filtrado.groupby(columna).agg({"TOTAL V": "sum", "CANT": "sum"}).reset_index()
                top_df = top_df.sort_values("TOTAL V", ascending=False).head(20)
                top_df["TOTAL V"] = top_df["TOTAL V"].apply(lambda x: f"${x/1_000:,.0f}K")

                # Subtítulo centrado para cada sección
                st.markdown(f"""
                <h4 style='text-align: center;'>🔹 {titulo}</h4>
                """, unsafe_allow_html=True)
                
                # Crear tabla HTML para el Top con estilos
                html_table = """
                <table style="width:100%; border-collapse: collapse; margin: 10px auto;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                """
                
                # Agregar encabezados
                for col in top_df.columns:
                    html_table += f'<th style="padding: 10px; border: 1px solid #ddd; text-align: center;">{col}</th>'
                
                html_table += """
                        </tr>
                    </thead>
                    <tbody>
                """
                
                # Agregar filas de datos
                for _, row in top_df.iterrows():
                    html_table += '<tr>'
                    for col in top_df.columns:
                        html_table += f'<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{row[col]}</td>'
                    html_table += '</tr>'
                
                html_table += """
                    </tbody>
                </table>
                """
                
                # Mostrar la tabla HTML
                st.markdown(html_table, unsafe_allow_html=True)

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
            mostrar_top_con_descarga("RAZON SOCIAL", "Top Clientes", "Top_Clientes")
            mostrar_top_con_descarga("VENDEDOR", "Top Vendedores", "Top_Vendedores")
            mostrar_top_con_descarga("CIUDAD", "Top Ciudades", "Top_Ciudades")
            mostrar_top_con_descarga("DPTO", "Top Departamentos", "Top_Departamentos")
            
            

    else:
        st.warning("⚠️ Por favor seleccione una Referencia para ver información.")

elif pagina=="Comparativo Ref":
    st.title("🔢 Comparativo por referencia")
    @st.cache_data
    def cargar_datos():
        try:
            df = pd.read_csv("Informe ventas.csv", sep=";")
        except:
            df = pd.read_csv("Informe ventas.csv", sep=",")
        df.columns = df.columns.str.strip()
        df["AÑO"] = df["AÑO"].astype(int)
        df["MES"] = df["MES"].str.upper()
        orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        df["MES"] = pd.Categorical(df["MES"], categories=orden_meses, ordered=True)
        return df

    def tabla_html_centrada(df, formato_columnas=None, nombre_indice=""):
        df_copy = df.copy()
        df_copy.index.name = None
        if nombre_indice:
            df_copy.index.name = nombre_indice

        html = '<table style="width: 100%; border-collapse: collapse; text-align: center;">'
        html += '<thead><tr style="background-color: #f0f0f0;">'
        if df_copy.index.name:
            html += f'<th>{df_copy.index.name}</th>'
        else:
            html += '<th></th>'
        for col in df_copy.columns:
            html += f'<th>{col}</th>'
        html += '</tr></thead><tbody>'

        for idx, row in df_copy.iterrows():
            html += '<tr>'
            html += f'<td><b>{idx}</b></td>'
            for col in df_copy.columns:
                val = row[col]
                if formato_columnas and col in formato_columnas:
                    val = formato_columnas[col](val)
                html += f'<td>{val}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        return html

    # Función modificada para mostrar top 10 por mayor volumen de ventas
    def mostrar_top10(df, columna, titulo, año1=None, año2=None):
        st.markdown(f"<h4 style='text-align: center;'>🏆 Top 10 {titulo}</h4>", unsafe_allow_html=True)
        
        # Si no hay años específicos, mostrar el top 10 general
        if año1 is None or año2 is None:
            top10 = df.groupby(columna)["TOTAL V"].sum().reset_index()
            top10["TOTAL V"] = top10["TOTAL V"] / 1_000
            top10 = top10.sort_values("TOTAL V", ascending=False).head(10)
            
            # Crear tabla HTML - cambiando el color del encabezado de rojo intenso a un gris claro
            html = '<table style="width: 100%; border-collapse: collapse; text-align: center;">'
            html += '<thead><tr style="background-color: #f0f0f0;">'
            html += f'<th>Posición</th><th>{columna}</th><th>Ventas</th>'
            html += '</tr></thead><tbody>'
            
            for i, (_, row) in enumerate(top10.iterrows(), 1):
                html += '<tr>'
                html += f'<td><b>#{i}</b></td>'
                html += f'<td>{row[columna]}</td>'
                html += f'<td>${row["TOTAL V"]:,.0f}K</td>'
                html += '</tr>'
            html += '</tbody></table>'
        else:
            # Si hay años específicos, mostrar con crecimiento/decrecimiento pero ordenado por mayor volumen
            df_año1 = df[df["AÑO"] == año1].groupby(columna)["TOTAL V"].sum() / 1000
            df_año2 = df[df["AÑO"] == año2].groupby(columna)["TOTAL V"].sum() / 1000
            
            df_comparacion = pd.DataFrame({
                f'{año1}': df_año1,
                f'{año2}': df_año2
            }).fillna(0)
            
            df_comparacion['% Cambio'] = (
                (df_comparacion[f'{año2}'] - df_comparacion[f'{año1}']) / 
                df_comparacion[f'{año1}'].replace(0, 1)
            ) * 100
            
            # Ordenar por el valor de ventas en el segundo año (más reciente)
            top10 = df_comparacion.nlargest(10, f'{año2}')
            
            # Crear tabla HTML con estilos modificados
            html = '<table style="width: 100%; border-collapse: collapse; text-align: center;">'
            html += '<thead><tr style="background-color: #f0f0f0;">'
            html += f'<th>{columna}</th><th>{año1}</th><th>{año2}</th><th>% Cambio</th>'
            html += '</tr></thead><tbody>'
            
            for item, row in top10.iterrows():
                html += '<tr>'
                html += f'<td>{item}</td>'
                
                # Aplicar color rojo para valores en cero
                if row[f"{año1}"] == 0:
                    html += f'<td><span style="color:red; font-weight: bold">${row[f"{año1}"]:,.0f}K</span></td>'
                else:
                    html += f'<td>${row[f"{año1}"]:,.0f}K</td>'
                    
                if row[f"{año2}"] == 0:
                    html += f'<td><span style="color:red; font-weight: bold">${row[f"{año2}"]:,.0f}K</span></td>'
                else:
                    html += f'<td>${row[f"{año2}"]:,.0f}K</td>'
                    
                # Modificar estilo para % Cambio
                color = "green" if row["% Cambio"] >= 0 else "red"
                html += f'<td><span style="color:{color}; font-weight: bold">{row["% Cambio"]:+.2f}%</span></td>'
                html += '</tr>'
            html += '</tbody></table>'
        
        st.markdown(html, unsafe_allow_html=True)
        
        return top10

    df = cargar_datos()
    df['TOTAL V'] = df['TOTAL V'].astype('int64')

    # Agregar segmentador de referencias al inicio
    referencias = df["REFERENCIA"].dropna().unique()
    referencia_seleccionada = st.selectbox("🔍 Seleccione una Referencia:", ["Todas"] + sorted(referencias))

    # Aplicar filtro de referencia si se ha seleccionado una específica
    if referencia_seleccionada != "Todas":
        df_filtrado = df[df["REFERENCIA"] == referencia_seleccionada].copy()
        st.success(f"Mostrando datos para la referencia: {referencia_seleccionada}")
    else:
        df_filtrado = df.copy()
        st.info("Mostrando datos para todas las referencias")

    años_disponibles = sorted(df_filtrado["AÑO"].unique())

    col1, col2 = st.columns(2)
    with col1:
        año1 = st.selectbox("Selecciona AÑO 1:", ["Todos"] + años_disponibles)
    with col2:
        año2 = st.selectbox("Selecciona AÑO 2:", ["Todos"] + años_disponibles)

    if (año1 != "Todos" and año2 == "Todos") or (año2 != "Todos" and año1 == "Todos"):
        st.warning("⚠️ Si seleccionas un año específico, debes seleccionar otro para comparar.")
    else:
        if año1 == "Todos" and año2 == "Todos":
            # Primero mostrar la gráfica
            df_group = df_filtrado.groupby(["MES", "AÑO"])["TOTAL V"].sum().reset_index()
            df_group["TOTAL V"] = df_group["TOTAL V"] / 1_000
            df_group = df_group.sort_values(by=["MES", "AÑO"])

            titulo_referencia = f" para {referencia_seleccionada}" if referencia_seleccionada != "Todas" else ""
            st.markdown(f"<h3 style='text-align: center;'>📊 Comparación de ventas por MES{titulo_referencia}</h3>", unsafe_allow_html=True)

            fig = go.Figure()
            años = sorted(df_group["AÑO"].unique())
            colores = px.colors.qualitative.Set2[:len(años)]
            for i, año in enumerate(años):
                df_año = df_group[df_group["AÑO"] == año]
                fig.add_trace(go.Bar(
                    x=df_año["MES"],
                    y=df_año["TOTAL V"],
                    name=str(año),
                    marker_color=colores[i % len(colores)]
                ))
            fig.update_layout(
                barmode='group',
                yaxis_title="Ventas ($K)",
                xaxis_title="Mes",
                plot_bgcolor="#fafafa",
                bargap=0.3,
                bargroupgap=0.1,
                xaxis={'categoryorder': 'array', 'categoryarray': df_filtrado["MES"].cat.categories}
            )
            st.plotly_chart(fig, use_container_width=True)

            # Luego mostrar la tabla
            st.markdown(f"<h3 style='text-align: center;'>📋 Tabla de ventas por MES y AÑO{titulo_referencia}</h3>", unsafe_allow_html=True)
            tabla_pivot = df_group.pivot(index="MES", columns="AÑO", values="TOTAL V").fillna(0)
            
            # Formatear con ceros en rojo - MODIFICADO
            def formato_con_ceros(x):
                if x == 0:
                    return f'<span style="color:red; font-weight: bold">${x:,.0f}K</span>'
                return f"${x:,.0f}K"
                
            html_tabla = tabla_html_centrada(tabla_pivot, formato_columnas={col: formato_con_ceros for col in tabla_pivot.columns})
            st.markdown(html_tabla, unsafe_allow_html=True)

            buffer = BytesIO()
            tabla_pivot.to_excel(buffer, index=True)
            st.download_button(
                label="📥 Descargar Excel",
                data=buffer.getvalue(),
                file_name=f"ventas_todos_los_años{'_'+referencia_seleccionada if referencia_seleccionada != 'Todas' else ''}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Finalmente mostrar los top 10 (cada uno ocupando todo el ancho)
            if not df_filtrado.empty:
                st.markdown("<h3 style='text-align: center;'>🏢 Top 10 por Ventas</h3>", unsafe_allow_html=True)
                top10_clientes = mostrar_top10(df_filtrado, "RAZON SOCIAL", "Clientes")
                
                st.markdown("<h3 style='text-align: center;'>🧑‍💼 Top 10 por Ventas</h3>", unsafe_allow_html=True)
                top10_vendedores = mostrar_top10(df_filtrado, "VENDEDOR", "Vendedores")

        else:
            # Primero mostrar la gráfica
            df_comp = df_filtrado[df_filtrado["AÑO"].isin([año1, año2])]
            tabla = df_comp.groupby(["AÑO", "MES"])["TOTAL V"].sum().reset_index()
            tabla["TOTAL V"] = tabla["TOTAL V"] / 1_000
            tabla["MES"] = pd.Categorical(tabla["MES"], categories=df_filtrado["MES"].cat.categories, ordered=True)
            tabla = tabla.sort_values(by=["MES", "AÑO"])

            titulo_referencia = f" para {referencia_seleccionada}" if referencia_seleccionada != "Todas" else ""
            st.markdown(f"<h3 style='text-align: center;'>📊 Comparación de ventas mensuales entre {año1} y {año2}{titulo_referencia}</h3>", unsafe_allow_html=True)

            fig = go.Figure()
            df_año1 = tabla[tabla["AÑO"] == año1]
            fig.add_trace(go.Bar(
                x=df_año1["MES"],
                y=df_año1["TOTAL V"],
                name=str(año1),
                marker_color="#2ecc71"
            ))
            df_año2 = tabla[tabla["AÑO"] == año2]
            fig.add_trace(go.Bar(
                x=df_año2["MES"],
                y=df_año2["TOTAL V"],
                name=str(año2),
                marker_color="#e74c3c"
            ))
            fig.update_layout(
                barmode='group',
                yaxis_title="Ventas ($K)",
                xaxis_title="Mes",
                plot_bgcolor="#fafafa",
                bargap=0.3,
                bargroupgap=0.1,
                xaxis={'categoryorder': 'array', 'categoryarray': df_filtrado["MES"].cat.categories}
            )
            st.plotly_chart(fig, use_container_width=True)

            # Luego mostrar la tabla
            tabla_pivot = tabla.pivot(index="MES", columns="AÑO", values="TOTAL V").fillna(0)
            tabla_pivot["% CRECIMIENTO"] = (
                (tabla_pivot[año2] - tabla_pivot[año1]) / tabla_pivot[año1].replace(0, 1)
            ) * 100
            tabla_pivot["% CRECIMIENTO"] = tabla_pivot["% CRECIMIENTO"].round(2)

            st.markdown(f"<h3 style='text-align: center;'>📋 Tabla comparativa de ventas y % crecimiento{titulo_referencia}</h3>", unsafe_allow_html=True)

            # FUNCIÓN MODIFICADA para formatear los valores
            def formato(x, col):
                if col == "% CRECIMIENTO":
                    color = "red" if x<0 else "green"
                    return f'<span style="color:{color}; font-weight: bold">{x:+.2f}%</span>'
                else:
                    if x == 0:
                        return f'<span style="color:red; font-weight: bold">${x:,.0f}K</span>'
                    return f"${x:,.0f}K"

            html_tabla = tabla_html_centrada(
                tabla_pivot,
                formato_columnas={col: lambda x, col=col: formato(x, col) for col in tabla_pivot.columns}
            )
            st.markdown(html_tabla, unsafe_allow_html=True)

            # Cálculo y visualización del crecimiento total
            total_año1 = tabla[tabla["AÑO"] == año1]["TOTAL V"].sum()
            total_año2 = tabla[tabla["AÑO"] == año2]["TOTAL V"].sum()
            crecimiento_total = ((total_año2 - total_año1) / total_año1) * 100 if total_año1 > 0 else 0
            
            color_crecimiento = "green" if crecimiento_total >= 0 else "red"
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; text-align: center;">
                <h4>Resumen de {referencia_seleccionada if referencia_seleccionada != "Todas" else "todas las referencias"}</h4>
                <p>Total {año1}: <b>${total_año1:,.0f}K</b></p>
                <p>Total {año2}: <b>${total_año2:,.0f}K</b></p>
                <p>Crecimiento total: <span style="color: {color_crecimiento}; font-weight: bold;">{crecimiento_total:+.2f}%</span></p>
            </div>
            """, unsafe_allow_html=True)

            buffer2 = BytesIO()
            tabla_pivot.to_excel(buffer2, index=True)
            st.download_button(
                label="📥 Descargar Excel",
                data=buffer2.getvalue(),
                file_name=f"comparativa_{año1}_vs_{año2}{'_'+referencia_seleccionada if referencia_seleccionada != 'Todas' else ''}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Finalmente mostrar los top 10 (cada uno ocupando todo el ancho)
            if not df_filtrado.empty:
                st.markdown("<h3 style='text-align: center;'>🏢 Top 10 Clientes por Ventas</h3>", unsafe_allow_html=True)
                top10_clientes = mostrar_top10(df_filtrado, "RAZON SOCIAL", "Clientes", año1, año2)
                
                st.markdown("<h3 style='text-align: center;'>🧑‍💼 Top 10 Vendedores por Ventas</h3>", unsafe_allow_html=True)
                top10_vendedores = mostrar_top10(df_filtrado, "VENDEDOR", "Vendedores", año1, año2)

elif pagina=="Comparativo por Grupo":
    st.title("🔢 Comparativo por Grupo")
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Informe ventas.csv", sep=";")
        df.columns = df.columns.str.strip()
        df["AÑO"] = df["AÑO"].astype(int)
        return df

    def mostrar_top20_por_grupo(df, grupo_col, grupo_nombre, año1, año2):
        st.markdown(f"<h4 style='text-align: center;'>📊 Top 20 {grupo_nombre}</h4>", unsafe_allow_html=True)

        df1 = df[df["AÑO"] == año1].groupby(grupo_col)["TOTAL V"].sum() / 1000
        df2 = df[df["AÑO"] == año2].groupby(grupo_col)["TOTAL V"].sum() / 1000

        df_merged = pd.DataFrame({
            f"{año1}": df1,
            f"{año2}": df2
        }).fillna(0)

        df_merged["% Cambio"] = ((df_merged[f"{año2}"] - df_merged[f"{año1}"]) / df_merged[f"{año1}"].replace(0, 1)) * 100
        df_top20 = df_merged.sort_values(by=f"{año2}", ascending=False).head(20)

        html = '<table style="width: 100%; border-collapse: collapse; text-align: center;">'
        html += f'<thead><tr style="background-color: #f0f0f0;"><th>{grupo_col}</th><th>{año1} </th><th>{año2} </th><th>% Cambio</th></tr></thead><tbody>'

        for idx, row in df_top20.iterrows():
            color = "green" if row["% Cambio"] >= 0 else "red"
            html += f"<tr><td>{idx}</td>"
            html += f"<td>${row[f'{año1}']:,.0f}K</td><td>${row[f'{año2}']:,.0f}K</td>"
            html += f"<td><span style='color:{color}; font-weight:bold'>{row['% Cambio']:+.2f}%</span></td></tr>"

        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)

    # App principal
    df = cargar_datos()
    años = sorted(df["AÑO"].unique())

    col1, col2 = st.columns(2)
    with col1:
        año1 = st.selectbox("Selecciona AÑO 1:", [""] + años)
    with col2:
        año2 = st.selectbox("Selecciona AÑO 2:", [""] + años)

    if (año1 and not año2) or (año2 and not año1):
        st.warning("⚠️ Si seleccionas un año, debes seleccionar el otro para comparar.")
    elif año1 and año2:
        mostrar_top20_por_grupo(df, "GRUPO TRES", "Grupo Tres", año1, año2)
        mostrar_top20_por_grupo(df, "GRUPO CUATRO", "Grupo CUATRO", año1, año2)

if pagina == "Geolocalización":
    # Cargar los datos
    import pydeck as pdk
    import numpy as np  # Añadida la importación de NumPy
    from streamlit_folium import folium_static
    import folium
    from folium.plugins import HeatMap
    
    # Cargar datos
    # ---------- CARGA DE DATOS ----------
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

    # Aseguramos que los nombres de columnas sean correctos
    if "DPTO" in df.columns and "CIUDAD" in df.columns and "DEPARTAMENTO" in df_geo.columns:
        df = df.merge(df_geo, how="left", left_on=["DPTO", "CIUDAD"], right_on=["DEPARTAMENTO", "CIUDAD"])
    else:
        st.error("❌ Asegúrate de que las columnas 'DPTO' y 'CIUDAD' estén en el archivo de ventas, y 'DEPARTAMENTO' y 'CIUDAD' en la geolocalización.")

    # ---------- FILTROS ----------
    st.subheader("📍 Segmentación del Mapa de Ventas")

    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)

    año_sel = col1.selectbox("Año", ["Todos"] + sorted(df["AÑO"].dropna().unique()))
    vendedor_sel = col2.selectbox("Vendedor", ["Todos"] + sorted(df["VENDEDOR"].dropna().unique()))
    referencia_sel = col3.selectbox("Referencia", ["Todos"] + sorted(df["REFERENCIA"].dropna().unique()))
    gr3_sel = col4.selectbox("Grupo Tres", ["Todos"] + sorted(df["GRUPO TRES"].dropna().unique()))
    gr4_sel = col5.selectbox("Grupo Cuatro", ["Todos"] + sorted(df["GRUPO CUATRO"].dropna().unique()))

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

    # ---------- MAPA ----------
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

            st.markdown("""### 🎯 Interpretación del Mapa:
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

    