# CreaBloques.py

import os

def crear_bloque(nombre):
    path = f"bloques/{nombre}.py"
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(f"# {nombre} - Bloque creado automáticamente\n")
            f.write("def ejecutar(*args, **kwargs):\n")
            f.write(f"    print('{nombre} está funcionando')\n")
            f.write("    return 'Resultado desde el bloque {nombre}'\n")
        print(f"Bloque {nombre} creado exitosamente.")
    else:
        print(f"El bloque {nombre} ya existe.")

# Crear bloques de ejemplo
crear_bloque("nuevo_bloque")
