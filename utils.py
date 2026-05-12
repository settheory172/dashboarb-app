"""
This module is in charge of managing the functions that print the information in the dashboard or main file called login.py

"""
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st
import plotly.express as px
from thefuzz import process, fuzz
import numpy as np
import datetime

"""Sets a connections to google drive sheet and order and rename all columns""" 
@st.cache_data(show_spinner = 'Recogiendo los datos desde la API...' )
def load_data():
    #conn.read() is effectively pd.read_csv() but for the cloud it returns a DataFrame you can chain Pandas methods directly 
    conn = st.connection('gsheets', type=GSheetsConnection)
    df = conn.read()
    columns_ordered = ['company_name','date','descripcin','vrtotal']
    df = df[columns_ordered]
    df = df.rename(columns={'company_name':'cliente','date':'fecha','descripcin':'detalle','vrtotal':'total'})
    return df 

"""depending on the role if role is user is shows raw data"""
def prepare_data(role = 'user'):
    df = load_data()
    
    if role == st.session_state['username']:
        # if it is not a gests then gets the raw 'total'
        return df, 'total'
    else:
        # Calculate the percentage for guests
        df['porcentaje'] = (df['total'] / df['total'].sum()) * 100
        #df['frecu_rel'] = df['total'].map(df['total'].value_counts(normalize=True))
        df_p = df.drop(columns=['total'])
        return df_p, 'porcentaje'

"""
to standardized some names of clients or costumers taking dataframe and column as 
total and an adapatable threshold returns new column with standardized names
"""
def consolidate_names(df, column_name, threshold=85):
    """
    Finds similar strings in a column and maps them to a single standardized name.
    """
    unique_names = df[column_name].unique().tolist()
    mapping = {}
    
    for name in unique_names:
        # If we haven't already mapped this name, it becomes a new "Base Name"
        if name not in mapping:
            # Find all names that are similar to this Base Name
            # token_set_ratio is great for ignoring extra words like "S.A.S" or "FANALCA"
            matches = process.extract(name, unique_names, scorer=fuzz.token_set_ratio, limit=None)
            
            for match_name, score in matches:
                if score >= threshold and match_name not in mapping:
                    mapping[match_name] = name # Map the variation to the Base Name
                    
    # Return a new series with the standardized names
    return df[column_name].map(mapping)

"""To standardized the style of the table on a greenish format given the dataframe and the target_column=total"""
def display_styled_table(df, target_column, color_map='Greens'):
    """
    Applies background gradient and currency formatting to a specific column
    and displays it in Streamlit using the full container width.
    """
    # 1. Apply the styling logic
    styled_df = df.style.background_gradient(
        subset=[target_column], 
        cmap=color_map
    ).format({target_column: '{:,.0f}'})
    
    # 2. Render the dataframe
    return st.dataframe(
        styled_df, 
        use_container_width=True, 
        hide_index=True
    )

"""To standardized the style of graph on a greenish format given figure, title, x and y and returns modified figure"""    
def plot_chart_theme(fig, title_text=None, x_label=None, y_label=None):
    """
    Applies a consistent dark green theme to any Plotly figure.
    """
    # Update Axes Labels
    labels = {}
    if x_label: labels['xaxis_title'] = x_label
    if y_label: labels['yaxis_title'] = y_label
    if title_text: labels['title'] = title_text
    
    fig.update_layout(
        title_x=0.5, # True centering is usually 0.5
        title_font=dict(size=30, color='#4ECDC4'),
        font=dict(color='#E0F7E0'),
        
        # Background Colors
        plot_bgcolor='#0D2818',
        paper_bgcolor='#051010',
        
        # Margins and Size
        margin=dict(l=50, r=20, t=80, b=50),
        height=500,
        
        # Apply labels dynamically
        **labels
    )

    # Force category order for bar charts specifically
    if fig.data and fig.data[0].type == 'bar':
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        
    return fig
  
