# main.py
import sys
from cache_simulator import FullyAssociativeCache
import test_cases

def run_all_tests(replacement_policy, memory_size, block_size, temporal_accesses, random_accesses):
    # We'll use a cache capacity of 128 blocks (2K words / 16 words per block)
    capacity = 128

    # Run Spatial Access Test
    print("=" * 60)
    cache_spatial = FullyAssociativeCache(capacity, replacement_policy)
    accesses = test_cases.spatial_access_test(cache_spatial, memory_size, block_size)
    print(cache_spatial)
    print("=" * 60)

    # Run Temporal Access Test (repeated access to block 0)
    cache_temporal = FullyAssociativeCache(capacity, replacement_policy)
    test_cases.temporal_access_test(cache_temporal, block_number=0, access_count=temporal_accesses)
    print(cache_temporal)
    print("=" * 60)

    # Run Random Access Test
    cache_random = FullyAssociativeCache(capacity, replacement_policy)
    test_cases.random_access_test(cache_random, memory_size, block_size, random_accesses)
    print(cache_random)
    print("=" * 60)

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
