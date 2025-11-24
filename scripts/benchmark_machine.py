"""
Script de Benchmark e Avaliação de Máquina
==========================================

Registra informações técnicas do computador para avaliar a velocidade
de preparação do modelo PrePol (treinamento, discretização H3, etc.).

Coleta:
- Especificações de hardware (CPU, RAM, disco)
- Informações de sistema operacional
- Versões de bibliotecas críticas
- Benchmarks de operações típicas do pipeline PrePol
- Tempos de I/O e processamento

Uso:
    python scripts/benchmark_machine.py
    python scripts/benchmark_machine.py --output logs/benchmark_results.json
"""

import sys
import platform
import psutil
import time
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

# Adiciona o diretório raiz ao path para importar prepol
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import h3
    H3_AVAILABLE = True
except ImportError:
    H3_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def get_system_info():
    """Coleta informações do sistema operacional e hardware."""
    info = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "os": platform.system(),
            "os_version": platform.version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        },
        "cpu": {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "max_frequency_mhz": psutil.cpu_freq().max if psutil.cpu_freq() else None,
            "current_frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        },
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "percent_used": psutil.virtual_memory().percent,
        },
        "disk": {},
        "libraries": get_library_versions(),
    }
    
    # Informações de disco para a partição do projeto
    try:
        disk_usage = psutil.disk_usage(str(project_root))
        info["disk"] = {
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "free_gb": round(disk_usage.free / (1024**3), 2),
            "percent_used": disk_usage.percent,
        }
    except Exception as e:
        info["disk"]["error"] = str(e)
    
    return info


def get_library_versions():
    """Retorna versões das bibliotecas críticas do projeto."""
    versions = {
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }
    
    if H3_AVAILABLE:
        versions["h3"] = h3.__version__
    
    if SKLEARN_AVAILABLE:
        import sklearn
        versions["scikit-learn"] = sklearn.__version__
    
    try:
        import joblib
        versions["joblib"] = joblib.__version__
    except ImportError:
        pass
    
    try:
        import pyarrow
        versions["pyarrow"] = pyarrow.__version__
    except ImportError:
        pass
    
    return versions


def benchmark_numpy_operations(size=10000000):
    """Benchmark de operações NumPy básicas."""
    print(f"  - NumPy operations (array size: {size:,})...", end=" ", flush=True)
    
    results = {}
    
    # Criação de array
    start = time.perf_counter()
    arr = np.random.rand(size)
    results["array_creation_s"] = round(time.perf_counter() - start, 4)
    
    # Operações matemáticas
    start = time.perf_counter()
    _ = np.sqrt(arr)
    results["sqrt_s"] = round(time.perf_counter() - start, 4)
    
    start = time.perf_counter()
    _ = np.exp(arr)
    results["exp_s"] = round(time.perf_counter() - start, 4)
    
    start = time.perf_counter()
    _ = arr.sum()
    results["sum_s"] = round(time.perf_counter() - start, 4)
    
    print("✓")
    return results


def benchmark_pandas_operations(rows=1000000):
    """Benchmark de operações Pandas típicas do pipeline."""
    print(f"  - Pandas operations ({rows:,} rows)...", end=" ", flush=True)
    
    results = {}
    
    # Criação de DataFrame
    start = time.perf_counter()
    df = pd.DataFrame({
        'date': pd.date_range('2013-01-01', periods=rows, freq='H'),
        'lat': np.random.uniform(-8.2, -7.9, rows),
        'lon': np.random.uniform(-35.1, -34.8, rows),
        'value': np.random.randint(0, 5, rows),
    })
    results["dataframe_creation_s"] = round(time.perf_counter() - start, 4)
    
    # GroupBy + aggregation
    start = time.perf_counter()
    _ = df.groupby(df['date'].dt.date)['value'].sum()
    results["groupby_sum_s"] = round(time.perf_counter() - start, 4)
    
    # Merge
    df2 = df.sample(n=min(100000, rows))
    start = time.perf_counter()
    _ = df.merge(df2, on='date', how='left')
    results["merge_s"] = round(time.perf_counter() - start, 4)
    
    # Sorting
    start = time.perf_counter()
    _ = df.sort_values(['date', 'lat'])
    results["sort_s"] = round(time.perf_counter() - start, 4)
    
    print("✓")
    return results


