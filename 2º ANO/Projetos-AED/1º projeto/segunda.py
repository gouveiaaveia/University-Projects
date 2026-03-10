import random
import time



def encontrar():
    for i in range(len(shuffled)-1):
        if shuffled[i+1] - shuffled[i] != 1:
            print("Valor encontrado: ", i+1)
            print("--- %s seconds ---" % (time.time() - comeco))
            return
        elif i == len(shuffled)-2:
            print("Nenhum valor em falta!!")

lista_valores = []

for i in range(10000000):
    lista_valores.append(i)

posicao_remover = random.randint(0, 999999)
shuffled = random.sample(lista_valores, len(lista_valores))

print("Posição a ser removida: ", shuffled[posicao_remover])
shuffled.pop(posicao_remover)


comeco = time.time()
shuffled.sort()
encontrar()

