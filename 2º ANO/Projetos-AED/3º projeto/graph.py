import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

data_string = """
--- Iteration 1 ---
Size: 10000
Insertion Sort A: 0.000019 s
Insertion Sort B: 0.116061 s
Insertion Sort C: 0.054534 s

Heap Sort A: 0.001108 s
Heap Sort B: 0.000850 s
Heap Sort C: 0.001288 s

Quick Sort A: 0.000096 s
Quick Sort B: 0.000078 s
Quick Sort C: 0.000688 s


Size: 20000
Insertion Sort A: 0.000029 s
Insertion Sort B: 0.498378 s
Insertion Sort C: 0.326104 s

Heap Sort A: 0.002181 s
Heap Sort B: 0.003802 s
Heap Sort C: 0.003808 s

Quick Sort A: 0.000221 s
Quick Sort B: 0.000181 s
Quick Sort C: 0.002029 s


Size: 30000
Insertion Sort A: 0.000048 s
Insertion Sort B: 1.061780 s
Insertion Sort C: 0.458556 s

Heap Sort A: 0.003469 s
Heap Sort B: 0.005519 s
Heap Sort C: 0.004428 s

Quick Sort A: 0.000545 s
Quick Sort B: 0.000304 s
Quick Sort C: 0.002162 s


Size: 50000
Insertion Sort A: 0.000292 s
Insertion Sort B: 3.090619 s
Insertion Sort C: 1.731674 s

Heap Sort A: 0.007298 s
Heap Sort B: 0.008627 s
Heap Sort C: 0.014354 s

Quick Sort A: 0.000409 s
Quick Sort B: 0.000473 s
Quick Sort C: 0.004594 s


Size: 60000
Insertion Sort A: 0.000122 s
Insertion Sort B: 5.047158 s
Insertion Sort C: 2.209682 s

Heap Sort A: 0.007394 s
Heap Sort B: 0.008613 s
Heap Sort C: 0.008789 s

Quick Sort A: 0.000789 s
Quick Sort B: 0.000459 s
Quick Sort C: 0.006458 s


Size: 70000
Insertion Sort A: 0.000176 s
Insertion Sort B: 5.974164 s
Insertion Sort C: 3.065949 s

Heap Sort A: 0.012065 s
Heap Sort B: 0.014699 s
Heap Sort C: 0.013664 s

Quick Sort A: 0.000701 s
Quick Sort B: 0.000759 s
Quick Sort C: 0.006084 s


Size: 80000
Insertion Sort A: 0.000107 s
Insertion Sort B: 7.689942 s
Insertion Sort C: 3.924851 s

Heap Sort A: 0.012658 s
Heap Sort B: 0.012110 s
Heap Sort C: 0.019885 s

Quick Sort A: 0.000690 s
Quick Sort B: 0.002165 s
Quick Sort C: 0.008930 s


Size: 100000
Insertion Sort A: 0.000114 s
Insertion Sort B: 11.169450 s
Insertion Sort C: 4.927351 s

Heap Sort A: 0.013382 s
Heap Sort B: 0.012593 s
Heap Sort C: 0.017596 s

Quick Sort A: 0.000839 s
Quick Sort B: 0.001366 s
Quick Sort C: 0.009432 s


Size: 200000
Insertion Sort A: 0.000251 s
Insertion Sort B: 42.816997 s
Insertion Sort C: 21.747838 s

Heap Sort A: 0.029582 s
Heap Sort B: 0.027948 s
Heap Sort C: 0.037697 s

Quick Sort A: 0.002113 s
Quick Sort B: 0.001908 s
Quick Sort C: 0.020992 s


Size: 300000
Insertion Sort A: 0.000398 s
Insertion Sort B: 92.517451 s
Insertion Sort C: 47.657038 s

Heap Sort A: 0.043053 s
Heap Sort B: 0.041736 s
Heap Sort C: 0.062875 s

Quick Sort A: 0.003018 s
Quick Sort B: 0.003484 s
Quick Sort C: 0.030840 s


Size: 350000
Heap Sort A: 0.047218 s
Heap Sort B: 0.050091 s
Heap Sort C: 0.069139 s

Quick Sort A: 0.003465 s
Quick Sort B: 0.003983 s
Quick Sort C: 0.040711 s


Size: 500000
Heap Sort A: 0.077188 s
Heap Sort B: 0.071177 s
Heap Sort C: 0.111895 s

Quick Sort A: 0.005187 s
Quick Sort B: 0.005505 s
Quick Sort C: 0.054567 s


Size: 1000000
Heap Sort A: 0.159177 s
Heap Sort B: 0.148015 s
Heap Sort C: 0.251526 s

Quick Sort A: 0.010969 s
Quick Sort B: 0.013247 s
Quick Sort C: 0.118367 s


--- Iteration 2 ---
Size: 10000
Insertion Sort A: 0.000012 s
Insertion Sort B: 0.104117 s
Insertion Sort C: 0.053665 s

Heap Sort A: 0.001029 s
Heap Sort B: 0.000998 s
Heap Sort C: 0.001278 s

Quick Sort A: 0.000076 s
Quick Sort B: 0.000086 s
Quick Sort C: 0.000756 s


Size: 20000
Insertion Sort A: 0.000023 s
Insertion Sort B: 0.465058 s
Insertion Sort C: 0.226536 s

Heap Sort A: 0.002167 s
Heap Sort B: 0.002163 s
Heap Sort C: 0.002804 s

Quick Sort A: 0.000145 s
Quick Sort B: 0.000222 s
Quick Sort C: 0.001661 s


Size: 30000
Insertion Sort A: 0.000035 s
Insertion Sort B: 1.047810 s
Insertion Sort C: 0.490956 s

Heap Sort A: 0.003441 s
Heap Sort B: 0.003437 s
Heap Sort C: 0.004209 s

Quick Sort A: 0.000258 s
Quick Sort B: 0.000251 s
Quick Sort C: 0.002757 s


Size: 50000
Insertion Sort A: 0.000059 s
Insertion Sort B: 3.464972 s
Insertion Sort C: 1.420026 s

Heap Sort A: 0.005948 s
Heap Sort B: 0.005697 s
Heap Sort C: 0.009247 s

Quick Sort A: 0.000466 s
Quick Sort B: 0.000526 s
Quick Sort C: 0.005948 s


Size: 60000
Insertion Sort A: 0.000090 s
Insertion Sort B: 3.955186 s
Insertion Sort C: 1.999808 s

Heap Sort A: 0.008865 s
Heap Sort B: 0.007280 s
Heap Sort C: 0.009210 s

Quick Sort A: 0.000448 s
Quick Sort B: 0.000675 s
Quick Sort C: 0.007489 s


Size: 70000
Insertion Sort A: 0.000089 s
Insertion Sort B: 5.444809 s
Insertion Sort C: 2.687364 s

Heap Sort A: 0.011626 s
Heap Sort B: 0.008713 s
Heap Sort C: 0.010929 s

Quick Sort A: 0.000636 s
Quick Sort B: 0.000682 s
Quick Sort C: 0.006020 s


Size: 80000
Insertion Sort A: 0.000182 s
Insertion Sort B: 6.953370 s
Insertion Sort C: 3.626176 s

Heap Sort A: 0.010709 s
Heap Sort B: 0.013131 s
Heap Sort C: 0.016633 s

Quick Sort A: 0.000900 s
Quick Sort B: 0.000712 s
Quick Sort C: 0.010054 s


Size: 100000
Insertion Sort A: 0.000247 s
Insertion Sort B: 11.140966 s
Insertion Sort C: 5.522248 s

Heap Sort A: 0.013919 s
Heap Sort B: 0.012484 s
Heap Sort C: 0.019296 s

Quick Sort A: 0.001031 s
Quick Sort B: 0.001174 s
Quick Sort C: 0.009040 s


Size: 200000
Insertion Sort A: 0.000230 s
Insertion Sort B: 40.647328 s
Insertion Sort C: 18.628380 s

Heap Sort A: 0.026821 s
Heap Sort B: 0.025328 s
Heap Sort C: 0.034941 s

Quick Sort A: 0.001731 s
Quick Sort B: 0.001889 s
Quick Sort C: 0.020644 s


Size: 300000
Insertion Sort A: 0.000348 s
Insertion Sort B: 96.487651 s
Insertion Sort C: 51.167136 s

Heap Sort A: 0.046104 s
Heap Sort B: 0.047332 s
Heap Sort C: 0.063913 s

Quick Sort A: 0.003506 s
Quick Sort B: 0.003103 s
Quick Sort C: 0.032385 s


Size: 350000
Heap Sort A: 0.052960 s
Heap Sort B: 0.048089 s
Heap Sort C: 0.070351 s

Quick Sort A: 0.003200 s
Quick Sort B: 0.004270 s
Quick Sort C: 0.039562 s


Size: 500000
Heap Sort A: 0.080960 s
Heap Sort B: 0.070236 s
Heap Sort C: 0.101285 s

Quick Sort A: 0.005989 s
Quick Sort B: 0.005051 s
Quick Sort C: 0.065763 s


Size: 1000000
Heap Sort A: 0.170541 s
Heap Sort B: 0.156208 s
Heap Sort C: 0.238029 s

Quick Sort A: 0.010788 s
Quick Sort B: 0.016406 s
Quick Sort C: 0.109346 s


--- Iteration 3 ---
Size: 10000
Insertion Sort A: 0.000012 s
Insertion Sort B: 0.107535 s
Insertion Sort C: 0.052324 s

Heap Sort A: 0.001030 s
Heap Sort B: 0.000943 s
Heap Sort C: 0.001619 s

Quick Sort A: 0.000099 s
Quick Sort B: 0.000105 s
Quick Sort C: 0.000797 s


Size: 20000
Insertion Sort A: 0.000022 s
Insertion Sort B: 0.445108 s
Insertion Sort C: 0.216150 s

Heap Sort A: 0.001995 s
Heap Sort B: 0.002138 s
Heap Sort C: 0.002933 s

Quick Sort A: 0.000188 s
Quick Sort B: 0.000162 s
Quick Sort C: 0.001421 s


Size: 30000
Insertion Sort A: 0.000035 s
Insertion Sort B: 0.975890 s
Insertion Sort C: 0.467357 s

Heap Sort A: 0.003301 s
Heap Sort B: 0.003349 s
Heap Sort C: 0.004229 s

Quick Sort A: 0.000255 s
Quick Sort B: 0.000241 s
Quick Sort C: 0.002401 s


Size: 50000
Insertion Sort A: 0.000119 s
Insertion Sort B: 2.872348 s
Insertion Sort C: 1.454140 s

Heap Sort A: 0.006079 s
Heap Sort B: 0.009470 s
Heap Sort C: 0.008086 s

Quick Sort A: 0.000395 s
Quick Sort B: 0.000489 s
Quick Sort C: 0.004074 s


Size: 60000
Insertion Sort A: 0.000082 s
Insertion Sort B: 4.363542 s
Insertion Sort C: 2.050985 s

Heap Sort A: 0.010203 s
Heap Sort B: 0.006743 s
Heap Sort C: 0.009400 s

Quick Sort A: 0.000479 s
Quick Sort B: 0.000656 s
Quick Sort C: 0.005653 s


Size: 70000
Insertion Sort A: 0.000084 s
Insertion Sort B: 5.701237 s
Insertion Sort C: 2.870921 s

Heap Sort A: 0.008479 s
Heap Sort B: 0.009215 s
Heap Sort C: 0.012025 s

Quick Sort A: 0.000651 s
Quick Sort B: 0.000737 s
Quick Sort C: 0.006488 s


Size: 80000
Insertion Sort A: 0.000149 s
Insertion Sort B: 7.612300 s
Insertion Sort C: 3.708684 s

Heap Sort A: 0.012483 s
Heap Sort B: 0.012301 s
Heap Sort C: 0.014026 s

Quick Sort A: 0.000766 s
Quick Sort B: 0.000812 s
Quick Sort C: 0.008534 s


Size: 100000
Insertion Sort A: 0.000112 s
Insertion Sort B: 11.049729 s
Insertion Sort C: 5.434222 s

Heap Sort A: 0.016204 s
Heap Sort B: 0.015187 s
Heap Sort C: 0.019337 s

Quick Sort A: 0.001039 s
Quick Sort B: 0.000909 s
Quick Sort C: 0.010616 s


Size: 200000
Insertion Sort A: 0.000257 s
Insertion Sort B: 43.649847 s
Insertion Sort C: 18.953979 s

Heap Sort A: 0.028602 s
Heap Sort B: 0.026550 s
Heap Sort C: 0.032074 s

Quick Sort A: 0.001806 s
Quick Sort B: 0.001716 s
Quick Sort C: 0.017624 s


Size: 300000
Insertion Sort A: 0.000363 s
Insertion Sort B: 88.636734 s
Insertion Sort C: 42.435605 s

Heap Sort A: 0.039274 s
Heap Sort B: 0.037236 s
Heap Sort C: 0.050951 s

Quick Sort A: 0.003355 s
Quick Sort B: 0.003476 s
Quick Sort C: 0.028061 s


Size: 350000
Heap Sort A: 0.044300 s
Heap Sort B: 0.044615 s
Heap Sort C: 0.063457 s

Quick Sort A: 0.003306 s
Quick Sort B: 0.003909 s
Quick Sort C: 0.035440 s


Size: 500000
Heap Sort A: 0.069110 s
Heap Sort B: 0.063105 s
Heap Sort C: 0.088982 s

Quick Sort A: 0.004313 s
Quick Sort B: 0.005227 s
Quick Sort C: 0.047994 s


Size: 1000000
Heap Sort A: 0.143056 s
Heap Sort B: 0.142176 s
Heap Sort C: 0.194181 s

Quick Sort A: 0.009961 s
Quick Sort B: 0.010957 s
Quick Sort C: 0.102189 s

Size: 20000
Insertion Sort A: 0.000052
Insertion Sort B: 0.387042
Insertion Sort C: 0.188101


Heap Sort A: 0.001995
Heap Sort B: 0.001984
Heap Sort C: 0.002536


Quick Sort A: 0.000635
Quick Sort B: 0.000377
Quick Sort C: 0.002225


Size: 30000
Insertion Sort A: 0.000034
Insertion Sort B: 0.834834
Insertion Sort C: 0.415286


Heap Sort A: 0.003150
Heap Sort B: 0.006153
Heap Sort C: 0.004583


Quick Sort A: 0.000501
Quick Sort B: 0.000466
Quick Sort C: 0.002912


Size: 50000
Insertion Sort A: 0.000062
Insertion Sort B: 2.331330
Insertion Sort C: 1.165486


Heap Sort A: 0.005263
Heap Sort B: 0.006977
Heap Sort C: 0.009787


Quick Sort A: 0.000902
Quick Sort B: 0.000847
Quick Sort C: 0.004788


Size: 60000
Insertion Sort A: 0.000081
Insertion Sort B: 3.308269
Insertion Sort C: 1.823984


Heap Sort A: 0.008549
Heap Sort B: 0.007388
Heap Sort C: 0.010364


Quick Sort A: 0.001166
Quick Sort B: 0.001462
Quick Sort C: 0.005949


Size: 70000
Insertion Sort A: 0.000090
Insertion Sort B: 4.708941
Insertion Sort C: 2.274271


Heap Sort A: 0.007550
Heap Sort B: 0.009782
Heap Sort C: 0.010726


Quick Sort A: 0.001077
Quick Sort B: 0.001422
Quick Sort C: 0.006998


Size: 80000
Insertion Sort A: 0.000096
Insertion Sort B: 5.915281
Insertion Sort C: 2.975742


Heap Sort A: 0.009900
Heap Sort B: 0.010763
Heap Sort C: 0.011718


Quick Sort A: 0.001331
Quick Sort B: 0.003099
Quick Sort C: 0.009547


Size: 100000
Insertion Sort A: 0.000123
Insertion Sort B: 9.193215
Insertion Sort C: 4.594896


Heap Sort A: 0.013557
Heap Sort B: 0.010889
Heap Sort C: 0.016662


Quick Sort A: 0.001550
Quick Sort B: 0.002001
Quick Sort C: 0.010883


Size: 250000
Insertion Sort A: 0.000259
Insertion Sort B: 60.640259
Insertion Sort C: 29.773556


Heap Sort A: 0.032316
Heap Sort B: 0.030963
Heap Sort C: 0.042092


Quick Sort A: 0.003918
Quick Sort B: 0.004198
Quick Sort C: 0.028441


Size: 500000
Insertion Sort A: 0.000549
Insertion Sort B: 236.306385
Insertion Sort C: 116.052308


Heap Sort A: 0.062961
Heap Sort B: 0.067759
Heap Sort C: 0.092738


Quick Sort A: 0.007807
Quick Sort B: 0.009218
Quick Sort C: 0.060155


Size: 1000000
Insertion Sort A: 0.001150
Insertion Sort B: 956.207584
Insertion Sort C: 479.080957


Heap Sort A: 0.138808
Heap Sort B: 0.140077
Heap Sort C: 0.192442


Quick Sort A: 0.016541
Quick Sort B: 0.020108
Quick Sort C: 0.116820
"""

