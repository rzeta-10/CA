import random
import matplotlib
matplotlib.use('Agg')  # For non-interactive plotting (e.g. on headless machines)
import matplotlib.pyplot as plt

########################################
# EXP01 SIMULATOR (Single-Level Cache)
########################################

class CacheLine:
    def __init__(self, tag=None, valid=False, dirty=False):
        self.tag = tag
        self.valid = valid
        self.dirty = dirty
        self.lru_counter = 0  # For LRU replacement

class FullyAssociativeCache:
    def __init__(self, cache_size_words, block_size_words, replacement_policy='LRU'):
        self.cache_size_lines = cache_size_words // block_size_words  # e.g., 2048/16 = 128 lines
        self.block_size = block_size_words
        self.replacement_policy = replacement_policy
        self.cache = [CacheLine() for _ in range(self.cache_size_lines)]
        self.cache_lines_used = 0
        self.misses = 0
        self.searches = 0
        self.hits = 0
        self.lru_counter = 0

    def address_breakdown(self, address):
        # With block size 16 words, we have a 4-bit block offset.
        tag = address >> 4  
        return tag

    def search_cache(self, tag):
        self.searches += 1
        for i in range(len(self.cache)):
            line = self.cache[i]
            if line.valid and line.tag == tag:
                self.hits += 1
                if self.replacement_policy == 'LRU':
                    self.cache[i].lru_counter = self.lru_counter
                    self.lru_counter += 1
                return True
        return False

    def add_to_cache(self, tag, operation='read'):
        # Look for an empty slot first.
        for i in range(self.cache_size_lines):
            if not self.cache[i].valid:
                self.cache[i] = CacheLine(tag=tag, valid=True, dirty=(operation=='write'))
                if self.replacement_policy == 'LRU':
                    self.cache[i].lru_counter = self.lru_counter
                    self.lru_counter += 1
                self.cache_lines_used += 1
                return None  # No eviction
        # Otherwise, use LRU replacement.
        lru_index = 0
        min_counter = self.cache[0].lru_counter
        for i in range(1, self.cache_size_lines):
            if self.cache[i].lru_counter < min_counter:
                min_counter = self.cache[i].lru_counter
                lru_index = i
        evicted = (self.cache[lru_index].tag, self.cache[lru_index].dirty)
        self.cache[lru_index] = CacheLine(tag=tag, valid=True, dirty=(operation=='write'))
        if self.replacement_policy == 'LRU':
            self.cache[lru_index].lru_counter = self.lru_counter
            self.lru_counter += 1
        return evicted

    def access_memory(self, address, operation='read'):
        tag = self.address_breakdown(address)
        if self.search_cache(tag):
            if operation == 'write':
                for line in self.cache:
                    if line.valid and line.tag == tag:
                        line.dirty = True
                        break
            return "Hit"
        else:
            self.misses += 1
            self.add_to_cache(tag, operation)
            return "Miss"

    def simulate_accesses(self, access_sequence, operation_sequence=None):
        results = []
        if operation_sequence is None:
            operation_sequence = ['read'] * len(access_sequence)
        for i in range(len(access_sequence)):
            addr = access_sequence[i]
            op = operation_sequence[i]
            res = self.access_memory(addr, op)
            results.append((addr, op, res))
        return results

    def get_performance_metrics(self):
        hit_ratio = (self.hits / self.searches) * 100 if self.searches > 0 else 0
        miss_ratio = (self.misses / self.searches) * 100 if self.searches > 0 else 0
        return {
            "Total Accesses": self.searches,
            "Hits": self.hits,
            "Misses": self.misses,
            "Hit Ratio (%)": hit_ratio,
            "Miss Ratio (%)": miss_ratio
        }

    def reset_metrics(self):
        self.misses = 0
        self.searches = 0
        self.hits = 0
        self.lru_counter = 0
        self.cache = [CacheLine() for _ in range(self.cache_size_lines)]
        self.cache_lines_used = 0

########################################
# EXTENDED MULTI-LEVEL CACHE SIMULATOR
########################################

