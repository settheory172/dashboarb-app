from streamlit.testing.v1 import AppTest
import pandas as pd
import streamlit as st
import pytest

# Datos de prueba compartidos
df = pd.DataFrame([
        {
            "detalle": "machete de herragro",
            "total": 197400,
            "cliente": "ESPUMADOS S.A.",
            "fecha": "01/10/2023",
        },
        {
            "detalle": "flexometro de mts",
            "total": 830025,
            "cliente": "BOMBAS Y MONTAJES",
            "fecha": "01/12/2023",
        },
        {
            "detalle": "amarres plasticos x2",
            "total": 1420,
            "cliente": "FABRICA NACIONAL",
            "fecha": "01/02/2023",
        },
        {
            "detalle": "amarres plasticos x2",
            "total": 6775,
            "cliente": "ESPUMADOS S.A.",
            "fecha": "01/08/2023",
        },
        {
            "detalle": "amarre plastico de x30",
            "total": 345,
            "cliente": "ESPUMADOS S.A.",
            "fecha": "01/09/2023",
        },
    ])

def ranking_product(df, target_column='total', top_n=1):
  # 1. Aggregate revenue by product description
  revenue_ranking = df.groupby('detalle')[target_column].sum().reset_index()
  # 2. Get the Most Sold (Highest Revenue)
  top_earners = revenue_ranking.sort_values(by=target_column, ascending=False).head(top_n)
  # 3. Get the Least Sold (Lowest Revenue)
  bottom_earners = revenue_ranking.sort_values(by=target_column, ascending=True).head(top_n)
  return top_earners, bottom_earners

#print(ranking_product(df))
#print("*"*20)
#print(ranking_product(df)[0])
#print("*"*20)
#print(ranking_product(df)[1])

def test_ranking_product():
    top, bottom = ranking_product(df)
    # Assert that the highest revenue product is correct
    assert top.iloc[0]["detalle"] == "flexometro de mts"
    assert top.iloc[0]["total"] == 830025

    # Assert that the lowest revenue product is correct
    assert bottom.iloc[0]["detalle"] == "amarre plastico de x30"
    assert bottom.iloc[0]["total"] == 345

def ranking_clients(df,target_column = 'total', top_n = 1):
    #totalizes the purchases by clients
    total_purchased = df.groupby('cliente')[target_column].sum().reset_index()
    # 2. Sort by the target column in descending order and pick the first row
    top_client = total_purchased.sort_values(by=target_column, ascending=False).head(top_n)
    return top_client

#print(ranking_clients(df))

def test_ranking_client():
    top = ranking_clients(df)
    # Assert that the highest revenue product is correct
    assert top.iloc[0]["cliente"] == "BOMBAS Y MONTAJES"
    assert top.iloc[0]["total"] == 830025

   
def customer_lifetime_value (df, target_column='total'):
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
    return clv

#print(customer_lifetime_value(df,'total'))

def test_customer_lifetime_value():
    value = customer_lifetime_value(df)
    # Assert that the highest revenue product is correct
    expected = 19237.1
    assert (value == pytest.approx(expected)), f"Expected revenue to be {expected}, but got {value}"
    #assert value ==  pytest.approx(345321) 

def monthly_growth_rate(df, target_column='total'):
    # Ensure the date column is an actual datetime object
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
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
    return monthly_df #monthly_df['mes']

#x = monthly_growth_rate(df)
#print(x)
#print(x.iloc[0])
#print(x.iloc[0]['mes'])
 
def test_montly_growth_rate():
    values = monthly_growth_rate(df)
    # Assertions
    compare = values.iloc[0]['mes']
    expected_date = "2023-02"
    assert (compare == expected_date), f"Expected revenue to be {expected_date}, but got {compare}"
   

def compund_annual_growth_rate(df, target_column='total'):
    # --- 1. GROUP DATA BY YEAR ---
    # We need annual totals to calculate CAGR properly
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
    df['anual'] = df['fecha'].dt.year
    yearly_df = df.groupby('anual')[target_column].sum().reset_index()
     # --- 2. EXTRACT VARIABLES FOR THE FORMULA ---
    # Get the first and last years in the dataset
    first_year = yearly_df['anual'].iloc[0]
    last_year = yearly_df['anual'].iloc[-1]

    # Get the revenue for those specific years
    beginning_value = yearly_df[target_column].iloc[0]
    ending_value = yearly_df[target_column].iloc[-1]

    # Calculate 'n' (number of years)
    n = last_year - first_year
    #if n > 0:
    cagr = ((ending_value / beginning_value) ** (1 / n)) - 1
    cagr_percentage = cagr * 100
    return cagr_percentage
          

#x = compund_annual_growth_rate(df)
#print(x)

def test_compound_annual_growth_rate():
    value = compund_annual_growth_rate(df)
    assert value == 0

def years_revenue (df, target_column = 'total'):
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
    return chart_data

#y = years_revenue(df)
#print(y)
#print('*'*20)
#print(y.iloc[0])
#print('*'*20)
#print(y.iloc[0]['mes'])

def test_years_revenue():
    values = years_revenue(df)
    # Assertions
    compare = values.iloc[0]['mes']
    expected = "Febrero"
    assert (compare == expected), f"Expected revenue to be {expected}, but got {compare}"
    

