# bloques/task_scheduler.py

import time

def ejecutar(*args, **kwargs):
    print("Task Scheduler está funcionando. Programando tareas...")
    time.sleep(2)
    print("Tarea programada completada.")
    return "Resultado desde el bloque task_scheduler"