# Cache block with valid and dirty bits.
class CacheBlock:
    def __init__(self, block_addr=None, valid=False, dirty=False):
        self.block_addr = block_addr  # Base address (aligned to block, i.e. lower 4 bits = 0)
        self.valid = valid
        self.dirty = dirty

# L1 Direct-Mapped Cache (2K words, 16-word blocks → 128 lines)
class DirectMappedCache:
    def __init__(self, size_words, block_size):
        self.block_size = block_size
        self.num_lines = size_words // block_size
        self.lines = [CacheBlock() for _ in range(self.num_lines)]
        self.hits = 0
        self.misses = 0
        self.accesses = 0

    def index_for_block(self, block_addr):
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

# L2 4-Way Set-Associative Cache (16K words, 16-word blocks → 1024 blocks, 256 sets with 4 ways)
class SetAssociativeCache:
    def __init__(self, size_words, block_size, ways):
        self.block_size = block_size
        total_blocks = size_words // block_size
        self.num_sets = total_blocks // ways
        self.ways = ways
        self.sets = [[CacheBlock() for _ in range(ways)] for _ in range(self.num_sets)]
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
                self.lru_counters[set_idx][j] = self.global_counter
                self.global_counter += 1
                if operation == 'write':
                    block.dirty = True
                return True
        self.misses += 1
        return False

    def insert(self, block_addr, operation='read'):
        set_idx = self.index_for_block(block_addr)
        for j, block in enumerate(self.sets[set_idx]):
            if not block.valid:
                self.sets[set_idx][j] = CacheBlock(block_addr=block_addr, valid=True, dirty=(operation=='write'))
                self.lru_counters[set_idx][j] = self.global_counter
                self.global_counter += 1
                return None
        # Otherwise, replace using LRU.
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

# Victim Cache: Fully–Associative, 4 blocks.
class VictimCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.blocks = []  # List of (block_addr, dirty)
        self.hits = 0
        self.misses = 0

    def lookup(self, block_addr):
        for i, (b_addr, dirty) in enumerate(self.blocks):
            if b_addr == block_addr:
                self.hits += 1
                victim_block = self.blocks.pop(i)
                return victim_block, True
        self.misses += 1
        return None, False

    def insert(self, block_addr, dirty):
        if len(self.blocks) >= self.capacity:
            self.blocks.pop(0)  # FIFO replacement
        self.blocks.append((block_addr, dirty))

# Write Buffer: 4 blocks.
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
        self.blocks = []
        self.flushes += 1

# Prefetch Cache: For instruction and data streams (4 blocks each, FIFO)
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

