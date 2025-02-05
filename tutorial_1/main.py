import sys
from cache_simulator import FullyAssociativeCache
import test_cases

def print_cache_statistics(cache_name, cache):
    stats = cache.get_stats()
    total_accesses = stats['hits'] + stats['misses']
    hit_rate = (stats['hits'] / total_accesses * 100) if total_accesses > 0 else 0
    
    print(f"\n{'='*20} {cache_name} Cache Statistics {'='*20}")
    print(f"Configuration:")
    print(f"  - Cache Size: {len(cache.cache)} blocks")
    print(f"  - Block Size: {cache.block_size} words")
    print(f"  - Replacement Policy: {cache.replacement_policy}")
    print("\nPerformance Metrics:")
    print(f"  - Total Accesses: {total_accesses}")
    print(f"  - Cache Hits: {stats['hits']}")
    print(f"  - Cache Misses: {stats['misses']}")
    print(f"  - Hit Rate: {hit_rate:.2f}%")
    print(f"  - Average Search Length: {stats['average_comparisons']:.2f}")

def run_all_tests(replacement_policy, memory_size, block_size, temporal_accesses, random_accesses):
    capacity = 128  # 2K words / 16 words per block
    
    # Spatial Access Test
    cache_spatial = FullyAssociativeCache(capacity, replacement_policy, block_size)
    test_cases.spatial_access_test(cache_spatial, memory_size, block_size)
    print_cache_statistics("Spatial Access", cache_spatial)
    
    # Temporal Access Test
    cache_temporal = FullyAssociativeCache(capacity, replacement_policy, block_size)
    test_cases.temporal_access_test(cache_temporal, 0, temporal_accesses)
    print_cache_statistics("Temporal Access", cache_temporal)
    
    # Random Access Test
    cache_random = FullyAssociativeCache(capacity, replacement_policy, block_size)
    test_cases.random_access_test(cache_random, memory_size, block_size, random_accesses)
    print_cache_statistics("Random Access", cache_random)
    
    # Generate and save comparison graph
    test_cases.plot_cache_performance(
        cache_spatial.get_stats(),
        cache_temporal.get_stats(),
        cache_random.get_stats(),
        filename='cache_performance.png'
    )
    print("Comparison graph saved as 'cache_performance.png'.")

def main():
    # Constants for simulation
    memory_size = 64 * 1024  # 64K words
    block_size = 16          # 16 words per block

    print("Cache Simulation: Fully Associative Cache with Multiple Replacement Policies")
    print("Available Replacement Policies: LRU, FIFO, Random")
    
    # Get user input for replacement policy and number of accesses for temporal and random tests.
    replacement_policy = input("Enter replacement policy (LRU/FIFO/Random): ").strip().upper()
    try:
        temporal_accesses = int(input("Enter the number of accesses for the temporal test: "))
        random_accesses = int(input("Enter the number of accesses for the random test: "))
    except ValueError:
        print("Invalid numeric input. Exiting.")
        sys.exit(1)

    run_all_tests(replacement_policy, memory_size, block_size, temporal_accesses, random_accesses)

if __name__ == "__main__":
    main()