def benchmark_h3_operations(n_coords=100000):
    """Benchmark de operações H3 (discretização espacial)."""
    if not H3_AVAILABLE:
        print("  - H3 operations... ✗ (library not available)")
        return {"error": "h3 library not installed"}
    
    print(f"  - H3 operations ({n_coords:,} coordinates)...", end=" ", flush=True)
    
    results = {}
    
    # Gera coordenadas aleatórias (região de Recife)
    lats = np.random.uniform(-8.2, -7.9, n_coords)
    lons = np.random.uniform(-35.1, -34.8, n_coords)
    
    # Conversão lat/lon → H3
    start = time.perf_counter()
    try:
        # h3 v4 API
        cells = [h3.latlng_to_cell(lat, lon, 9) for lat, lon in zip(lats, lons)]
    except AttributeError:
        # h3 v3 API
        cells = [h3.geo_to_h3(lat, lon, 9) for lat, lon in zip(lats, lons)]
    results["latlng_to_h3_s"] = round(time.perf_counter() - start, 4)
    
    # K-ring neighbors (k=1)
    sample_cells = cells[:1000]
    start = time.perf_counter()
    try:
        # h3 v4 API
        _ = [h3.grid_disk(cell, 1) for cell in sample_cells]
    except AttributeError:
        # h3 v3 API
        _ = [h3.k_ring(cell, 1) for cell in sample_cells]
    results["k_ring_1000_cells_s"] = round(time.perf_counter() - start, 4)
    
    print("✓")
    return results


def benchmark_sklearn_training(n_samples=50000, n_features=10):
    """Benchmark de treinamento RandomForest (simulando PrePol)."""
    if not SKLEARN_AVAILABLE:
        print("  - RandomForest training... ✗ (library not available)")
        return {"error": "scikit-learn not installed"}
    
    print(f"  - RandomForest training ({n_samples:,} samples)...", end=" ", flush=True)
    
    results = {}
    
    # Gera dados sintéticos
    X = np.random.rand(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)
    
    # Treinamento
    start = time.perf_counter()
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    results["training_s"] = round(time.perf_counter() - start, 4)
    
    # Predição
    start = time.perf_counter()
    _ = rf.predict_proba(X[:10000])
    results["prediction_10k_samples_s"] = round(time.perf_counter() - start, 4)
    
    print("✓")
    return results


def benchmark_io_operations():
    """Benchmark de operações de I/O (leitura/escrita)."""
    print("  - I/O operations...", end=" ", flush=True)
    
    results = {}
    temp_dir = project_root / "scripts" / "temp_benchmark"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # CSV write/read
        df = pd.DataFrame(np.random.rand(100000, 10))
        csv_path = temp_dir / "test.csv"
        
        start = time.perf_counter()
        df.to_csv(csv_path, index=False)
        results["csv_write_s"] = round(time.perf_counter() - start, 4)
        
        start = time.perf_counter()
        _ = pd.read_csv(csv_path)
        results["csv_read_s"] = round(time.perf_counter() - start, 4)
        
        # Parquet write/read (se disponível)
        try:
            parquet_path = temp_dir / "test.parquet"
            
            start = time.perf_counter()
            df.to_parquet(parquet_path, index=False)
            results["parquet_write_s"] = round(time.perf_counter() - start, 4)
            
            start = time.perf_counter()
            _ = pd.read_parquet(parquet_path)
            results["parquet_read_s"] = round(time.perf_counter() - start, 4)
        except Exception:
            results["parquet_note"] = "pyarrow not available"
        
        print("✓")
    
    finally:
        # Limpa arquivos temporários
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    return results