"""shows top_n of most sold product, taking a dataframe and target_column=total it returns barchart and table of ranks"""  
def ranking_product(df, target_column = 'total', top_n= 15):

    # 1. Aggregate revenue by product description
    revenue_ranking = df.groupby('detalle')[target_column].sum().reset_index()
    # 2. Get the Most Sold (Highest Revenue)
    top_earners = revenue_ranking.sort_values(by=target_column, ascending=False).head(top_n)
    # 3. Get the Least Sold (Lowest Revenue) Sort ascending so the lowest earner is at the top
    bottom_earners = revenue_ranking.sort_values(by=target_column, ascending=True)

    col1, col2 = st.columns(2)

    with col1:
        top_product = top_earners.iloc[0]
        st.metric(label='Producto con mayor valor en ventas', 
                  value=top_product['detalle'], 
                  delta=top_product[target_column],
                  delta_arrow='off',
                  format= 'accounting',
                  border=True,)

    with col2:
        bottom_product = bottom_earners.iloc[0]
        st.metric(label='Productos con menor valor en ventas', 
                  value=bottom_product['detalle'], 
                  delta=bottom_product[target_column],
                  delta_color='orange',
                  delta_arrow='off',
                  format='accounting', 
                  border=True,) # Red if low revenue is 'bad'

    # 1. Prepare and sort your Top 10 (Highest to Lowest) we use ascending=True to put the biggest at the top of the chart.
    top_10_sorted = top_earners.sort_values(by=target_column, ascending=True).tail(top_n) 

    # 2. Create the horizontal bar chart
    fig = px.bar(
        top_10_sorted, 
        x=target_column, 
        y='detalle', 
        orientation='h',
        title=f'Top {top_n} Productos por Venta',
        labels={target_column: 'Ventas Totales ($)', 'detalle': 'Producto'},
        color_discrete_sequence=['#2ecc71'] # Your green color
    )


    # 3. Display in Streamlit
    with st.container(): # The border is optional but looks great
        st.subheader(f'Ranking de los {top_n} productos mayormente vendidos')
        display_styled_table(top_earners,target_column=target_column)
        fig = (plot_chart_theme(fig)) 
        st.plotly_chart(fig, use_container_width=True)
        st.caption('Nota: Datos basados desde el inicio de la empresa.')
        st.divider()
  
"""shows top_n of clients with most the purchases, taking a dataframe and target_column=total it returns scatterchart"""  
def ranking_clients(df,target_column = 'total', top_n = 15):
    #totalizes the purchases by clients
    total_purchased = df.groupby('cliente')[target_column].sum().reset_index()
    # Apply the fuzzy matching
    total_purchased['cliente_estandar'] = consolidate_names(total_purchased, 'cliente')
    total_purchased = total_purchased.drop(columns=['cliente'])
    # Group by the new standard name and sum the totals
    total_grouped = total_purchased.groupby('cliente_estandar', as_index=False)[target_column].sum()
    # Sort by total descending for better presentation
    total_grouped = total_grouped.sort_values(by=target_column, ascending=False).reset_index(drop=True)
    
    # Option B: Interactive Plotly Chart (Recommended for clarity)
    fig = px.scatter(
        total_grouped, 
        x='cliente_estandar', 
        y=target_column,
        size =target_column,
        color=target_column,          # Bubble color based on purchases
        hover_name='cliente_estandar',   # Show client name on hover
        title='comportamiento de las ventas por cliente',
        labels={'cliente_estandar': 'Cliente', target_column: 'Total en compras ($)'},
        #color_continuous_scale='Greens'
        )
    

    with st.container():
        #st.dataframe(total_purchased, use_container_width=True)
        st.subheader(f'Top {top_n} de clientes')
        display_styled_table(total_grouped,target_column=target_column)
        fig = plot_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.divider()
        
