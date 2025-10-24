from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore
from multiprocessing import current_process, Array, Value
from time import sleep
import random

# -----------------------------
# PARÁMETROS (manteniendo forma)
# -----------------------------
K = 20              # nº de botellas a producir (múltiplo de 10 para cerrar bien)
MAX_STORAGE = 10    # capacidad máxima de la caja (10 botellas)
NPROD = 1           # nº de productores (1 embotellador)
N = K * NPROD       # nº total de botellas

def delay(factor = 3):
    sleep(random.random()/factor)

"""
    PRODUCTOR (Embotellador):
    - ADD_DATA -> AÑADE UNA BOTELLA A LA CAJA.
    - PRODUCE  -> GENERA BOTELLAS (K unidades).
"""
def add_data(storage, data, position, sem_capacity, sem_full, count):
    # esperar hueco en la caja
    sem_capacity.acquire()
    # colocar botella
    with count.get_lock():
        storage[position] = 1
        count.value += 1
        print(f"[{current_process().name}] coloca botella {count.value}/{MAX_STORAGE} en pos {position}")
        # si la caja está llena, avisar al empaquetador
        if count.value == MAX_STORAGE:
            print(">> Caja llena. Aviso al empaquetador.")
            sem_full.release()
    delay(4)

def produce(storage, sem_capacity, sem_full, count):
    position = 0   # índice donde insertar la siguiente botella
    for n in range(K):
        print(f"\n[{current_process().name}] produciendo")
        # 'data' no importa: solo marcamos la presencia de botella
        data = 1
        add_data(storage, data, position, sem_capacity, sem_full, count)
        print(f"[{current_process().name}]\t==>\t| botella : {n+1}\t| posicion : {position}")
        position = (position + 1) % MAX_STORAGE


"""
    CONSUMIDOR (Empaquetador):
    - CONSUME -> ESPERA A CAJA LLENA, SELLA, GUARDA Y REPONE LA CAJA VACÍA.
    Termina tras procesar todas las cajas completas: K / MAX_STORAGE.
"""
def consume(storage, sem_capacity, sem_full, count):
    cajas_a_procesar = K // MAX_STORAGE
    procesadas = 0
    while procesadas < cajas_a_procesar:
        # esperar a que la caja esté llena
        sem_full.acquire()

        print(f"\n[{current_process().name}] Caja llena recibida. Sellando y guardando...")
        delay(6)

        # vaciar caja y reponer huecos
        with count.get_lock():
            for i in range(MAX_STORAGE):
                storage[i] = 0
                sem_capacity.release()  # reponer huecos
            count.value = 0

        procesadas += 1
        print(f"[{current_process().name}] Caja repuesta (vacía). Cajas procesadas: {procesadas}/{cajas_a_procesar}\n")


"""
    MAIN:
    - CREA 1 PRODUCTOR (embotellador) Y 1 CONSUMIDOR (empaquetador).
    - MANTIENE LA ESTRUCTURA DE ARRANQUE Y JOIN.
"""
def main():
    # storage de la caja (0 = vacío, 1 = botella)
    storage = Array('i', MAX_STORAGE)
    for i in range(MAX_STORAGE):
        storage[i] = 0

    # Semáforos:
    sem_capacity = BoundedSemaphore(MAX_STORAGE)  # huecos libres (10 al inicio)
    sem_full    = Semaphore(0)                    # señal de "caja llena"
    count = Value('i', 0)                         # botellas actuales en la caja

    # 1 productor (embotellador)
    producer = Process(target=produce,
                       name='Prod   0',
                       args=(storage, sem_capacity, sem_full, count))

    # 1 consumidor (empaquetador)
    consumer = Process(target=consume,
                       name='Consumer',
                       args=(storage, sem_capacity, sem_full, count))

    # inicializar procesos
    for p in [producer, consumer]:
        p.start()
    for p in [producer, consumer]:
        p.join()

if __name__ == '__main__':
    main()
