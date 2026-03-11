import numpy as np
import csv
import os
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from scipy import stats, signal
from numpy.fft import rfft, rfftfreq
from sklearn.decomposition import PCA
from skrebate import ReliefF
from mpl_toolkits.mplot3d import Axes3D 


def upload_data(p_num):
    data = []
    data_path = f"FORTH_TRACE_DATASET-master/part{p_num}"

    for file in os.listdir(data_path):
        file_path = os.path.join(data_path, file)
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                data.append([float(val) for val in row])
    return np.array(data)

def calculate_modules(data):
    acc_module = np.linalg.norm(data[:, 1:4], axis=1) 
    gyro_module = np.linalg.norm(data[:, 4:7], axis=1) 
    mag_module = np.linalg.norm(data[:, 7:10], axis=1)
    return acc_module, gyro_module, mag_module

def create_boxplot_by_activity_and_device(data, modules, sensor_name):

    device_ids = data[:, 0]
    unique_devices = np.unique(device_ids)
    n_devices = len(unique_devices)

    ncols = 3
    nrows = (n_devices + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 6, nrows * 5), squeeze=False)
    fig.suptitle(f'Boxplots do Módulo do {sensor_name} por Atividade e Dispositivo', fontsize=16)

    axes_flat = axes.flatten()
    plot_count = 0

    for i, dev_id in enumerate(unique_devices):
        ax = axes_flat[i]
        dev_mask = (device_ids == dev_id)
        dev_data = data[dev_mask]
        dev_modules = modules[dev_mask]

        if dev_modules.size == 0:
            ax.set_title(f'Dispositivo {int(dev_id)} (Sem Dados)')
            ax.set_xticks([])
            ax.set_yticks([])
            continue

        activities = dev_data[:, 11] 
        unique_activities = np.unique(activities)

        labels_int = sorted([int(act) for act in unique_activities if np.any(activities == act)])
        if not labels_int:
             ax.set_title(f'Dispositivo {int(dev_id)} (Sem Atividades Válidas)')
             ax.set_xticks([])
             ax.set_yticks([])
             continue

        grouped_data = [dev_modules[activities == float(label)] for label in labels_int] # Usar float para comparação com dados

        ax.boxplot(grouped_data, tick_labels=labels_int) 
        ax.set_title(f'Dispositivo {int(dev_id)}')
        ax.set_xlabel('ID da Atividade') 
        ax.set_ylabel('Módulo do Vetor')
        ax.grid(True, linestyle='--', alpha=0.7)
        plot_count += 1

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

def analyze_outlier_density_iqr(data, modules, sensor_name, device_id=2):

    print(f"\n--- 3.2. Densidade de Outliers (Método IQR) para {sensor_name} (Dispositivo {device_id}) ---")

    device_mask = (data[:, 0] == device_id)
    modules_dev = modules[device_mask]
    activities_dev = data[device_mask, 11]

    unique_activities = np.unique(activities_dev)
    results = {}
    total_points_device = modules_dev.size
    total_outliers_device = 0

    print(f"{'Atividade':<10} | {'Densidade (%)':<15} | {'Nº Outliers':<12} | {'Nº Pontos':<10}")
    print("-" * 60)
    for act in unique_activities:
        act_data = modules_dev[activities_dev == act]
        n_r = act_data.size

        q1, q3 = np.percentile(act_data, [25, 75])
        iqr_val = q3 - q1
        lower_bound = q1 - (1.5 * iqr_val)
        upper_bound = q3 + (1.5 * iqr_val)

        outlier_mask = (act_data < lower_bound) | (act_data > upper_bound)
        n_o = np.sum(outlier_mask)
        total_outliers_device += n_o

        density = (n_o / n_r) * 100 if n_r > 0 else 0

        print(f"{int(act):<10} | {density:<15.2f} | {n_o:<12} | {n_r:<10}")
        results[act] = {'density': density, 'n_o': n_o, 'n_r': n_r}

    overall_density = (total_outliers_device / total_points_device) * 100 if total_points_device > 0 else 0
    print("-" * 60)
    print(f"{'TOTAL':<10} | {overall_density:<15.2f} | {total_outliers_device:<12} | {total_points_device:<10}")

    return results, overall_density

