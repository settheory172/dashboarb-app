import pandas as pd
from streamlit.testing.v1 import AppTest

def test_ranking_product_ui(monkeypatch):
    # 1. Creamos un script temporal en memoria (o simulamos un archivo app.py)
    # Aquí simulamos cómo se llamaría a tu función dentro de una app de Streamlit real
        
    # 2. Guardamos este script temporalmente para que AppTest pueda leerlo
    with open("temp_app.py", "w", encoding="utf-8") as f:
        f.write(codigo_streamlit)
        
    try:
        # 3. Cargamos el archivo temporal con AppTest y lo ejecutamos
        at = AppTest.from_file("temp_app.py")
        at.run()
        
        # 4. Verificamos que la aplicación corrió SIN excepciones ni errores de código
        assert not at.exception, f"La app falló con el error: {at.exception}"
        
        # 5. Validamos que los componentes visuales clave se hayan renderizado correctamente
        # Verificamos que aparecieron las dos métricas (st.metric)
        assert len(at.metric) >= 2, "Deberían mostrarse al menos dos métricas de ranking"
        
        # Verificamos los valores de las métricas basados en nuestros datos falsos (Laptop = 2000 total)
        assert at.metric[0].label == 'Producto con mayor valor en ventas'
        assert at.metric[0].value == 'Laptop'
        
        # Verificamos que el gráfico de Plotly se renderizó
        assert len(at.plotly_chart) >= 1, "El gráfico de barras no se renderizó"
        
        # Verificamos el subheader
        assert "Ranking de los" in at.subheader[0].value
        
    finally:
        # 6. Limpiamos y borramos el archivo temporal al terminar la prueba
        import os
        if os.path.exists("temp_app.py"):
            os.remove("temp_app.py")
