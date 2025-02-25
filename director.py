# director.py

import importlib

def ejecutar_bloque(bloque_nombre):
    try:
        # Intentamos importar el bloque dinámicamente
        bloque = importlib.import_module(f"bloques.{bloque_nombre}")
        resultado = bloque.ejecutar()
        print(f"Resultado del bloque {bloque_nombre}: {resultado}")
    except Exception as e:
        print(f"Error al ejecutar el bloque {bloque_nombre}: {e}")

def main():
    print("Iniciando IAMO...")
    # Ejecutamos el bloque holamundo
    ejecutar_bloque("holamundo")

if __name__ == "__main__":
    main()