"""function that calculates the time custumers spent making purchases by using KPI CLV and returns
    formula and specific metrics to obtain CLV calculation
"""        
def customer_lifetime_value (df, target_column):
    # 1. Ensure date is in datetime format
    #df['fecha'] = pd.to_datetime(df['fecha'])
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')

    # 2. Calculate APV (Average Purchase Value)
    # We group by date and cliente to define a unique "transaction"
    order_totals = df.groupby(['cliente', 'fecha'])[target_column].sum()
    apv = order_totals.mean()

    # 3. Calculate Purchase Frequency
    total_orders = order_totals.count()
    total_customers = df['cliente'].nunique()
    purchase_frequency = total_orders / total_customers

    # 4. Calculate Average Customer Lifespan (in years)
    lifespans = df.groupby('cliente')['fecha'].agg(lambda x: (x.max() - x.min()).days / 365)
    customer_lifespan = lifespans.mean()

    # If your data is from a short time range, lifespan might be 0. 
    # You may need to set a "constant" lifespan if you haven't been in business long.
    if customer_lifespan == 0:
        customer_lifespan = 1 

    # 5. Final CLV Calculation
    clv = apv * purchase_frequency * customer_lifespan
    
    st.title('Valor de Vida del Cliente o CLV Analisis')

    col1, col2, col3, col4 = st.columns(4)
    
    with st. container():
        col1.metric('Promedio valor de compra o APV', f'{apv:,.0f}')
        col2.metric('Frecuencia de compra o PF', f'{purchase_frequency:.0f}x')
        col3.metric('Promedio de vida anual o AL', f'{customer_lifespan:.0f}')
        col4.metric('Total CLV', f'${clv:,.0f}', delta_color='normal')
        
    with st. expander('Ver formula:'):
        st.info(f'**Formula:** ${apv:,.0f} (APV) × {purchase_frequency:.0f} (Freq) × {customer_lifespan:.0f} (Lifespan) = **${clv:,.0f}**')
        
    st.divider()
     
"""calculate revenue monthly from purchases it returns the most recent earning, trends of growth as line graphs and chart
    and a summary chart from dec 2020 to april 2026 
"""     
def monthly_growth_rate(df, target_column):
    # Ensure the date column is an actual datetime object
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
    
    st.title('📈 Tasa de ganancias mensual')
        
    # --- CALCULATE GROWTH RATE ---

    # A. Group the data by a specific period (e.g., Monthly)
    # We extract the Year-Month period from the date
    df['mes'] = df['fecha'].dt.to_period('M')

    # Sum the 'Cost' (Revenue) for each month
    monthly_df = df.groupby('mes')[target_column].sum().reset_index()
    
    # B. Apply the Growth Rate Formula
    # pct_change() automatically calculates: (Current - Previous) / Previous
    monthly_df['Tasa de crecimiento (%)'] = monthly_df[target_column].pct_change() * 100
    
    # Fill the first month's NaN value (since there is no previous month to compare to) with 0
    monthly_df['Tasa de crecimiento (%)'] = monthly_df['Tasa de crecimiento (%)'].fillna(0)
    
    # Convert the 'Month' period back to a string so Streamlit can chart it easily
    monthly_df['mes'] = monthly_df['mes'].astype(str)
    
    # --- 3. DISPLAY RESULTS IN STREAMLIT ---

    st.subheader('Ganacias mensuales & Resumen de crecimiento')
    # Display the aggregated dataframe
    st.dataframe(
        monthly_df.style.format({
            target_column: '{:,.0f}',
            'Tasa de crecimiento (%)': '{:.0f}%'
        }),
        use_container_width=True
    )

    # Visualizing the Growth Rate
   
    #st.line_chart(data=monthly_df, x='mes', y='Tasa de crecimiento (%)')
    #st.divider()
    
    fig = px.line(
        monthly_df, 
        x='mes', 
        y='Tasa de crecimiento (%)',
        title='Tendencias de tasa de crecimiento',
        labels={'mes': 'mes', 'Tasa de crecimiento(%)': 'Tasa de crecimiento(%)'},
        )
    
    fig = (plot_chart_theme(fig)) 
    #st.plotly_chart(fig, use_container_width=True)
    
    # --- 4. HIGHLIGHT CURRENT METRICS ---
    # Use Streamlit's metric component to show a dashboard-style summary
    st.subheader('Reciente performance')

    if len(monthly_df) >= 2:
        latest_revenue = monthly_df.iloc[-1][target_column]
        latest_growth = monthly_df.iloc[-1]['Tasa de crecimiento (%)']
        
        st.metric(
            label=f'Ganancia por {monthly_df.iloc[-1]['mes']}', 
            value=f'{latest_revenue:,.0f}', 
            delta=f'{latest_growth:.0f}% (vs Mes anterior)'
        )
    
    st.subheader('Tendencias de tasa de crecimiento')
    tab1, tab2, tab3 = st.tabs(['Linea meses','linea aprox','datos'])
    
    with tab1:
        st.line_chart(data=monthly_df, x='mes', y='Tasa de crecimiento (%)')
    with tab2:
        st.plotly_chart(fig, use_container_width=True)
    with tab3:
        display_styled_table(monthly_df,target_column=target_column)
   