def zscore_outliers(arr, k=3.0):
    arr = np.asarray(arr)
    mean, std = np.mean(arr), np.std(arr)
    z_scores = np.abs((arr - mean) / std)
    return z_scores > k

def plot_zscore_comparison_by_device(data, modules, sensor_name, ks=[3.0, 3.5, 4.0]):
 
    device_ids = data[:, 0]
    unique_devices = np.unique(device_ids)
    n_devices = len(unique_devices)
    n_ks = len(ks)

    fig, axes = plt.subplots(n_devices, n_ks, figsize=(n_ks * 6, n_devices * 4), squeeze=False, sharey='row')
    fig.suptitle(f'Z-Score Outliers por Atividade - {sensor_name}', fontsize=16)

    overall_handles = []
    overall_labels = []

    for i, dev_id in enumerate(unique_devices):
        dev_mask = (device_ids == dev_id)
        modules_dev = modules[dev_mask]
        activities_dev = data[dev_mask, 11]
        unique_acts = np.unique(activities_dev)

        for j, k in enumerate(ks):
            ax = axes[i, j]
            has_inliers = False
            has_outliers = False

            sorted_unique_acts = sorted(unique_acts)

            for act_id in sorted_unique_acts:
                act_data = modules_dev[activities_dev == act_id]
                if act_data.size == 0: continue

                outlier_mask = zscore_outliers(act_data, k=k)
                x_coords = np.full(act_data.shape, act_id)

                # Plotar inliers (azul)
                inliers = ax.scatter(x_coords[~outlier_mask], act_data[~outlier_mask],
                                     color='blue', s=6, alpha=0.6, label='Inlier')
                if np.any(~outlier_mask): has_inliers = True

                # Plotar outliers (vermelho)
                outliers = ax.scatter(x_coords[outlier_mask], act_data[outlier_mask],
                                      color='red', s=10, marker='x', label='Outlier')
                if np.any(outlier_mask): has_outliers = True

            ax.set_title(f'Disp {int(dev_id)}, k = {k}')
            ax.set_xlabel('ID da Atividade')
            if j == 0: ax.set_ylabel('Módulo do Vetor')

            if len(sorted_unique_acts) > 0:
                 ax.set_xticks(sorted_unique_acts)
                 ax.set_xticklabels([int(a) for a in sorted_unique_acts])

            ax.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

def kmeans_outlier_combined_3d(acc_module, gyro_module, mag_module, n_clusters_list=[3,4,5], std_fact = 2.0):

    # Normalizar
    scaler = StandardScaler()
    X = np.vstack((acc_module, gyro_module, mag_module)).T
    X_scaled = scaler.fit_transform(X)

    fig = plt.figure(figsize=(18, 6))
    fig.suptitle("Clusters e Outliers K-Means 3D (Módulos Combinados, Distância) - TODOS OS DISPOSITIVOS", fontsize=14)

    for i, k in enumerate(n_clusters_list, start=1):
        ax = fig.add_subplot(1, len(n_clusters_list), i, projection='3d')

        # K-Means
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        centers = kmeans.cluster_centers_

        # Distâncias e threshold
        distances = np.linalg.norm(X_scaled - centers[labels], axis=1)
        threshold = np.mean(distances) + std_fact * np.std(distances)
        outlier_mask = distances > threshold

        # Plot inliers (clusters coloridos)
        ax.scatter(
            X_scaled[~outlier_mask, 0],
            X_scaled[~outlier_mask, 1],
            X_scaled[~outlier_mask, 2],
            c=labels[~outlier_mask],
            cmap='viridis',
            s=5,
            alpha=0.6
        )

        ax.scatter(
            X_scaled[outlier_mask, 0],
            X_scaled[outlier_mask, 1],
            X_scaled[outlier_mask, 2],
            c='red',
            marker='x',
            s=15,
            alpha=0.8
        )

        ax.set_title(f'k = {k}\nOutliers: {np.sum(outlier_mask)}')
        ax.set_xlabel('Módulo Acel (scaled)')
        ax.set_ylabel('Módulo Gyro (scaled)')
        ax.set_zlabel('Módulo Mag (scaled)')

    plt.tight_layout()
    plt.show()      

