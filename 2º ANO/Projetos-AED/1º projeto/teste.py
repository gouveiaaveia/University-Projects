import matplotlib.pyplot as plt
import numpy as np

# Leitura e processamento dos dados
solucao2 = {}
solucao3 = {}

with open("resultados7.txt", "r") as arquivo:
    linhas = arquivo.readlines()
    n = int(linhas[0])
    dic = 1
    for i in range(1, len(linhas)):
        valores = linhas[i].split()
        if dic == 3:
            dic = 1
        if dic == 1:
            solucao2[valores[0]] = solucao2.get(valores[0], 0) + float(valores[1])
        elif dic == 2:
            solucao3[valores[0]] = solucao3.get(valores[0], 0) + float(valores[1])
        dic += 1

# Calcula a média para cada chave
for key in solucao2.keys():
    solucao2[key] /= n
    solucao3[key] /= n

# Obtém as chaves e os valores
keys_2 = list(solucao2.keys())
values_2 = list(solucao2.values())
keys_3 = list(solucao3.keys())
values_3 = list(solucao3.values())

# Converte as chaves para valores reais
actual_x_2 = np.array([float(k) for k in keys_2])
actual_x_3 = np.array([float(k) for k in keys_3])

# Função para calcular e plotar a reta de regressão
def plot_regression_line(actual_x, y, ax, label):
    coeffs = np.polyfit(actual_x, y, 1)
    poly = np.poly1d(coeffs)
    y_pred = poly(actual_x)
    ss_res = np.sum((np.array(y) - y_pred) ** 2)
    ss_tot = np.sum((np.array(y) - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    index_x = np.arange(len(actual_x))
    a = (index_x[-1] - index_x[0]) / (actual_x[-1] - actual_x[0])
    c = index_x[0] - a * actual_x[0]
    x_transformed = a * actual_x + c
    ax.plot(x_transformed, y_pred, '--', label=f'{label} (regressão linear, R² = {r2:.3f})')
    ax.legend()
    return r2

# --- Gráfico para Solução 2 ---
common_y_min = min(min(values_2), min(values_3))
common_y_max = max(max(values_2), max(values_3))
margin = (common_y_max - common_y_min) * 0.1
common_y_max += margin
num_yticks = 5
y_ticks_common = np.linspace(common_y_min, common_y_max, num_yticks)

fig2, ax2 = plt.subplots(figsize=(12, 6))
x_pos_2 = np.arange(len(keys_2))
ax2.plot(x_pos_2, values_2, 's-', label='Solução 2')
r2_2 = plot_regression_line(actual_x_2, values_2, ax2, 'Solução 2')
ax2.set_xticks(x_pos_2)
ax2.set_xticklabels(keys_2)
ax2.set_xlabel('Tamanho da Lista')
ax2.set_ylabel('Tempo (s)')
ax2.set_title('Solução 2')
ax2.set_ylim(common_y_min, common_y_max)
ax2.set_yticks(y_ticks_common)
ax2.set_yticklabels([f"{tick:.3f}" for tick in y_ticks_common])

# --- Gráfico para Solução 3 com escala ajustada ---
fig3, ax3 = plt.subplots(figsize=(12, 6))
x_pos_3 = np.arange(len(keys_3))
ax3.plot(x_pos_3, values_3, 'd-', label='Solução 3')
r2_3 = plot_regression_line(actual_x_3, values_3, ax3, 'Solução 3')
ax3.set_xticks(x_pos_3)
ax3.set_xticklabels(keys_3)
ax3.set_xlabel('Tamanho da Lista')
ax3.set_ylabel('Tempo (s)')
ax3.set_title('Solução 3')

# Calcula escala específica para Solução 3
sol3_y_min = min(values_3)
sol3_y_max = max(values_3)
margin3 = (sol3_y_max - sol3_y_min) * 0.1
sol3_y_max += margin3
num_yticks_sol3 = 5
y_ticks_sol3 = np.linspace(sol3_y_min, sol3_y_max, num_yticks_sol3)
ax3.set_ylim(sol3_y_min, sol3_y_max)
ax3.set_yticks(y_ticks_sol3)
ax3.set_yticklabels([f"{tick:.3f}" for tick in y_ticks_sol3])

plt.tight_layout()
plt.show()

print("R² para Solução 2:", r2_2)
print("R² para Solução 3:", r2_3)