# --- Enhanced Parsing Logic ---
# Pre-process the data string to insert "--- Iteration 4 ---" header
# The new block starts after the Iteration 3 data.
# Iteration 3's last data line is "Quick Sort C: 0.102189 s" for Size 1000000.
# The line after that (potentially after some blank lines) starting with "Size: 20000"
# is the beginning of the implicit Iteration 4.

modified_data_string = data_string
iter3_header_str = "--- Iteration 3 ---"
idx_iter3_header = modified_data_string.find(iter3_header_str)

if idx_iter3_header != -1:
    # Search for the specific context of Iteration 3's end
    # Last size in Iter 3 is 1000000, last entry is Quick Sort C
    iter3_size_1M_block_start_str = "\nSize: 1000000" # Preceded by a newline
    idx_iter3_size_1M_block_start = modified_data_string.find(iter3_size_1M_block_start_str, idx_iter3_header)

    if idx_iter3_size_1M_block_start != -1:
        iter3_last_data_line_str = "Quick Sort C: 0.102189 s"
        idx_iter3_last_data_line = modified_data_string.find(iter3_last_data_line_str, idx_iter3_size_1M_block_start)

        if idx_iter3_last_data_line != -1:
            # Point after this line
            point_after_iter3_data = idx_iter3_last_data_line + len(iter3_last_data_line_str)
            
            # Find the start of the next "Size:" block, which should be "Size: 20000"
            # for the implicit Iteration 4
            next_size_block_str = "\nSize: 20000" # Searching for it on a new line
            idx_start_of_iter4_data = modified_data_string.find(next_size_block_str, point_after_iter3_data)

            if idx_start_of_iter4_data != -1:
                # Ensure content between is only whitespace
                inter_content = modified_data_string[point_after_iter3_data:idx_start_of_iter4_data]
                if inter_content.strip() == "":
                    # Insert the Iteration 4 header
                    iter4_header_to_insert = "\n--- Iteration 4 ---\n"
                    # The idx_start_of_iter4_data is where "\nSize: 20000" starts.
                    # We want to insert header *before* "Size: 20000", but after the newline.
                    # So, insert at idx_start_of_iter4_data + 1 (to be after the existing newline)
                    
                    insertion_point = idx_start_of_iter4_data + 1 # After the newline, before "Size: 20000"
                    
                    modified_data_string = (modified_data_string[:insertion_point] +
                                            "--- Iteration 4 ---\n" + # Added \n for clarity
                                            modified_data_string[insertion_point:])
                else:
                    print("Warning: Non-whitespace content found between assumed Iteration 3 end and Iteration 4 start. Header not inserted.")
            else:
                print("Warning: Could not find the start of implicit Iteration 4 data ('Size: 20000'). Header not inserted.")
        else:
            print("Warning: Could not find the last data line of Iteration 3. Header not inserted.")
    else:
        print("Warning: Could not find Size 1000000 block in Iteration 3. Header not inserted.")