"""it shows initial and current earnings from 2020 to 2026 and percentage using KPI CARG and return chart and line graph of
    every year in revenue
"""
def compund_annual_growth_rate(df, target_column):
    # --- 1. GROUP DATA BY YEAR ---
    # We need annual totals to calculate CAGR properly
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
    df['anual'] = df['fecha'].dt.year
    yearly_df = df.groupby('anual')[target_column].sum().reset_index()
    st.divider()
    st.title("Ganancia anual:")
    
    #Interactive Plotly Chart (Recommended for clarity)
    fig = px.line(
        yearly_df, 
        x='anual', 
        y=target_column, 
        markers=True,
        title='comportamiento de las ventas anuales',
        labels={'Anual': 'Anual', target_column: 'Ventas totales ($)'}
    )
    
    # --- 2. EXTRACT VARIABLES FOR THE FORMULA ---
    # Get the first and last years in the dataset
    first_year = yearly_df['anual'].iloc[0]
    last_year = yearly_df['anual'].iloc[-1]

    # Get the revenue for those specific years
    beginning_value = yearly_df[target_column].iloc[0]
    ending_value = yearly_df[target_column].iloc[-1]

    # Calculate 'n' (number of years)
    n = last_year - first_year
    # --- 3. CALCULATE CAGR ---
    # We wrap this in an 'if' statement to avoid dividing by zero 
    # if your dataset only spans a single year.
    if n > 0:
        cagr = ((ending_value / beginning_value) ** (1 / n)) - 1
        cagr_percentage = cagr * 100
        
        # --- 4. DISPLAY IN STREAMLIT ---
        col1, col2, col3 = st.columns(3)
        col1.metric(label=f"Valor inicial ({first_year})", value=f"{beginning_value:,.0f}")
        col2.metric(label=f"Valor final ({last_year})", value=f"{ending_value:,.0f}")
        col3.metric(label=f"{n}-años Tasa de Crecimiento Anual Compuesta o CAGR", value=f"{cagr_percentage:.0f}%")

    else:
        st.info("CAGR requiere de al menos dos valores diferentes para calculado.")
    
    with st.container(): # The border is optional but looks great
        # Show the summary table
        st.subheader("Total de ventas anuales")
        display_styled_table(yearly_df,target_column=target_column)
        #shows yearly purchases line chart
        fig = plot_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.divider()
 
"""calculates KPI rate of clients that are retained or already abandoned, 
but user defines by slider how many days are considered abandonment by the costumers it returns
percentage of retained and abandoned costumers, a chart with infor about last purchase,total revenue, number of orders
and days of being inactive and a category of retained or abandoned from dec 2020 to apr 2026 
""" 
def client_retention_abandonment(df, target_column):
    #st.dataframe(df)
    st.title('Valores de clientes que han abandonado o se retienen')
    # --- 1. DEFINE THE PARAMETERS ---
    # We use the most recent purchase in the whole dataset as our "Today" marker
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
    analysis_min = df['fecha'].min()
    analysis_max = df['fecha'].max()
    st.write(f'Analisis desde: **{analysis_min.strftime('%d-%m-%y')}**; hasta: **{analysis_max.strftime('%d-%m-%y')}.**')
    
    # Streamlit Slider: Let the user define what "Abandoned" means!
    churn_threshold = st.slider(
        'Cantidad de dias sin compra para ser considerado **ABANDONO**', 
        min_value=30, 
        max_value=365, 
        value=90 # Default to 90 days
    )
    
 
    client_stats = df.groupby(['cliente','fecha'])[target_column].sum().reset_index()
    client_stats['cliente_estandar'] = consolidate_names(client_stats, 'cliente')
    client_stats = client_stats.drop(columns=['cliente'])
    #st.dataframe(client_stats)
    
    # --- 2. CALCULATE PER-CLIENT STATS ---
    # Group by client to find their last purchase date and total spent
    clientes = client_stats.groupby('cliente_estandar').agg(
        ultima_compra=('fecha', 'max'),
        Total_gastado =(target_column, 'sum'),
        Total_Ordenes=(target_column, 'count')).reset_index()
      
  
    # Calculate exactly how many days it has been since their last purchase
    clientes['Dias inactivo'] = (analysis_max - clientes['ultima_compra']).dt.days
    
    # Classify them as Retained or Abandoned based on the slider value
    clientes['Estatus'] = clientes['Dias inactivo'].apply(
        lambda x: 'Retenido' if x <= churn_threshold else 'Abandono'
    )
     
    # --- 3. CALCULATE OVERALL RATES ---
    total_clients = len(clientes)
    retained_count = len(clientes[clientes['Estatus'] == 'Retenido'])
    abandoned_count = total_clients - retained_count

    retention_rate = (retained_count / total_clients) * 100
    abandon_rate = (abandoned_count / total_clients) * 100
    
    # --- 4. DISPLAY TOP-LEVEL METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric('Total clientes', total_clients)
    col2.metric('Tasa de retenidos', f'{retention_rate:.1f}%', f'{retained_count} Clientes activos')
    # Using delta_color="inverse" makes the red arrow show up for high churn (which is bad)
    col3.metric('Tasa de abandono', f'{abandon_rate:.1f}%', f'{abandoned_count} Clientes que abandonaron', delta_color='inverse', delta_arrow='down')

    # --- 5. DISPLAY PER-CLIENT BREAKDOWN ---
    st.subheader('Tabla que abandonaron y se retienen')

    # Clean up the dataframe for display
    display_df = clientes.copy()
    display_df['ultima_compra'] = display_df['ultima_compra'].dt.strftime('%d-%m-%y')

    st.dataframe(
        display_df.style.format({
            'Total_gastado': '{:,.0f}'
        }),
        use_container_width=True
    )
    
    st.divider()
    