# Multi-Level Cache Simulator combining all components.
class MultiLevelCacheSimulator:
    def __init__(self):
        # L1: Direct Mapped, 2K words, 16-word blocks.
        self.L1 = DirectMappedCache(size_words=2048, block_size=16)
        # L2: 4-Way Set-Associative, 16K words, 16-word blocks.
        self.L2 = SetAssociativeCache(size_words=16384, block_size=16, ways=4)
        # Extra components:
        self.victim = VictimCache(capacity=4)
        self.write_buffer = WriteBuffer(capacity=4)
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
        self.total_accesses += 1
        # Align address to block boundary (clear lower 4 bits)
        block_addr = address & ~0xF
        # For reads, decide whether this is an instruction or data fetch.
        if operation == 'read':
            access_type = 'instruction' if random.random() < 0.5 else 'data'
        else:
            access_type = 'data'
        # Step 1: Check Prefetch Cache (only for read accesses)
        if operation == 'read':
            if access_type == 'instruction':
                if self.prefetch_instr.lookup(block_addr):
                    self.prefetch_hits += 1
                    evicted = self.L1.insert(block_addr, operation)
                    if evicted is not None:
                        evicted_block, dirty = evicted
                        if dirty:
                            self.write_buffer.insert(evicted_block)
                        else:
                            self.victim.insert(evicted_block, dirty)
                    self.prefetch_instr.insert(block_addr + 16)
                    return "Hit in Prefetch (Instr)"
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
        # Step 2: Check L1 Cache
        if self.L1.lookup(block_addr):
            self.L1_hits += 1
            if operation == 'write':
                self.L1.update_write(block_addr)
            if access_type == 'instruction':
                self.prefetch_instr.insert(block_addr + 16)
            else:
                self.prefetch_data.insert(block_addr + 16)
            return "Hit in L1"
        # Step 3: L1 Miss → Check Victim Cache
        victim_block, found = self.victim.lookup(block_addr)
        if found:
            self.victim_hits += 1
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
        # Step 4: Victim Miss → Check L2 Cache
        if self.L2.lookup(block_addr, operation):
            self.L2_hits += 1
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
        # Step 5: L2 Miss → Fetch from Main Memory
        self.main_memory_accesses += 1
        _ = self.L2.insert(block_addr, operation)
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
        return "Miss – Fetched from Memory"

    def get_performance(self):
        total_hits = self.L1_hits + self.victim_hits + self.L2_hits + self.prefetch_hits
        hit_ratio = (total_hits / self.total_accesses) * 100 if self.total_accesses > 0 else 0
        miss_ratio = (self.main_memory_accesses / self.total_accesses) * 100 if self.total_accesses > 0 else 0
        return {
            "Total Accesses": self.total_accesses,
            "L1 Hits": self.L1_hits,
            "Victim Hits": self.victim_hits,
            "L2 Hits": self.L2_hits,
            "Prefetch Hits": self.prefetch_hits,
            "Main Memory Accesses": self.main_memory_accesses,
            "Write Buffer Flushes": self.write_buffer.flushes,
            "Hit Ratio (%)": hit_ratio,
            "Miss Ratio (%)": miss_ratio
        }

    def reset(self):
        self.__init__()

########################################
# ACCESS PATTERN GENERATORS
########################################

def generate_spatial_accesses(num_accesses, start_address=0):
    # Consecutive blocks (each block is 16 words)
    return [start_address + i*16 for i in range(num_accesses)]

def generate_temporal_accesses(num_accesses, base_addresses=None, hot_prob=0.98, cold_start=10000):
    if base_addresses is None:
        base_addresses = [20*16, 21*16, 22*16, 23*16, 24*16, 25*16]
    seq = []
    cold = cold_start
    for _ in range(num_accesses):
        if random.random() < hot_prob:
            seq.append(random.choice(base_addresses))
        else:
            seq.append(cold)
            cold += 16
    return seq

def generate_random_accesses(num_accesses, memory_size_words):
    seq = []
    for _ in range(num_accesses):
        addr = random.randint(0, memory_size_words - 16)
        addr_aligned = addr - (addr % 16)
        seq.append(addr_aligned)
    return seq

########################################
# SIMULATION PARAMETERS AND EXECUTION
########################################

main_memory_size_words = 64 * 1024  # 64K words
num_accesses_list = [100, 500, 1000, 2000, 5000, 10000, 50000, 100000]
access_pattern_names = ["Spatial", "Temporal", "Random"]

# Dictionaries to store results for each simulator.
results_exp01 = { pattern: {"hit_ratio": [], "miss_ratio": []} for pattern in access_pattern_names }
results_multi = { pattern: {"hit_ratio": [], "miss_ratio": []} for pattern in access_pattern_names }

for pattern in access_pattern_names:
    for num_accesses in num_accesses_list:
        if pattern == "Spatial":
            seq = generate_spatial_accesses(num_accesses, start_address=0)
        elif pattern == "Temporal":
            seq = generate_temporal_accesses(num_accesses)
        elif pattern == "Random":
            seq = generate_random_accesses(num_accesses, main_memory_size_words)
        
        # Run Exp01 Simulation (all operations 'read')
        exp01_cache = FullyAssociativeCache(cache_size_words=2048, block_size_words=16, replacement_policy="LRU")
        exp01_cache.simulate_accesses(seq)
        perf_exp01 = exp01_cache.get_performance_metrics()
        results_exp01[pattern]["hit_ratio"].append(perf_exp01["Hit Ratio (%)"])
        results_exp01[pattern]["miss_ratio"].append(perf_exp01["Miss Ratio (%)"])
        
        # Run Extended Multi-Level Simulation
        multi_sim = MultiLevelCacheSimulator()
        for addr in seq:
            multi_sim.access(addr, "read")
        perf_multi = multi_sim.get_performance()
        results_multi[pattern]["hit_ratio"].append(perf_multi["Hit Ratio (%)"])
        results_multi[pattern]["miss_ratio"].append(perf_multi["Miss Ratio (%)"])

