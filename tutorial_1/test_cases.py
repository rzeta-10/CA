import random
import matplotlib.pyplot as plt

def spatial_access_test(cache_simulator, memory_size, block_size, print_details=True):
    """
    Simulate sequential access (spatial). Each block is accessed sequentially.
    """
    block_count = memory_size // block_size
    accessed_blocks = []
    if print_details:
        print("Spatial Access Test:")
        print("  Starting Address: 0")
    for block_number in range(block_count):
        accessed_blocks.append(block_number)
        cache_simulator.access(block_number)
    if print_details:
        print("  Sample of first 10 blocks accessed:", accessed_blocks[:10])
    return accessed_blocks

def temporal_access_test(cache_simulator, block_number, access_count, print_details=True):
    """
    Simulate repeated (temporal) access to a single block.
    """
    if print_details:
        print("Temporal Access Test:")
        print(f"  Starting Address: Block {block_number}")
        print(f"  Repeatedly accessing block {block_number} {access_count} times.")
    for _ in range(access_count):
        cache_simulator.access(block_number)
    return [block_number] * access_count

def random_access_test(cache_simulator, memory_size, block_size, access_count, print_details=True):
    """
    Simulate random accesses to memory blocks.
    """
    block_count = memory_size // block_size
    sample_accesses = []
    if print_details:
        print("Random Access Test:")
        print(f"  Memory Size: {memory_size} words, Block Size: {block_size} words")
        print(f"  Performing {access_count} random accesses. Sample addresses:")
    for i in range(access_count):
        block_number = random.randint(0, block_count - 1)
        if i < 10:
            sample_accesses.append(block_number)
        cache_simulator.access(block_number)
    if print_details:
        print("  Sample of first 10 random accesses:", sample_accesses)
    return sample_accesses

def plot_cache_performance(spatial_stats, temporal_stats, random_stats, filename='cache_performance.png'):
    """
    Create comparative bar plots for cache performance metrics and save as PNG.
    """
    tests = ['Spatial', 'Temporal', 'Random']
    metrics = {
        'Hit Rate (%)': [
            (spatial_stats['hits'] / (spatial_stats['hits'] + spatial_stats['misses'])) * 100,
            (temporal_stats['hits'] / (temporal_stats['hits'] + temporal_stats['misses'])) * 100,
            (random_stats['hits'] / (random_stats['hits'] + random_stats['misses'])) * 100
        ],
        'Average Comparisons': [
            spatial_stats['average_comparisons'],
            temporal_stats['average_comparisons'],
            random_stats['average_comparisons']
        ]
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Hit Rate Plot
    x = range(len(tests))
    ax1.bar(x, metrics['Hit Rate (%)'], color=['blue', 'green', 'red'])
    ax1.set_ylabel('Hit Rate (%)')
    ax1.set_title('Cache Hit Rate by Access Pattern')
    ax1.set_xticks(x)
    ax1.set_xticklabels(tests)

    # Average Comparisons Plot
    ax2.bar(x, metrics['Average Comparisons'], color=['blue', 'green', 'red'])
    ax2.set_ylabel('Average Comparisons')
    ax2.set_title('Average Cache Comparisons by Access Pattern')
    ax2.set_xticks(x)
    ax2.set_xticklabels(tests)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()