def dbscan_outlier_combined_3d(data, acc_module, gyro_module, mag_module, device_id_to_filter=2, params_list=None):
    """
    Aplica DBSCAN para detecção de outliers no espaço 3D dos módulos dos sensores.
    Filtra por um dispositivo específico.
    Implementa o ponto 3.7.1 (Bónus).
    """
    print(f"\n--- 3.7.1. Análise de Outliers DBSCAN 3D (Módulos Combinados) - DISPOSITIVO {device_id_to_filter} ---")

    # Parâmetros (eps, min_samples) para testar
    if params_list is None:
        params_list = [
            (0.5, 10),  # eps=0.5, min_samples=10
            (0.3, 15),  # eps=0.3, min_samples=15
            (0.7, 5)    # eps=0.7, min_samples=5
        ]

    # --- Filtrar dados pelo device_id_to_filter ---
    device_mask = (data[:, 0] == device_id_to_filter)
    if not np.any(device_mask):
        print(f"ERRO: Não foram encontrados dados para o dispositivo {device_id_to_filter}.")
        return

    acc_module_dev = acc_module[device_mask]
    gyro_module_dev = gyro_module[device_mask]
    mag_module_dev = mag_module[device_mask]
    
    print(f"A analisar {len(acc_module_dev)} amostras do dispositivo {device_id_to_filter}.")

    # Normalizar (apenas os dados do dispositivo)
    scaler = StandardScaler()
    X = np.vstack((acc_module_dev, gyro_module_dev, mag_module_dev)).T
    X_scaled = scaler.fit_transform(X)

    n_plots = len(params_list)
    fig = plt.figure(figsize=(n_plots * 6, 5)) # (width, height)
    fig.suptitle(f"Clusters e Outliers DBSCAN 3D (Módulos) - Dispositivo {device_id_to_filter}", fontsize=14)

    for i, (eps_val, min_s_val) in enumerate(params_list, start=1):
        ax = fig.add_subplot(1, n_plots, i, projection='3d')

        # Aplicar DBSCAN
        db = DBSCAN(eps=eps_val, min_samples=min_s_val, n_jobs=-1) 
        labels = db.fit_predict(X_scaled)

        # Outliers são naturalmente identificados com label -1
        outlier_mask = (labels == -1)
        n_outliers = np.sum(outlier_mask)
        n_clusters = len(np.unique(labels)) - (1 if n_outliers > 0 else 0)

        print(f"Params (eps={eps_val}, min_s={min_s_val}): Encontrados {n_clusters} clusters e {n_outliers} outliers.")

        # Plot inliers (pontos que pertencem a um cluster)
        ax.scatter(
            X_scaled[~outlier_mask, 0],
            X_scaled[~outlier_mask, 1],
            X_scaled[~outlier_mask, 2],
            c=labels[~outlier_mask], # Cor por cluster
            cmap='viridis',
            s=5,
            alpha=0.6
        )

        # Plot outliers (pontos com label -1)
        ax.scatter(
            X_scaled[outlier_mask, 0],
            X_scaled[outlier_mask, 1],
            X_scaled[outlier_mask, 2],
            c='red',
            marker='x',
            s=15,
            alpha=0.8,
            label='Outlier'
        )

        ax.set_title(f'eps={eps_val}, min_s={min_s_val}\nClusters: {n_clusters}, Outliers: {n_outliers}')
        ax.set_xlabel('Módulo Acel (scaled)')
        ax.set_ylabel('Módulo Gyro (scaled)')
        ax.set_zlabel('Módulo Mag (scaled)')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