########################################
# PLOTTING COMPARISON GRAPHS
########################################

for pattern in access_pattern_names:
    # Hit Ratio Comparison
    plt.figure(figsize=(8,6))
    plt.plot(num_accesses_list, results_exp01[pattern]["hit_ratio"], marker='o', label="Exp01 (Single-Level)")
    plt.plot(num_accesses_list, results_multi[pattern]["hit_ratio"], marker='s', label="Extended Multi-Level")
    plt.xscale("log")
    plt.title(f"{pattern} Access Pattern - Hit Ratio Comparison")
    plt.xlabel("Number of Accesses (log scale)")
    plt.ylabel("Hit Ratio (%)")
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"comparison_{pattern.lower()}_hit_ratio.png")
    plt.close()

    # Miss Ratio Comparison
    plt.figure(figsize=(8,6))
    plt.plot(num_accesses_list, results_exp01[pattern]["miss_ratio"], marker='o', label="Exp01 (Single-Level)")
    plt.plot(num_accesses_list, results_multi[pattern]["miss_ratio"], marker='s', label="Extended Multi-Level")
    plt.xscale("log")
    plt.title(f"{pattern} Access Pattern - Miss Ratio Comparison")
    plt.xlabel("Number of Accesses (log scale)")
    plt.ylabel("Miss Ratio (%)")
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"comparison_{pattern.lower()}_miss_ratio.png")
    plt.close()

########################################
# PLOTTING DIFFERENCE GRAPHS (Exp01 - Extended)
########################################

for pattern in access_pattern_names:
    # Compute differences: (Exp01 value - Extended value)
    diff_hit = [exp - multi for exp, multi in zip(results_exp01[pattern]["hit_ratio"],
                                                   results_multi[pattern]["hit_ratio"])]
    diff_miss = [exp - multi for exp, multi in zip(results_exp01[pattern]["miss_ratio"],
                                                    results_multi[pattern]["miss_ratio"])]
    
    plt.figure(figsize=(8,6))
    plt.plot(num_accesses_list, diff_hit, marker='o', linestyle='-', label="Hit Ratio Difference")
    plt.plot(num_accesses_list, diff_miss, marker='s', linestyle='--', label="Miss Ratio Difference")
    plt.xscale("log")
    plt.title(f"Difference (Exp01 - Extended) in Hit/Miss Ratios\n{pattern} Access Pattern")
    plt.xlabel("Number of Accesses (log scale)")
    plt.ylabel("Difference (%)")
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"difference_{pattern.lower()}.png")
    plt.close()

########################################
# PRINT SUMMARY OF RESULTS TO TERMINAL
########################################

print("\n--- Simulation Comparison Summary ---")
for pattern in access_pattern_names:
    print(f"\nAccess Pattern: {pattern}")
    print("Accesses\tExp01 Hit%\tMulti-Level Hit%\tExp01 Miss%\tMulti-Level Miss%")
    for i, num in enumerate(num_accesses_list):
        exp01_hit = results_exp01[pattern]["hit_ratio"][i]
        multi_hit = results_multi[pattern]["hit_ratio"][i]
        exp01_miss = results_exp01[pattern]["miss_ratio"][i]
        multi_miss = results_multi[pattern]["miss_ratio"][i]
        print(f"{num:9}\t{exp01_hit:10.2f}\t{multi_hit:17.2f}\t{exp01_miss:10.2f}\t{multi_miss:16.2f}")