else:
    print("Warning: '--- Iteration 3 ---' header not found. Cannot insert Iteration 4 header.")


# --- Standard Parsing Logic (now with Iteration 4 header potentially inserted) ---
parsed_data = []
current_iteration = 0
current_size = 0
# Regex that tolerates missing 's' and surrounding whitespace
algo_regex = re.compile(r'(.+ Sort) ([A-C]): ([\d.]+)\s*s?')

for line in modified_data_string.strip().split('\n'):
    line = line.strip()
    if not line:
        continue

    iteration_match = re.match(r'--- Iteration (\d+) ---', line)
    if iteration_match:
        current_iteration = int(iteration_match.group(1))
        # print(f"Switched to Iteration {current_iteration}") # Debug
        continue

    size_match = re.match(r'Size: (\d+)', line)
    if size_match:
        current_size = int(size_match.group(1))
        # print(f"Processing Size: {current_size} for Iteration {current_iteration}") # Debug
        if current_iteration == 0: # Safety check if a Size line appears before any Iteration header
            print(f"Warning: Size {current_size} found before any Iteration header. Assigning to Iteration 0 or previous.")
        continue
    
    if current_iteration == 0 and current_size == 0: # Skip lines before first "Size:" or "Iteration:" if they don't match algo
        # This might happen if there are intro lines not matching the pattern.
        # For this specific data, it should be fine.
        # print(f"Skipping line before initial setup: {line}") # Debug
        continue


    algo_match_res = algo_regex.match(line)
    if algo_match_res:
        algorithm = algo_match_res.group(1)
        variant = algo_match_res.group(2)
        time_str = algo_match_res.group(3)
        try:
            time = float(time_str)
            if current_iteration == 0: # If data appears before "--- Iteration 1 ---"
                 print(f"Warning: Data '{line}' found with no active iteration. Skipping.")
                 continue
            if current_size == 0: # If algo data appears before "Size:" under an iteration
                 print(f"Warning: Data '{line}' found with no active size for Iteration {current_iteration}. Skipping.")
                 continue

            parsed_data.append({
                'Iteration': current_iteration,
                'Size': current_size,
                'Algorithm': algorithm,
                'Variant': variant,
                'Time': time
            })
        except ValueError:
            print(f"Warning: Could not parse time '{time_str}' for Iteration {current_iteration}, Size {current_size}, Algo {algorithm} {variant} from line '{line}'")
    # else:
        # print(f"Debug: Line not matched by algo_regex: '{line}' for Iter: {current_iteration}, Size: {current_size}")