def test_significance_by_activity_all_devices(data, modules, sensor_name):
    """Realiza testes de significância das médias dos módulos por atividade para todos os dispositivos."""
    print(f"\n{'='*70}\n4.1 Teste de significância das médias — {sensor_name}\n{'='*70}")

    device_ids = np.unique(data[:, 0])

    for device_id in device_ids:
        print(f"\n{'-'*60}\nDispositivo {int(device_id)}\n{'-'*60}")

        mask_dev = data[:, 0] == device_id
        modules_dev = modules[mask_dev]
        activities = data[mask_dev, 11]
        unique_acts = np.unique(activities)
        grouped = [modules_dev[activities == act] for act in unique_acts]

        print("Teste de normalidade (Kolmogorov-Smirnov):")
        normal_results = []
        all_groups_large_enough = True

        for act, values in zip(unique_acts, grouped):
            if len(values) < 20:
                print(f"Atividade {int(act):<2}: (Amostra pequena, n={len(values)}) → Assumindo Não normal")
                normal_results.append(False)
                if len(values) == 0:
                    all_groups_large_enough = False
                continue

            scaled_values = (values - np.mean(values)) / np.std(values) if np.std(values) > 0 else values
            try:
                stat, p = stats.kstest(scaled_values, 'norm')
            except ValueError:
                print(f"Atividade {int(act):<2}: (Erro no teste K-S, dados constantes?) → Assumindo Não normal")
                normal_results.append(False)
                continue

            is_normal = p > 0.05
            normal_results.append(is_normal)
            print(f"Atividade {int(act):<2}: Stat={stat:.4f}, p={p:.4f} → {'Normal' if is_normal else 'Não normal'}")

        if not all_groups_large_enough:
            print("\nAVISO: Um ou mais grupos estão vazios. Impossível realizar teste de comparação.")
            continue

        # Escolha do teste
        grouped_filtered = [g for g in grouped if len(g) > 0]
        if len(grouped_filtered) < 2:
            print("AVISO: Menos de dois grupos com dados. Impossível realizar teste.")
            continue

        if all(normal_results):
            test_name = "ANOVA"
            f_stat, p_value = stats.f_oneway(*grouped_filtered)
        else:
            test_name = "Kruskal-Wallis"
            try:
                f_stat, p_value = stats.kruskal(*grouped_filtered)
            except ValueError as e:
                print(f"ERRO ao executar Kruskal-Wallis: {e}")
                continue

        print(f"\nResultado ({test_name}): Estatística={f_stat:.4f}, p-valor={p_value:.6f}")

FS = 100
WINDOW_SEC = 5.0 
WINDOW_LEN = int(WINDOW_SEC * FS)
WINDOW_STEP = WINDOW_LEN // 2 

def sliding_windows(data, labels, win_len=WINDOW_LEN, step=WINDOW_STEP):

    n = data.shape[0]
    for start in range(0, n - win_len + 1, step):
        w = slice(start, start + win_len)
        lab = np.unique(labels[w])
        if len(lab) == 1:
            yield start, data[w], lab[0]
        else:
            continue

def compute_statistical_features(x):
    # x: 1D array
    features = {}
    features['mean'] = np.mean(x)
    features['median'] = np.median(x)
    features['std'] = np.std(x)
    features['var'] = np.var(x)
    features['rms'] = np.sqrt(np.mean(x**2))
    # derivatives
    d = np.diff(x)
    features['mean_deriv'] = np.mean(d) if len(d)>0 else 0.0
    # skew/kurt
    features['skew'] = stats.skew(x)
    features['kurtosis'] = stats.kurtosis(x)
    # iqr
    q1, q3 = np.percentile(x, [25,75])
    features['iqr'] = q3 - q1
    # zero crossing
    zc = ((x[:-1] * x[1:]) < 0).sum() / float(len(x))
    features['zero_cross_rate'] = zc
    # mean crossing
    mean_val = features['mean']
    mc = (((x[:-1]-mean_val)*(x[1:]-mean_val))<0).sum() / float(len(x))
    features['mean_cross_rate'] = mc
    return features

def spectral_features(x, fs=FS):
    feats = {}
    X = rfft(x - np.mean(x))  # remove mean if desired
    P = np.abs(X)**2
    freqs = rfftfreq(len(x), 1.0/fs)
    # dominant frequency (exclude DC)
    if len(P)>1:
        idx = np.argmax(P[1:]) + 1
        feats['dom_freq'] = freqs[idx]
    else:
        feats['dom_freq'] = 0.0
    feats['energy'] = P.sum() / len(x)
    # spectral entropy
    ps = P / (P.sum() + 1e-12)
    ps = ps + 1e-12
    feats['spec_entropy'] = -np.sum(ps * np.log(ps))
    return feats

