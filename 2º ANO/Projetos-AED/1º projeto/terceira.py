import random
import time

lista_valores = []

for i in range(10000000):
    lista_valores.append(i)

posicao_remover = random.randint(0, 999999)
shuffled = random.sample(lista_valores, len(lista_valores))

print("Posição a ser removida: ", shuffled[posicao_remover])

shuffled.pop(posicao_remover)

comeco = time.time()

soma_espectavel = (max(shuffled) * (max(shuffled) + 1)) / 2 - (min(shuffled) * (min(shuffled) - 1)) / 2

segunda_soma = sum(shuffled)

print("Valor encontrado: ", soma_espectavel - segunda_soma)
print("--- %s seconds ---" % (time.time() - comeco))