df = pd.DataFrame(parsed_data)

if df.empty:
    print("DataFrame is empty after parsing. Cannot generate plots.")
else:
    # Calculate average times
    df_avg = df.groupby(['Size', 'Algorithm', 'Variant'])['Time'].mean().reset_index()
    df_avg['AlgorithmVariant'] = df_avg['Algorithm'] + " " + df_avg['Variant']

    # Set plot style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (12, 7)

    # --- Plot 1: Insertion Sort Variants ---
    plt.figure()
    insertion_data = df_avg[df_avg['Algorithm'] == 'Insertion Sort']
    if not insertion_data.empty:
        sns.lineplot(data=insertion_data, x='Size', y='Time', hue='Variant', marker='o')
        plt.title('Desempenho do Insertion Sort (Médias)')
        plt.xlabel('Tamanho da Entrada (Size)')
        
        # Use log scale if max time is very large (due to Iteration 4 data)
        if insertion_data['Time'].max() > 50: # Adjusted threshold
            plt.yscale('log')
            plt.ylabel('Tempo Médio de Execução (s) - Escala Logarítmica')
        else:
            plt.ylabel('Tempo Médio de Execução (s)')
            
        plt.legend(title='Variante')
        plt.tight_layout()
        plt.savefig('insertion_sort_performance_v2.png')
        plt.close()
        print("Gráfico 'insertion_sort_performance_v2.png' gerado.")
    else:
        print("Não há dados para o Insertion Sort.")

    # --- Plot 2: Heap Sort Variants ---
    plt.figure()
    heap_data = df_avg[df_avg['Algorithm'] == 'Heap Sort']
    if not heap_data.empty:
        sns.lineplot(data=heap_data, x='Size', y='Time', hue='Variant', marker='o')
        plt.title('Desempenho do Heap Sort (Médias)')
        plt.xlabel('Tamanho da Entrada (Size)')
        plt.ylabel('Tempo Médio de Execução (s)')
        plt.legend(title='Variante')
        plt.tight_layout()
        plt.savefig('heap_sort_performance_v2.png')
        plt.close()
        print("Gráfico 'heap_sort_performance_v2.png' gerado.")
    else:
        print("Não há dados para o Heap Sort.")

    # --- Plot 3: Quick Sort Variants ---
    plt.figure()
    quick_data = df_avg[df_avg['Algorithm'] == 'Quick Sort']
    if not quick_data.empty:
        sns.lineplot(data=quick_data, x='Size', y='Time', hue='Variant', marker='o')
        plt.title('Desempenho do Quick Sort (Médias)')
        plt.xlabel('Tamanho da Entrada (Size)')
        plt.ylabel('Tempo Médio de Execução (s)')
        plt.legend(title='Variante')
        plt.tight_layout()
        plt.savefig('quick_sort_performance_v2.png')
        plt.close()
        print("Gráfico 'quick_sort_performance_v2.png' gerado.")
    else:
        print("Não há dados para o Quick Sort.")

    # --- Plot 4: Comparison of 'A' Variants ---
    plt.figure()
    variant_a_data = df_avg[df_avg['Variant'] == 'A']
    if not variant_a_data.empty:
        sns.lineplot(data=variant_a_data, x='Size', y='Time', hue='Algorithm', marker='o')
        plt.title('Comparação das Variantes "A" (Médias)')
        plt.xlabel('Tamanho da Entrada (Size)')
        plt.ylabel('Tempo Médio de Execução (s) - Escala Logarítmica')
        plt.yscale('log') 
        plt.legend(title='Algoritmo')
        plt.tight_layout()
        plt.savefig('variant_a_comparison_v2.png')
        plt.close()
        print("Gráfico 'variant_a_comparison_v2.png' gerado.")
    else:
        print("Não há dados para as variantes 'A'.")

    # --- Plot 5: Comparison of 'B' Variants ---
    plt.figure()
    variant_b_data = df_avg[df_avg['Variant'] == 'B']
    if not variant_b_data.empty:
        insertion_b = variant_b_data[variant_b_data['Algorithm'] == 'Insertion Sort']
        other_b = variant_b_data[variant_b_data['Algorithm'] != 'Insertion Sort']
        fig, ax1 = plt.subplots()
        color = 'tab:red'
        ax1.set_xlabel('Tamanho da Entrada (Size)')
        ax1.set_ylabel('Tempo Médio (s) - Heap B, Quick B', color=color)
        if not other_b.empty:
            sns.lineplot(data=other_b, x='Size', y='Time', hue='Algorithm', marker='o', ax=ax1, palette=[p for p in sns.color_palette() if p != sns.color_palette()[2]]) # Avoid color clash if possible
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.legend(loc='upper left')
        if not insertion_b.empty:
            ax2 = ax1.twinx()
            color = sns.color_palette()[2] # Explicitly choose a different color
            ax2.set_ylabel('Tempo Médio (s) - Insertion B (Escala Log)', color=color)
            sns.lineplot(data=insertion_b, x='Size', y='Time', linestyle='--', color=color, marker='x', ax=ax2, label="Insertion Sort B") # Simplified label
            ax2.tick_params(axis='y', labelcolor=color)
            if insertion_b['Time'].max() > 50: # Use log if IS B is very slow
                 ax2.set_yscale('log')
            # Combine legends
            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='center right')
            if ax1.get_legend() is not None: ax1.get_legend().remove() # Remove ax1's legend if ax2 combined it

        plt.title('Comparação das Variantes "B" (Médias)')
        plt.tight_layout()
        plt.savefig('variant_b_comparison_v2.png')
        plt.close()
        print("Gráfico 'variant_b_comparison_v2.png' gerado.")
    else:
        print("Não há dados para as variantes 'B'.")

    # --- Plot 6: Comparison of 'C' Variants ---
    plt.figure()
    variant_c_data = df_avg[df_avg['Variant'] == 'C']
    if not variant_c_data.empty:
        insertion_c = variant_c_data[variant_c_data['Algorithm'] == 'Insertion Sort']
        other_c = variant_c_data[variant_c_data['Algorithm'] != 'Insertion Sort']
        fig, ax1 = plt.subplots()
        color = 'tab:red'
        ax1.set_xlabel('Tamanho da Entrada (Size)')
        ax1.set_ylabel('Tempo Médio (s) - Heap C, Quick C', color=color)
        if not other_c.empty:
            sns.lineplot(data=other_c, x='Size', y='Time', hue='Algorithm', marker='o', ax=ax1, palette=[p for p in sns.color_palette() if p != sns.color_palette()[2]])
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.legend(loc='upper left')
        if not insertion_c.empty:
            ax2 = ax1.twinx()
            color = sns.color_palette()[2]
            ax2.set_ylabel('Tempo Médio (s) - Insertion C (Escala Log)', color=color)
            sns.lineplot(data=insertion_c, x='Size', y='Time', linestyle='--', color=color, marker='x', ax=ax2, label="Insertion Sort C")
            ax2.tick_params(axis='y', labelcolor=color)
            if insertion_c['Time'].max() > 50: # Use log if IS C is very slow
                 ax2.set_yscale('log')
            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='center right')
            if ax1.get_legend() is not None: ax1.get_legend().remove()


        plt.title('Comparação das Variantes "C" (Médias)')
        plt.tight_layout()
        plt.savefig('variant_c_comparison_v2.png')
        plt.close()
        print("Gráfico 'variant_c_comparison_v2.png' gerado.")
    else:
        print("Não há dados para as variantes 'C'.")

    # Determine max size for Insertion Sort overall for limited plots
    insertion_sort_all_data = df[df['Algorithm'] == 'Insertion Sort']
    max_size_insertion_overall = 0
    if not insertion_sort_all_data.empty:
        max_size_insertion_overall = insertion_sort_all_data['Size'].max()
    
    # Default limit, can be adjusted if Insertion Sort has consistent data further out from Iter 1-3
    limit_size_for_overall_plot = 300000 
    # If Iter 4 has Insertion Sort data consistently for larger values than 300k, and other algos too,
    # this limit might be re-evaluated. For now, stick to 300k to match previous intent.
    # The new Iteration 4 for IS has 250k, 500k, 1M. So IS data goes far.
    # But Heap/Quick also have data far out. The 300k was based on IS from Iter 1-3.
    # Let's see how data availability looks across all algos up to 1M.
    
    # Sizes where *all three algorithm types* have at least one variant represented
    common_sizes = df_avg.groupby('Size')['Algorithm'].nunique()
    common_sizes = common_sizes[common_sizes == 3].index.tolist()
    limit_size_for_overall_plot = max(common_sizes) if common_sizes else 300000


    # --- Plot 7: Overall Comparison (log scale y-axis, limited size) ---
    plt.figure()
    # df_avg_limited_size = df_avg[df_avg['Size'] <= 300000] # Original limit
    df_avg_limited_size = df_avg[df_avg['Size'] <= limit_size_for_overall_plot]

    if not df_avg_limited_size.empty:
        sns.lineplot(data=df_avg_limited_size, x='Size', y='Time', hue='AlgorithmVariant', marker='o', style='Algorithm', dashes=False)
        plt.title(f'Comparação Geral (Médias, N <= {limit_size_for_overall_plot/1000:.0f}k)')
        plt.xlabel('Tamanho da Entrada (Size)')
        plt.ylabel('Tempo Médio (s) - Escala Logarítmica')
        plt.yscale('log')
        plt.legend(title='Algoritmo e Variante', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig('overall_comparison_log_limited_size_v2.png')
        plt.close()
        print(f"Gráfico 'overall_comparison_log_limited_size_v2.png' (até N={limit_size_for_overall_plot}) gerado.")
    else:
        print(f"Não há dados para 'overall_comparison_log_limited_size_v2.png' até N={limit_size_for_overall_plot}.")

    # --- Plot 8: HeapSort and QuickSort for larger sizes ---
    plt.figure()
    df_avg_heap_quick = df_avg[df_avg['Algorithm'].isin(['Heap Sort', 'Quick Sort'])]
    if not df_avg_heap_quick.empty:
        sns.lineplot(data=df_avg_heap_quick, x='Size', y='Time', hue='AlgorithmVariant', marker='o', style='Algorithm', dashes=False)
        plt.title('Comparação Heap Sort vs Quick Sort (Médias)')
        plt.xlabel('Tamanho da Entrada (Size)')
        plt.ylabel('Tempo Médio de Execução (s)')
        plt.legend(title='Algoritmo e Variante', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig('heap_quick_comparison_v2.png')
        plt.close()
        print("Gráfico 'heap_quick_comparison_v2.png' gerado.")
    else:
        print("Não há dados para 'heap_quick_comparison_v2.png'.")
        
    # --- Plot 9: Best of each algorithm type (A variants) - linear scale limited ---
    plt.figure()
    # variant_a_data_limited = df_avg[(df_avg['Variant'] == 'A') & (df_avg['Size'] <= 300000)]
    variant_a_data_limited = df_avg[(df_avg['Variant'] == 'A') & (df_avg['Size'] <= limit_size_for_overall_plot)]
    if not variant_a_data_limited.empty:
        sns.lineplot(data=variant_a_data_limited, x='Size', y='Time', hue='Algorithm', marker='o')
        plt.title(f'Variantes "A" (Médias, N <= {limit_size_for_overall_plot/1000:.0f}k, Escala Linear)')
        plt.xlabel('Tamanho da Entrada (Size)')
        plt.ylabel('Tempo Médio de Execução (s)')
        plt.legend(title='Algoritmo')
        plt.tight_layout()
        plt.savefig('variant_a_comparison_linear_limited_v2.png')
        plt.close()
        print(f"Gráfico 'variant_a_comparison_linear_limited_v2.png' (até N={limit_size_for_overall_plot}) gerado.")
    else:
        print(f"Não há dados para 'variant_a_comparison_linear_limited_v2.png' (até N={limit_size_for_overall_plot}).")

    print("Processamento de gráficos v2 concluído.")
    file_list_v2 = [
        'insertion_sort_performance_v2.png', 'heap_sort_performance_v2.png', 'quick_sort_performance_v2.png',
        'variant_a_comparison_v2.png', 'variant_b_comparison_v2.png', 'variant_c_comparison_v2.png',
        'overall_comparison_log_limited_size_v2.png', 'heap_quick_comparison_v2.png',
        'variant_a_comparison_linear_limited_v2.png'
    ]
    print(f"Ficheiros gerados: {', '.join(file_list_v2)}")