def movement_intensity_features(ax, ay, az):
    # MI(t)
    mi = np.sqrt(ax**2 + ay**2 + az**2)
    AI = np.mean(mi)
    VI = np.var(mi)
    SMA = np.mean(np.abs(ax) + np.abs(ay) + np.abs(az))
    return {'AI': AI, 'VI': VI, 'SMA': SMA}

def eigenvalue_features(ax, ay, az):
    X = np.vstack([ax, ay, az]).T
    C = np.cov(X, rowvar=False)
    vals = np.linalg.eigvalsh(C)  # sorted ascending
    vals = np.sort(vals)[::-1]    # descending
    return {'EVA1': float(vals[0]), 'EVA2': float(vals[1])}

def cagc_feature(ax, ay, az):
    # gravidade ~ ax, heading ~ norm(y,z)
    heading = np.sqrt(ay**2 + az**2)
    # corr coef between ax and heading
    if np.std(ax)>0 and np.std(heading)>0:
        r = np.corrcoef(ax, heading)[0,1]
    else:
        r = 0.0
    return {'CAGH': float(r)}

def avg_velocity_from_acc(ax, dt=1.0/FS):
    # simples integração (pode precisar de detrend/highpass para drift)
    v = np.cumsum(ax) * dt
    return np.mean(v)

def get_corr(a, b):
    """Calcula a correlação de Pearson, tratando valores constantes."""
    if np.std(a) > 0 and np.std(b) > 0:
        r = np.corrcoef(a, b)[0, 1]
        # Retorna 0 se a correlação for NaN (pode acontecer com dados quase constantes)
        return r if np.isfinite(r) else 0.0
    else:
        return 0.0

def aratsg_feature(gx, fs=FS):
    dt = 1.0/fs
    angles = np.cumsum(gx) * dt
    return np.mean(angles)

def extract_features_window(win_data, fs=FS):

    ax, ay, az = win_data[:,0], win_data[:,1], win_data[:,2]
    gx, gy, gz = win_data[:,3], win_data[:,4], win_data[:,5]
    
    # estadisticas por eixo
    feat = {}
    for name, arr in [('ax',ax),('ay',ay),('az',az),('gx',gx),('gy',gy),('gz',gz)]:
        stat = compute_statistical_features(arr)
        spec = spectral_features(arr, fs=fs)
        # prefix keys
        for k,v in {**stat, **spec}.items():
            feat[f'{name}_{k}'] = v
    
    # ADICIONADO: Pairwise Correlation (Tabela 1 Artigo )
    feat['corr_acc_xy'] = get_corr(ax, ay)
    feat['corr_acc_xz'] = get_corr(ax, az)
    feat['corr_acc_yz'] = get_corr(ay, az)
    feat['corr_gyro_xy'] = get_corr(gx, gy)
    feat['corr_gyro_xz'] = get_corr(gx, gz)
    feat['corr_gyro_yz'] = get_corr(gy, gz)
            
    # physical features (acel)
    feat.update(movement_intensity_features(ax,ay,az))
    feat.update(eigenvalue_features(ax,ay,az))
    # A sua implementação de cagc_feature assume ax=grav, ay/az=heading
    feat.update(cagc_feature(ax,ay,az)) 

    feat['ARATG'] = aratsg_feature(gx, fs=fs) 
    feat['AVH'] = np.linalg.norm([avg_velocity_from_acc(ay,1/fs), avg_velocity_from_acc(az,1/fs)])
    feat['AVG'] = avg_velocity_from_acc(ax,1/fs)
    feat['AAE'] = np.mean([spectral_features(ax,fs)['energy'],
                           spectral_features(ay,fs)['energy'],
                           spectral_features(az,fs)['energy']])
    feat['ARE'] = np.mean([spectral_features(gx,fs)['energy'],
                           spectral_features(gy,fs)['energy'],
                           spectral_features(gz,fs)['energy']])
    return feat