def calculate_performance_score(benchmarks):
    """Calcula score de performance baseado nos benchmarks."""
    try:
        # Pesos para diferentes operações (quanto menor o tempo, melhor)
        scores = []
        
        if "numpy" in benchmarks and "sum_s" in benchmarks["numpy"]:
            # Score NumPy (baseline: 0.01s = 100 pontos)
            numpy_score = min(100, (0.01 / benchmarks["numpy"]["sum_s"]) * 100)
            scores.append(numpy_score)
        
        if "pandas" in benchmarks and "groupby_sum_s" in benchmarks["pandas"]:
            # Score Pandas (baseline: 0.1s = 100 pontos)
            pandas_score = min(100, (0.1 / benchmarks["pandas"]["groupby_sum_s"]) * 100)
            scores.append(pandas_score)
        
        if "h3" in benchmarks and "latlng_to_h3_s" in benchmarks["h3"]:
            # Score H3 (baseline: 1.0s = 100 pontos)
            h3_score = min(100, (1.0 / benchmarks["h3"]["latlng_to_h3_s"]) * 100)
            scores.append(h3_score)
        
        if "sklearn" in benchmarks and "training_s" in benchmarks["sklearn"]:
            # Score sklearn (baseline: 5.0s = 100 pontos)
            sklearn_score = min(100, (5.0 / benchmarks["sklearn"]["training_s"]) * 100)
            scores.append(sklearn_score)
        
        if scores:
            overall_score = round(sum(scores) / len(scores), 2)
            rating = "Excellent" if overall_score >= 80 else "Good" if overall_score >= 60 else "Fair" if overall_score >= 40 else "Poor"
            return {
                "overall_score": overall_score,
                "rating": rating,
                "note": "Score baseado em tempos de execução (100 = baseline ideal)"
            }
    
    except Exception as e:
        return {"error": str(e)}
    
    return {"overall_score": 0, "rating": "Unknown"}


def run_full_benchmark():
    """Executa todos os benchmarks e retorna resultados consolidados."""
    print("\n" + "="*60)
    print("PrePol Machine Benchmark")
    print("="*60 + "\n")
    
    print("Coletando informações do sistema...")
    system_info = get_system_info()
    print(f"  ✓ OS: {system_info['system']['os']} {system_info['system']['architecture']}")
    print(f"  ✓ CPU: {system_info['cpu']['logical_cores']} cores")
    print(f"  ✓ RAM: {system_info['memory']['total_gb']} GB\n")
    
    print("Executando benchmarks...\n")
    
    benchmarks = {
        "numpy": benchmark_numpy_operations(),
        "pandas": benchmark_pandas_operations(),
        "h3": benchmark_h3_operations(),
        "sklearn": benchmark_sklearn_training(),
        "io": benchmark_io_operations(),
    }
    
    print("\nCalculando performance score...")
    performance = calculate_performance_score(benchmarks)
    
    results = {
        "system_info": system_info,
        "benchmarks": benchmarks,
        "performance": performance,
    }
    
    print(f"  ✓ Overall Score: {performance.get('overall_score', 'N/A')} ({performance.get('rating', 'N/A')})\n")
    
    return results


def print_summary(results):
    """Imprime resumo dos resultados."""
    print("="*60)
    print("RESUMO")
    print("="*60 + "\n")
    
    sys_info = results["system_info"]
    bench = results["benchmarks"]
    perf = results["performance"]
    
    print(f"Máquina: {sys_info['system']['os']} | {sys_info['cpu']['logical_cores']} cores | {sys_info['memory']['total_gb']} GB RAM")
    print(f"Python: {sys_info['system']['python_version']}")
    print(f"Performance Score: {perf.get('overall_score', 'N/A')}/100 ({perf.get('rating', 'N/A')})\n")
    
    print("Tempos de Operação:")
    if "numpy" in bench and "sum_s" in bench["numpy"]:
        print(f"  • NumPy sum (10M elements): {bench['numpy']['sum_s']}s")
    if "pandas" in bench and "groupby_sum_s" in bench["pandas"]:
        print(f"  • Pandas groupby (1M rows): {bench['pandas']['groupby_sum_s']}s")
    if "h3" in bench and "latlng_to_h3_s" in bench["h3"]:
        print(f"  • H3 discretization (100K coords): {bench['h3']['latlng_to_h3_s']}s")
    if "sklearn" in bench and "training_s" in bench["sklearn"]:
        print(f"  • RandomForest training (50K samples): {bench['sklearn']['training_s']}s")
    
    print("\n" + "="*60 + "\n")


def save_results(results, output_path=None):
    """Salva resultados em arquivo JSON."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = project_root / "scripts" / f"benchmark_{timestamp}.json"
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Resultados salvos em: {output_path}")


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Benchmark de máquina para PrePol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output", "-o",
        help="Caminho para salvar resultados JSON (padrão: scripts/benchmark_TIMESTAMP.json)",
        default=None,
    )
    
    args = parser.parse_args()
    
    try:
        results = run_full_benchmark()
        print_summary(results)
        save_results(results, args.output)
        
        print("✓ Benchmark concluído com sucesso!")
        return 0
    
    except KeyboardInterrupt:
        print("\n\n✗ Benchmark interrompido pelo usuário.")
        return 1
    
    except Exception as e:
        print(f"\n\n✗ Erro durante benchmark: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
