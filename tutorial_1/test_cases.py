# test_cases.py
import random

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
        if block_number < 10:
            accessed_blocks.append(block_number)
        cache_simulator.access(block_number)
    if print_details:
        print("  Sample of first 10 blocks accessed:", accessed_blocks)
    return block_count

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
    return access_count

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
    return access_count