def analyze_pca(feature_matrix, feature_names):

    print(f"\n{'='*60}\n4.3 & 4.4 - Análise de Componentes Principais (PCA)\n{'='*60}")

    # Normalização (z-score)
    scaler = StandardScaler() 
    features_scaled = scaler.fit_transform(feature_matrix)

    # PCA
    pca = PCA()
    features_pca = pca.fit_transform(features_scaled)
    print(f"PCA aplicado. Número total de componentes calculadas: {pca.n_components_}")

    explained_variance_ratio = pca.explained_variance_ratio_
    cumulative_explained_variance = np.cumsum(explained_variance_ratio)

    # Quantas componentes explicam 75%?
    n_components_75 = np.where(cumulative_explained_variance >= 0.75)[0][0] + 1
    print(f"\nSão necessárias {n_components_75} componentes principais para explicar pelo menos 75% da variância.")

    # Vamos mostrar as features que mais contribuem para as N componentes que "ficaram"
    print("\n--- Contribuição das Features para as Componentes Principais (Top 5) ---")
    
    for i in range(n_components_75):
        print(f"\nPC{i+1} (Explica {explained_variance_ratio[i]*100:.2f}% da variância):")
        
        loadings = pca.components_[i]
        
        feature_loadings = sorted(zip(feature_names, loadings), key=lambda x: abs(x[1]), reverse=True)
        
        for feature, loading in feature_loadings[:5]:
            print(f"  {feature:<25} (Peso: {loading:.4f})")

    plt.figure(figsize=(10, 6))
    plt.bar(range(1, len(explained_variance_ratio) + 1),
            explained_variance_ratio, alpha=0.7, color='b', label='Variância Explicada')
    plt.step(range(1, len(cumulative_explained_variance) + 1),
             cumulative_explained_variance, where='mid', color='r', label='Variância Acumulada')
    plt.axhline(y=0.75, color='g', linestyle='--', label='75% Variância')
    plt.axvline(x=n_components_75, color='red', linestyle='--', label=f'{n_components_75} Componentes')
    plt.title('Análise de Componentes Principais (PCA)')
    plt.xlabel('Número da Componente Principal')
    plt.ylabel('Proporção da Variância Explicada')
    plt.legend()
    plt.tight_layout()
    plt.show()

    # --- 4.4.1: Exemplo de compressão ---
    print("\n4.4.1 — Exemplo de compressão do vetor de features:")
    example_idx = 0  # ou outro índice de janela
    reduced_example = features_pca[example_idx, :n_components_75]
    print(f"→ Janela #{example_idx}: {n_components_75} componentes principais =\n{reduced_example}\n")

    return pca, scaler, features_pca, n_components_75

def fisher_score(X, y):

    unique_classes = np.unique(y)
    n_features = X.shape[1]
    scores = np.zeros(n_features)

    overall_mean = np.mean(X, axis=0)

    for i in range(n_features):
        num = 0.0
        den = 0.0
        for c in unique_classes:
            X_c = X[y == c, i]
            n_c = len(X_c)
            if n_c < 2:
                continue
            mean_c = np.mean(X_c)
            var_c = np.var(X_c)
            num += n_c * (mean_c - overall_mean[i])**2
            den += n_c * var_c
        scores[i] = num / den if den > 0 else 0.0

    return scores

def feature_selection_analysis(feature_matrix, feature_names, labels_vector):
    print(f"\n{'='*60}\n4.5 & 4.6 - Feature Selection: Fisher Score e ReliefF\n{'='*60}")

    fisher_scores = fisher_score(feature_matrix, labels_vector)
    sorted_idx_fisher = np.argsort(fisher_scores)[::-1]
    top10_fisher = sorted_idx_fisher[:10]

    print("\nTop 10 Features — Fisher Score:")
    for rank, idx in enumerate(top10_fisher, 1):
        print(f"{rank:2d}. {feature_names[idx]}  (score={fisher_scores[idx]:.4f})")

    # --- ReliefF ---
    print("\nA aplicar ReliefF")
    relief = ReliefF(n_neighbors=10, n_features_to_select=10)
    relief.fit(feature_matrix, labels_vector)
    relief_scores = relief.feature_importances_
    sorted_idx_relief = np.argsort(relief_scores)[::-1]
    top10_relief = sorted_idx_relief[:10]

    print("\nTop 10 Features — ReliefF:")
    for rank, idx in enumerate(top10_relief, 1):
        print(f"{rank:2d}. {feature_names[idx]}  (score={relief_scores[idx]:.4f})")

    return top10_fisher, top10_relief, fisher_scores, relief_scores

