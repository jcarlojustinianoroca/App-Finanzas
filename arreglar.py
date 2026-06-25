import os
import sys

# Crear el virtual environment
print("Creando entorno virtual 'venv'...")
os.system("python -m venv venv")

# Instalar Flask usando pip del venv
print("Instalando Flask...")
if sys.platform == "win32":
    # En Windows
    os.system("venv\\Scripts\\pip install flask")
else:
    # En Linux/Mac
    os.system(". venv/bin/activate && pip install flask")

print("✓ Entorno virtual creado e instalado correctamente!")