import numpy as np
import sys
import os
import time

# Asegurarse de que el path de utils esté disponible
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.quantizer import TurboQuantizer

def run_benchmark(num_vectors=500, dim=1024):
    quantizer = TurboQuantizer(dim, cache_dir="/tmp/turbo_bench_cache")
    
    # Generar vectores de prueba normalizados (igual que e5-large en coseno)
    rng = np.random.default_rng(seed=2024)
    data = rng.standard_normal((num_vectors, dim)).astype(np.float32)
    data = data / np.linalg.norm(data, axis=1, keepdims=True)
    
    queries = rng.standard_normal((5, dim)).astype(np.float32)
    queries = queries / np.linalg.norm(queries, axis=1, keepdims=True)
    
    errors = []
    print(f"\n--- Benchmark TurboQuant (Dim: {dim}, Vectores: {num_vectors}, Queries: {len(queries)}) ---\n")
    
    # Pre-comprimir todos los vectores
    t0 = time.time()
    compressed_data = [quantizer.compress(v) for v in data]
    t_compress = time.time() - t0
    print(f"⚙️  Compresión: {t_compress:.3f}s ({t_compress/num_vectors*1000:.2f}ms por vector)")
    
    # Calcular similitud asimétrica vs. dot product exacto
    t0 = time.time()
    for query in queries:
        for v_idx, (v, comp) in enumerate(zip(data, compressed_data)):
            original_dot = float(np.dot(query, v))
            turbo_dot = quantizer.compute_asymmetric_dot(query, comp)
            errors.append(abs(original_dot - turbo_dot))
    t_search = time.time() - t0
    
    total_ops = len(queries) * num_vectors
    print(f"🔍 Búsqueda asimétrica: {t_search:.3f}s ({total_ops} pares)")
    print(f"\n📊 Resultados de Distorsión:")
    print(f"   Error Medio Absoluto (MAE): {np.mean(errors):.6f}")
    print(f"   Error Máximo:               {np.max(errors):.6f}")
    print(f"   Desviación Estándar:        {np.std(errors):.6f}")
    
    # Validar compresión (bytes)
    sample_comp = compressed_data[0]
    original_bytes = dim * 4  # float32
    compressed_bytes = len(sample_comp) # Ahora es un objeto bytes
    ratio = original_bytes / compressed_bytes
    print(f"\n💾 Compresión: {original_bytes}B → {compressed_bytes}B (ratio: {ratio:.1f}x)")
    
    mae = np.mean(errors)
    if mae < 0.02:
        print(f"\n✅ ÉXITO: MAE={mae:.4f} < 2%. TurboQuant funcionando correctamente.")
    else:
        print(f"\n⚠️  ALERTA: MAE={mae:.4f} > 2%. Ajustar parámetros QJL.")

if __name__ == "__main__":
    run_benchmark()
