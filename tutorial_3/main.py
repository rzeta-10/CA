import random
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non–interactive plotting
import matplotlib.pyplot as plt

# ============================================================
# Helper class: CacheBlock (contains block address, valid, dirty)
# ============================================================
class CacheBlock:
    def __init__(self, block_addr=None, valid=False, dirty=False):
        self.block_addr = block_addr  # full block base address (16–bit address with lower 4 bits=0)
        self.valid = valid
        self.dirty = dirty

# ============================================================
# Level 1 Cache: Direct Mapped
#  – 2K words with 16–word blocks → 2048/16 = 128 lines.
#  – The index is computed as: (block_addr // block_size) mod 128.
# ============================================================
class DirectMappedCache:
    def __init__(self, size_words, block_size):
        self.block_size = block_size
        self.num_lines = size_words // block_size  # 2048/16 = 128
        self.lines = [CacheBlock() for _ in range(self.num_lines)]
        self.hits = 0
        self.misses = 0
        self.accesses = 0

    def index_for_block(self, block_addr):
        # block_addr is assumed aligned (lowest 4 bits = 0)
        return (block_addr // self.block_size) % self.num_lines

    def lookup(self, block_addr):
        self.accesses += 1
        idx = self.index_for_block(block_addr)
        block = self.lines[idx]
        if block.valid and block.block_addr == block_addr:
            self.hits += 1
            return True
        else:
            self.misses += 1
            return False

    def insert(self, block_addr, operation='read'):
        """
        Insert a block into L1. If there is an already–present block at the mapped index,
        return its (block_addr, dirty) status so that the simulator can send it to the victim cache
        (if clean) or write buffer (if dirty).
        """
        idx = self.index_for_block(block_addr)
        old_block = self.lines[idx]
        evicted = None
        if old_block.valid:
            evicted = (old_block.block_addr, old_block.dirty)
        self.lines[idx] = CacheBlock(block_addr=block_addr, valid=True, dirty=(operation=='write'))
        return evicted

    def update_write(self, block_addr):
        idx = self.index_for_block(block_addr)
        self.lines[idx].dirty = True

# ============================================================
# Level 2 Cache: 4–Way Set–Associative Cache
#  – 16K words with 16–word blocks → 16384/16 = 1024 blocks.
#  – With 4 ways, the number of sets = 1024/4 = 256.
#  – We use an LRU replacement mechanism.
# ============================================================
class SetAssociativeCache:
    def __init__(self, size_words, block_size, ways):
        self.block_size = block_size
        total_blocks = size_words // block_size
        self.num_sets = total_blocks // ways  # 1024/4 = 256
        self.ways = ways
        # For each set, maintain a list of CacheBlock objects.
        self.sets = [ [CacheBlock() for _ in range(ways)] for _ in range(self.num_sets) ]
        # For LRU we maintain a counter per block.
        self.lru_counters = [[0]*ways for _ in range(self.num_sets)]
        self.global_counter = 0
        self.hits = 0
        self.misses = 0
        self.accesses = 0

    def index_for_block(self, block_addr):
        return (block_addr // self.block_size) % self.num_sets

    def lookup(self, block_addr, operation='read'):
        self.accesses += 1
        set_idx = self.index_for_block(block_addr)
        for j, block in enumerate(self.sets[set_idx]):
            if block.valid and block.block_addr == block_addr:
                self.hits += 1
                # Update LRU counter.
                self.lru_counters[set_idx][j] = self.global_counter
                self.global_counter += 1
                if operation == 'write':
                    block.dirty = True
                return True
        self.misses += 1
        return False

    def insert(self, block_addr, operation='read'):
        set_idx = self.index_for_block(block_addr)
        # Look for an invalid (empty) block in the set.
        for j, block in enumerate(self.sets[set_idx]):
            if not block.valid:
                self.sets[set_idx][j] = CacheBlock(block_addr=block_addr, valid=True, dirty=(operation=='write'))
                self.lru_counters[set_idx][j] = self.global_counter
                self.global_counter += 1
                return None
        # Otherwise, use LRU replacement.
        lru_index = 0
        min_val = self.lru_counters[set_idx][0]
        for j in range(1, self.ways):
            if self.lru_counters[set_idx][j] < min_val:
                min_val = self.lru_counters[set_idx][j]
                lru_index = j
        evicted_block = self.sets[set_idx][lru_index]
        evicted = (evicted_block.block_addr, evicted_block.dirty)
        self.sets[set_idx][lru_index] = CacheBlock(block_addr=block_addr, valid=True, dirty=(operation=='write'))
        self.lru_counters[set_idx][lru_index] = self.global_counter
        self.global_counter += 1
        return evicted

# ============================================================
# Victim Cache: Fully–Associative, 4 Blocks.
# When L1 evicts a clean block, it is inserted here.
# ============================================================
class VictimCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.blocks = []  # each element is a tuple: (block_addr, dirty)
        self.hits = 0
        self.misses = 0

    def lookup(self, block_addr):
        for i, (b_addr, dirty) in enumerate(self.blocks):
            if b_addr == block_addr:
                self.hits += 1
                # Remove the block from victim cache upon hit.
                victim_block = self.blocks.pop(i)
                return victim_block, True
        self.misses += 1
        return None, False

    def insert(self, block_addr, dirty):
        # Use FIFO replacement.
        if len(self.blocks) >= self.capacity:
            self.blocks.pop(0)
        self.blocks.append((block_addr, dirty))

# ============================================================
# Write Buffer: 4 Blocks.
# When L1 evicts a dirty block, it is stored here until written back.
# If the buffer is full, we flush (simulate write–back).
# ============================================================
class WriteBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.blocks = []  # list of block addresses
        self.flushes = 0

    def insert(self, block_addr):
        self.blocks.append(block_addr)
        if len(self.blocks) > self.capacity:
            self.flush()

    def flush(self):
        # Simulate a flush: all blocks are written back to main memory.
        self.blocks = []
        self.flushes += 1

# ============================================================
# Prefetch Cache: For Instruction and Data Streams.
# Fully associative with FIFO replacement (4 blocks).
# On a prefetch hit, the block is removed from the prefetch cache.
# ============================================================
class PrefetchCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.blocks = []  # list of block addresses
        self.hits = 0
        self.misses = 0

    def lookup(self, block_addr):
        if block_addr in self.blocks:
            self.hits += 1
            self.blocks.remove(block_addr)
            return True
        else:
            self.misses += 1
            return False

    def insert(self, block_addr):
        if block_addr in self.blocks:
            return
        if len(self.blocks) >= self.capacity:
            self.blocks.pop(0)
        self.blocks.append(block_addr)

# ============================================================
# Multi–Level Cache Simulator (using all components)
# ============================================================
class MultiLevelCacheSimulator:
    def __init__(self):
        # Level 1: 2K words, 16–word block
        self.L1 = DirectMappedCache(size_words=2048, block_size=16)
        # Level 2: 16K words, 4–way associative, 16–word block
        self.L2 = SetAssociativeCache(size_words=16384, block_size=16, ways=4)
        # Victim Cache: 4 blocks
        self.victim = VictimCache(capacity=4)
        # Write Buffer: 4 blocks
        self.write_buffer = WriteBuffer(capacity=4)
        # Prefetch caches: one for instruction stream and one for data stream (each 4 blocks)
        self.prefetch_instr = PrefetchCache(capacity=4)
        self.prefetch_data  = PrefetchCache(capacity=4)
        # Statistics:
        self.main_memory_accesses = 0
        self.L1_hits = 0
        self.victim_hits = 0
        self.L2_hits = 0
        self.prefetch_hits = 0
        self.total_accesses = 0

    def access(self, address, operation='read'):
        """
        Simulate a memory access. The flow is:
          1. (For read accesses) Check the appropriate prefetch cache.
          2. Check L1.
          3. On L1 miss, check the victim cache.
          4. On victim miss, check L2.
          5. On L2 miss, fetch from main memory.
        When inserting into L1, if a block is evicted:
          – If dirty, add it to the write buffer.
          – If clean, add it to the victim cache.
        Also, after each access, prefetch the “next block” (block_addr + 16)
        into the appropriate prefetch cache.
        """
        self.total_accesses += 1
        # Align the address to a block boundary (lower 4 bits zero).
        block_addr = address & ~0xF

        # Decide access type for prefetching:
        # For reads, randomly decide whether the access is part of the instruction stream or data stream.
        if operation == 'read':
            access_type = 'instruction' if random.random() < 0.5 else 'data'
        else:
            access_type = 'data'

        # --- Step 1: Check Prefetch Cache (only for read accesses) ---
        if operation == 'read':
            if access_type == 'instruction':
                if self.prefetch_instr.lookup(block_addr):
                    self.prefetch_hits += 1
                    # Insert block into L1
                    evicted = self.L1.insert(block_addr, operation)
                    if evicted is not None:
                        evicted_block, dirty = evicted
                        if dirty:
                            self.write_buffer.insert(evicted_block)
                        else:
                            self.victim.insert(evicted_block, dirty)
                    # Prefetch next block.
                    self.prefetch_instr.insert(block_addr + 16)
                    return "Hit in Prefetch (Instruction)"
            else:
                if self.prefetch_data.lookup(block_addr):
                    self.prefetch_hits += 1
                    evicted = self.L1.insert(block_addr, operation)
                    if evicted is not None:
                        evicted_block, dirty = evicted
                        if dirty:
                            self.write_buffer.insert(evicted_block)
                        else:
                            self.victim.insert(evicted_block, dirty)
                    self.prefetch_data.insert(block_addr + 16)
                    return "Hit in Prefetch (Data)"

        # --- Step 2: Check L1 Cache ---
        if self.L1.lookup(block_addr):
            self.L1_hits += 1
            if operation == 'write':
                self.L1.update_write(block_addr)
            # After a hit, prefetch the next block.
            if access_type == 'instruction':
                self.prefetch_instr.insert(block_addr + 16)
            else:
                self.prefetch_data.insert(block_addr + 16)
            return "Hit in L1"

        # --- Step 3: L1 Miss → Check Victim Cache ---
        victim_block, found = self.victim.lookup(block_addr)
        if found:
            self.victim_hits += 1
            # Victim hit: bring the block back into L1.
            evicted = self.L1.insert(block_addr, operation)
            if evicted is not None:
                evicted_block, dirty = evicted
                if dirty:
                    self.write_buffer.insert(evicted_block)
                else:
                    self.victim.insert(evicted_block, dirty)
            if access_type == 'instruction':
                self.prefetch_instr.insert(block_addr + 16)
            else:
                self.prefetch_data.insert(block_addr + 16)
            return "Hit in Victim Cache"

        # --- Step 4: Victim Miss → Check L2 Cache ---
        if self.L2.lookup(block_addr, operation):
            self.L2_hits += 1
            # On L2 hit, insert block into L1.
            evicted = self.L1.insert(block_addr, operation)
            if evicted is not None:
                evicted_block, dirty = evicted
                if dirty:
                    self.write_buffer.insert(evicted_block)
                else:
                    self.victim.insert(evicted_block, dirty)
            if access_type == 'instruction':
                self.prefetch_instr.insert(block_addr + 16)
            else:
                self.prefetch_data.insert(block_addr + 16)
            return "Hit in L2"

        # --- Step 5: L2 Miss → Fetch from Main Memory ---
        self.main_memory_accesses += 1
        # Bring the block into L2.
        _ = self.L2.insert(block_addr, operation)
        # Now insert into L1.
        evicted = self.L1.insert(block_addr, operation)
        if evicted is not None:
            evicted_block, dirty = evicted
            if dirty:
                self.write_buffer.insert(evicted_block)
            else:
                self.victim.insert(evicted_block, dirty)
        if access_type == 'instruction':
            self.prefetch_instr.insert(block_addr + 16)
        else:
            self.prefetch_data.insert(block_addr + 16)
        return "Miss – Fetched from Main Memory"

    def get_performance(self):
        total_hits = self.L1_hits + self.victim_hits + self.L2_hits + self.prefetch_hits
        hit_ratio = (total_hits / self.total_accesses) * 100 if self.total_accesses > 0 else 0
        miss_ratio = (self.main_memory_accesses / self.total_accesses) * 100 if self.total_accesses > 0 else 0
        return {
            'Total Accesses': self.total_accesses,
            'L1 Hits': self.L1_hits,
            'Victim Hits': self.victim_hits,
            'L2 Hits': self.L2_hits,
            'Prefetch Hits': self.prefetch_hits,
            'Main Memory Accesses': self.main_memory_accesses,
            'Write Buffer Flushes': self.write_buffer.flushes,
            'Hit Ratio (%)': hit_ratio,
            'Miss Ratio (%)': miss_ratio
        }

    def reset(self):
        self.__init__()

# ============================================================
# Access Pattern Generators
# ============================================================
def generate_spatial_accesses(num_accesses, start_address=0):
    # For spatial, we access consecutive blocks.
    # (Each block is 16 words; we use addresses that are multiples of 16.)
    return [start_address + i * 16 for i in range(num_accesses)]

def generate_temporal_accesses(num_accesses, base_addresses=None, hot_prob=0.98, cold_start=10000):
    # For temporal accesses, most accesses come from a small "hot" set.
    if base_addresses is None:
        # Use a few hot blocks (ensure addresses are multiples of 16)
        base_addresses = [20*16, 21*16, 22*16, 23*16, 24*16, 25*16]
    access_sequence = []
    cold = cold_start
    for i in range(num_accesses):
        if random.random() < hot_prob:
            access_sequence.append(random.choice(base_addresses))
        else:
            access_sequence.append(cold)
            cold += 16
    return access_sequence

def generate_random_accesses(num_accesses, memory_size_words):
    # Generate random addresses and align them to 16–word blocks.
    seq = []
    for _ in range(num_accesses):
        addr = random.randint(0, memory_size_words - 16)
        addr_aligned = addr - (addr % 16)
        seq.append(addr_aligned)
    return seq

# ============================================================
# Simulation Parameters and Execution
# ============================================================
main_memory_size_words = 64 * 1024  # 64K words
num_accesses_list = [100, 500, 1000, 2000, 5000, 10000, 50000, 100000]
access_pattern_names = ['Spatial', 'Temporal', 'Random']

# We will store hit and miss ratios for each access pattern.
results = { pattern: {'hit_ratio': [], 'miss_ratio': []} for pattern in access_pattern_names }
details = { pattern: [] for pattern in access_pattern_names }

# Run simulations for each pattern and each access count.
for pattern in access_pattern_names:
    for num_accesses in num_accesses_list:
        simulator = MultiLevelCacheSimulator()
        if pattern == 'Spatial':
            seq = generate_spatial_accesses(num_accesses, start_address=0)
        elif pattern == 'Temporal':
            seq = generate_temporal_accesses(num_accesses)
        elif pattern == 'Random':
            seq = generate_random_accesses(num_accesses, main_memory_size_words)
        # For simplicity, we simulate all operations as 'read'.
        for addr in seq:
            simulator.access(addr, 'read')
        perf = simulator.get_performance()
        results[pattern]['hit_ratio'].append(perf['Hit Ratio (%)'])
        results[pattern]['miss_ratio'].append(perf['Miss Ratio (%)'])
        details[pattern].append(perf)

# ============================================================
# Plotting the Results (Hit Ratio and Miss Ratio vs Number of Accesses)
# ============================================================
for pattern in access_pattern_names:
    # Hit Ratio
    plt.figure(figsize=(8, 6))
    plt.plot(num_accesses_list, results[pattern]['hit_ratio'], marker='o', label='Hit Ratio')
    plt.xscale('log')
    plt.title(f'{pattern} Access Pattern – Hit Ratio')
    plt.xlabel('Number of Accesses (log scale)')
    plt.ylabel('Hit Ratio (%)')
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'multilevel_{pattern.lower()}_hit_ratio.png')
    plt.close()

    # Miss Ratio
    plt.figure(figsize=(8, 6))
    plt.plot(num_accesses_list, results[pattern]['miss_ratio'], marker='o', label='Miss Ratio')
    plt.xscale('log')
    plt.title(f'{pattern} Access Pattern – Miss Ratio')
    plt.xlabel('Number of Accesses (log scale)')
    plt.ylabel('Miss Ratio (%)')
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'multilevel_{pattern.lower()}_miss_ratio.png')
    plt.close()

