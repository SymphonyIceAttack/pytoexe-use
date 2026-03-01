import streamlit as st
import os
from pathlib import Path

# Configurar la página
st.set_page_config(page_title="ASEMA - Gestor de Cuotas", layout="wide")

# Mostrar información de depuración
st.write("### Información de depuración")
st.write(f"**Directorio actual de trabajo:** {os.getcwd()}")
st.write(f"**Archivos en el directorio actual:** {os.listdir('.')}")

# Verificar si existe la carpeta static
if os.path.exists("static"):
    st.write("✅ La carpeta 'static' SÍ existe")
    st.write(f"**Archivos en 'static':** {os.listdir('static')}")
    
    # Buscar cualquier archivo de imagen en la carpeta static
    archivos_static = os.listdir("static")
    imagenes = [f for f in archivos_static if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
    if imagenes:
        st.write(f"**Imágenes encontradas:** {imagenes}")
        
        # Mostrar la primera imagen encontrada
        from PIL import Image
        logo_path = os.path.join("static", imagenes[0])
        logo = Image.open(logo_path)
        
        st.image(logo, caption=f"Mostrando: {imagenes[0]}", width=200)
    else:
        st.warning("No se encontraron imágenes en la carpeta 'static'")
else:
    st.error("❌ La carpeta 'static' NO existe en el directorio actual")
    st.info("Por favor, crea la carpeta 'static' en: " + os.getcwd())

# El resto de tu aplicación
st.markdown("---")
st.title("Gestor de Cuotas - ASEMA")