from streamlit.testing.v1 import AppTest

def test_ranking_product_ui():

    # 1. Definimos la función envoltorio
    def app_para_probar():
        # Importamos TODO lo necesario DENTRO de la función
        import pandas as pd
        import streamlit as st
        from utils import ranking_product, display_styled_table, plot_chart_theme
        
        # Datos de prueba falsos
        df_falso = pd.DataFrame({
            'detalle': ['Tornillo', 'Tuerca', 'Lija', 'Rodillo'],
            'total': [1500, 50, 100, 500]
        })
            
        # 2. Ejecutamos la función helper 
        return ranking_product(df_falso, target_column='total', top_n=2)
    
    
    # 2. Cargamos la función en AppTest
    at = AppTest.from_function(app_para_probar)
    at.run()

    # 3. Validaciones
    assert not at.exception, f"La UI falló con el error: {at.exception}"
    
    assert len(at.metric) >= 2, "Deberían mostrarse al menos dos métricas en la interfaz"
    assert at.metric[0].label == 'Producto con mayor valor en ventas'
    assert at.metric[0].value == 'Tornillo'
    
    assert at.metric[1].label == 'Productos con menor valor en ventas'
    assert at.metric[1].value == 'Tuerca'

    assert "Ranking de los 2 productos mayormente vendidos" in at.subheader[0].value


