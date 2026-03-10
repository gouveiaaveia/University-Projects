import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Nome do ficheiro com os dados
nome_ficheiro = "resultados6.txt"

# Leitura dos dados do ficheiro
with open(nome_ficheiro, "r") as f:
    linhas = f.readlines()

# Número de execuções
n_execucoes = int(linhas[0].strip())

# Tamanhos esperados das entradas
tamanhos_esperados = [1000000, 2000000, 3000000, 5000000, 6000000, 8000000, 9000000, 10000000, 12000000, 14000000]

# Dicionários para armazenar os tempos das medições
data1 = {}
data2 = {}

# Índice para percorrer as linhas do ficheiro
indice = 1

# Processamento das linhas do ficheiro
for execucao in range(n_execucoes):
    for tamanho in tamanhos_esperados:
        linha1 = list(map(float, linhas[indice].strip().split()))
        indice += 1
        linha2 = list(map(float, linhas[indice].strip().split()))
        indice += 1

        if int(linha1[0]) != tamanho or int(linha2[0]) != tamanho:
            print(f"Tamanho inesperado (esperado: {tamanho}, obtido: {linha1[0]} e {linha2[0]})")
            continue

        data1.setdefault(tamanho, []).append(linha1[1])
        data2.setdefault(tamanho, []).append(linha2[1])

# Organiza os dados por tamanho de entrada
tamanhos = sorted(data1.keys())
tamanhos_np = np.array(tamanhos).reshape(-1, 1)

# Cálculo das médias
tempos1_med = [np.mean(data1[t]) for t in tamanhos]
tempos2_med = [np.mean(data2[t]) for t in tamanhos]

# Regressão linear para Medição 1
modelo1 = LinearRegression()
modelo1.fit(tamanhos_np, tempos1_med)
y1_pred = modelo1.predict(tamanhos_np)
r2_1 = r2_score(tempos1_med, y1_pred)

# Regressão linear para Medição 2
modelo2 = LinearRegression()
modelo2.fit(tamanhos_np, tempos2_med)
y2_pred = modelo2.predict(tamanhos_np)
r2_2 = r2_score(tempos2_med, y2_pred)

# Plotagem dos gráficos
plt.figure(figsize=(14, 7))

# Gráfico para a primeira medição
plt.subplot(1, 2, 1)
plt.plot(tamanhos, tempos1_med, marker='o', color='blue', label='Média dos tempos')
plt.plot(tamanhos, y1_pred, color='red', linestyle='--', label=f'Regressão Linear (R² = {r2_1:.4f})')
plt.xlabel("Tamanho da entrada")
plt.ylabel("Tempo de execução (s)")
plt.title("Medição 1")
plt.legend()
plt.grid(True)

# Gráfico para a segunda medição
plt.subplot(1, 2, 2)
plt.plot(tamanhos, tempos2_med, marker='o', color='green', label='Média dos tempos')
plt.plot(tamanhos, y2_pred, color='red', linestyle='--', label=f'Regressão Linear (R² = {r2_2:.4f})')
plt.xlabel("Tamanho da entrada")
plt.ylabel("Tempo de execução (s)")
plt.title("Medição 2")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