# ============================================================
# Print Detailed Performance Metrics to Terminal
# ============================================================
print("\n--- Multi-Level Cache Performance Results ---")
print("Configuration:")
print("  L1 Cache: Direct Mapped, 2K words, 16-word blocks")
print("  L2 Cache: 4-Way Set Associative, 16K words, 16-word blocks")
print("  Main Memory: 64K words")
print("  Write Buffer: 4 Blocks")
print("  Victim Cache: 4 Blocks")
print("  Prefetch Cache: Instruction and Data (each 4 Blocks)")
print("----------------------------------------------------\n")

for pattern in access_pattern_names:
    print(f"Access Pattern: {pattern}")
    for i, num_accesses in enumerate(num_accesses_list):
        perf = details[pattern][i]
        print(f"  Number of Accesses: {num_accesses}")
        print(f"    Total Accesses         : {perf['Total Accesses']}")
        print(f"    L1 Hits                : {perf['L1 Hits']}")
        print(f"    Victim Cache Hits      : {perf['Victim Hits']}")
        print(f"    L2 Hits                : {perf['L2 Hits']}")
        print(f"    Prefetch Hits          : {perf['Prefetch Hits']}")
        print(f"    Main Memory Accesses   : {perf['Main Memory Accesses']}")
        print(f"    Write Buffer Flushes   : {perf['Write Buffer Flushes']}")
        print(f"    Hit Ratio              : {perf['Hit Ratio (%)']:.2f}%")
        print(f"    Miss Ratio             : {perf['Miss Ratio (%)']:.2f}%")
    print("="*50)