"""plots a linegraph the the revenue generated every year in months as a comparison"""
def years_revenue (df, target_column):
    # 0. Define the Spanish mapping
    month_map = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    #1. Ensure dat format
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
    # 2. Extract Year and Month Name for the chart
    df['anual'] = df['fecha'].dt.year.astype(str)  # Convert to string so Plotly treats it as a category
    df['mes_num'] = df['fecha'].dt.month
    
    # 3. Create the Spanish Month column using the map
    df['mes'] = df['mes_num'].map(month_map)
    
    # 4. Group and aggregate
    chart_data = df.groupby(['anual', 'mes_num', 'mes'])[target_column].sum().reset_index()
    
    # 3. Group the data to get the total money (Price) per month/year
    # We use sort=False to keep the month order if possible, or sort later
    #chart_data = df.groupby(['anual', 'mes', df['fecha'].dt.month])[target_column].sum().reset_index()
    chart_data = chart_data.sort_values('mes_num') # Ensures months are in order (Jan -> Dec)
    
      # Sidebar filter for years
    selected_years = st.multiselect(
        'Selecciona el valor',
        options=df['anual'].unique(),
        default=df['anual'].unique()
    )

    # Filter dataframe
    filtered_df = chart_data[chart_data['anual'].isin(selected_years)]
    
    # 4. Create the Plotly Chart
    fig = px.line(
        #chart_data, 
        filtered_df,
        x='mes', 
        y=target_column, 
        color='anual',
        title='Comportamientos de las ganacias anuales',
        markers=True,
        labels={target_column: 'Pesos($)', 'mes': 'mes'}
    )
    
    # 5. Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    

"""general functions that plots and prints specific functions if role is user it shows raw data or else a percentage"""
def show_data(role = 'user'):
    #shows charts at the width of the site
    st.set_page_config(layout="wide")
    
    #gets a tuple of dataframe and column = total
    df_to_show, column = prepare_data(role)
    
    st.write('Seleccionar para mostrar o esconder tabla:')
    #checkbox to hide or show data from drive
    if st.checkbox('Mostrar tabla:'):
        st.dataframe(df_to_show)
    
    #functions that shows the most and least sold products 
    ranking_product(df_to_show, column)
    
    #funtions about costumers or clients
    ranking_clients(df_to_show,column)
    customer_lifetime_value(df_to_show,column)
    client_retention_abandonment(df_to_show,column)
    
    #functions related to behavior of purchases in months or years
    monthly_growth_rate(df_to_show,column)
    compund_annual_growth_rate(df_to_show,column)
    years_revenue(df_to_show,column)
    






        
        

       