def main():
    """Função principal para executar o pipeline de análise de dados."""
    participant_id = 0
    data = upload_data(participant_id)
    if data.size == 0:
        print(f"Não foram carregados dados para o participante {participant_id}. A terminar.")
        return
    
    acc_module, gyro_module, mag_module = calculate_modules(data)

    # Ponto 3.1: Boxplots
    create_boxplot_by_activity_and_device(data, acc_module, "Acelerómetro")
    create_boxplot_by_activity_and_device(data, gyro_module, "Giroscópio")
    create_boxplot_by_activity_and_device(data, mag_module, "Magnetómetro")

    # Ponto 3.2: Densidade de Outliers (IQR)
    analyze_outlier_density_iqr(data, acc_module, "Acelerómetro", device_id=2)
    analyze_outlier_density_iqr(data, gyro_module, "Giroscópio", device_id=2)
    analyze_outlier_density_iqr(data, mag_module, "Magnetómetro", device_id=2)

    # Ponto 3.3 & 3.4: Outliers Z-Score
    plot_zscore_comparison_by_device(data, acc_module, "Acelerómetro", ks=[3.0, 3.5, 4.0])
    plot_zscore_comparison_by_device(data, gyro_module, "Giroscópio", ks=[3.0, 3.5, 4.0])
    plot_zscore_comparison_by_device(data, mag_module, "Magnetómetro", ks=[3.0, 3.5, 4.0])
    
    # Ponto 3.6 & 3.7: K-Means combinado (Acel + Gyro + Mag)
    # Nota: K-Means corre em TODOS os dispositivos, como implementado originalmente.
    kmeans_outlier_combined_3d(acc_module, gyro_module, mag_module, n_clusters_list=[3,4,5])

    
    # Ponto 3.7.1 (Bónus): DBSCAN combinado
    # A correr apenas para o Dispositivo 2, como pedido.
    dbscan_params_to_test = [
        (0.5, 10),  # eps=0.5, min_samples=10
        (0.3, 15),  # eps=0.3, min_samples=15
        (0.7, 10)   # eps=0.7, min_samples=10
    ]
    # Passamos o 'data' para permitir o filtro, e 'device_id_to_filter=2'
    dbscan_outlier_combined_3d(data, acc_module, gyro_module, mag_module, 
                               device_id_to_filter=2, 
                               params_list=dbscan_params_to_test)
    

    # Ponto 4.1: Testes de Significância
    test_significance_by_activity_all_devices(data, acc_module, "Acelerómetro")
    test_significance_by_activity_all_devices(data, gyro_module, "Giroscópio")
    test_significance_by_activity_all_devices(data, mag_module, "Magnetómetro")

    # Ponto 4.2: Extração de Features
    all_features = []
    all_labels = []
    sensor_data = data[:, 1:10]   # ax..mz
    activity_labels = data[:, 11] # última coluna

    # Criar janelas válidas
    for start, win_data, win_label in sliding_windows(sensor_data, activity_labels):
        # Extrair features desta janela
        feat_dict = extract_features_window(win_data)
        all_features.append(list(feat_dict.values()))
        all_labels.append(win_label)

    # Converter para arrays
    feature_matrix = np.array(all_features)
    # Certificar que feat_dict não está vazio (caso não haja janelas)
    if not all_features:
        print("Não foram geradas janelas de features. A terminar o script mais cedo.")
        return
        
    feature_names = list(feat_dict.keys())
    labels_vector = np.array(all_labels)

    print(f"Features extraídas: {feature_matrix.shape[1]} por janela.")
    print(f"Número de janelas válidas: {feature_matrix.shape[0]}")

    # Ponto 4.3 & 4.4: Análise com PCA
    pca, scaler, features_pca, n_components_75 = analyze_pca(feature_matrix, feature_names)

    # Ponto 4.5 & 4.6: Fisher Score e ReliefF
    top10_fisher, top10_relief, fisher_scores, relief_scores = feature_selection_analysis(
        feature_matrix, feature_names, labels_vector
    )

if __name__ == "__main__":
    main()