def client_retention_abandonment(df, target_column='total'):
    # --- 1. DEFINE THE PARAMETERS ---
    # We use the most recent purchase in the whole dataset as our "Today" marker
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
    #analysis_min = df['fecha'].min()
    analysis_max = df['fecha'].max()
    
    client_stats = df.groupby(['cliente','fecha'])[target_column].sum().reset_index()
    #client_stats = client_stats.drop(columns=['cliente'])
    clientes = client_stats.groupby('cliente').agg(
        ultima_compra=('fecha', 'max'),
        Total_gastado =(target_column, 'sum'),
        Total_Ordenes=(target_column, 'count')).reset_index()

    # Calculate exactly how many days it has been since their last purchase
    clientes['Dias inactivo'] = (analysis_max - clientes['ultima_compra']).dt.days
        
    # Classify them as Retained or Abandoned based on the slider value
    clientes['Estatus'] = clientes['Dias inactivo'].apply(
        lambda x: 'Retenido' if x <= 90 else 'Abandono'
    )

    # --- 3. CALCULATE OVERALL RATES ---
    total_clients = len(clientes)
    retained_count = len(clientes[clientes['Estatus'] == 'Retenido'])
    abandoned_count = total_clients - retained_count

    retention_rate = (retained_count / total_clients) * 100
    abandon_rate = (abandoned_count / total_clients) * 100

    return clientes,retention_rate,abandon_rate
 

#y = client_retention_abandonment(df)
#print(y[0])
#print(y[1])
#print(y[2])

def test_client_retention_abandonment():
    values = client_retention_abandonment(df)
    # Assertions
    retention_rate = values[1]
    abandonment_rate = values[2]
    expected_retention_rate = 66.666666667
    expected_abandonment_rate = 33.3333333

    assert (retention_rate == pytest.approx(expected_retention_rate)), f"Expected revenue to be {expected_retention_rate}, but got {retention_rate}"
    assert (abandonment_rate == pytest.approx(expected_abandonment_rate)), f"Expected revenue to be {expected_abandonment_rate}, but got {abandonment_rate}"


def test_dashboard_table():
    #import streamlit as st

    # 2. Define a wrapper function that acts as your "Streamlit app script"
    def app_script():
        import streamlit as st
        import pandas as pd

        df = pd.DataFrame([
            {
                "detalle": "machete de herragro",
                "total": 197400,
                "cliente": "ESPUMADOS S.A.",
                "fecha": "01/10/2023",
            },
            {
                "detalle": "flexometro de mts",
                "total": 830025,
                "cliente": "BOMBAS Y MONTAJES",
                "fecha": "01/12/2023",
            },
            {
                "detalle": "amarres plasticos x2",
                "total": 1420,
                "cliente": "FABRICA NACIONAL",
                "fecha": "01/02/2023",
            },
        ])

        def display_styled_table(df, target_column = 'total', color_map="Greens"):
            """Applies background gradient and currency formatting to a specific column

            and displays it in Streamlit using the full container width.
            """
            styled_df = df.style.background_gradient(
                subset=[target_column], cmap=color_map
            ).format({target_column: "{:,.0f}"})

            return st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
        display_styled_table(df)
        
    # 1. Load the app script using AppTest
    at = AppTest.from_function(app_script)

    # 2. Run the app
    at.run()

    # 3. Assert that the app executed without any uncaught exceptions
    assert not at.exception, f"App raised an exception: {at.exception}"

    # 4. Verify that the dataframe element was rendered successfully
    assert len(at.dataframe) > 0, "No dataframe element found in the app."

    # Optional: Check properties of the rendered dataframe element if needed
    # e.g., checking the shape or values via the underlying element
    rendered_df = at.dataframe[0].value
    assert "total" in rendered_df.columns


def test_plot_chart_theme():
    #import streamlit as st
    #import plotly.express as px

    # 2. Define a wrapper function that acts as your "Streamlit app script"
    def app_script():
        import streamlit as st
        import plotly.express as px
        import pandas as pd

        df = pd.DataFrame([
            {
                "detalle": "machete de herragro",
                "total": 197400,
                "cliente": "ESPUMADOS S.A.",
                "fecha": "01/10/2023",
            },
            {
                "detalle": "flexometro de mts",
                "total": 830025,
                "cliente": "BOMBAS Y MONTAJES",
                "fecha": "01/12/2023",
            },
            {
                "detalle": "amarres plasticos x2",
                "total": 1420,
                "cliente": "FABRICA NACIONAL",
                "fecha": "01/02/2023",
            },
        ])

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
        
        
     # 2. Create the horizontal bar chart
        fig = px.bar(
            df, 
            x='total', 
            y='detalle', 
            orientation='h',
            #title=f'Top {top_n} Productos por Venta',
            #labels={target_column: 'Ventas Totales ($)', 'detalle': 'Producto'},
            color_discrete_sequence=['#2ecc71'] # Your green color
        )
        fig = (plot_chart_theme(fig)) 
        #plot_chart_theme(df)
        # CRITICAL: Render the chart so AppTest can detect it
        st.plotly_chart(fig, use_container_width=True)

    
    at = AppTest.from_function(app_script)
    at.run()
    
    # 1. Check that the app executed without throwing any exceptions
    assert not at.exception, f"App crashed with exceptions: {at.exception}"
    # Verify that a plotly chart element was successfully rendered
    # Use at.get() to check for the plotly chart element
    charts = at.get("plotly_chart")
    assert len(charts) == 1, "Expected exactly 1 plotly chart to be rendered"
