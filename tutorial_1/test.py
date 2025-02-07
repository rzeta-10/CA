import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non-interactive plotting
import matplotlib.pyplot as plt
import random

# --- Cache Simulator Classes ---
class CacheLine:
    def __init__(self, tag=None, valid=False, dirty=False):
        self.tag = tag
        self.valid = valid
        self.dirty = dirty
        self.lru_counter = 0  # For LRU replacement

class FullyAssociativeCache:
    def __init__(self, cache_size_words, block_size_words, replacement_policy='FIFO'):
        self.cache_size_lines = cache_size_words // block_size_words
        self.block_size_words = block_size_words
        self.replacement_policy = replacement_policy
        # For FIFO and Random we maintain a list; for LRU the lru_counter is used.
        self.cache = [CacheLine() for _ in range(self.cache_size_lines)]
        self.cache_lines_used = 0
        self.misses = 0
        self.searches = 0
        self.hits = 0
        self.lru_counter = 0  # Global counter for LRU

    def address_breakdown(self, address):
        """Break down the address into tag (using 4 bits for the offset since block size is 16 words)."""
        block_offset_bits = 4  # log2(16)
        tag = address >> block_offset_bits
        return tag

    def search_cache(self, tag, access_index):
        """Search for the tag in cache. Update LRU counter if needed."""
        self.searches += 1
        for i in range(len(self.cache)):
            line = self.cache[i]
            if line.valid and line.tag == tag:
                self.hits += 1
                if self.replacement_policy == 'LRU':
                    self.cache[i].lru_counter = self.lru_counter
                    self.lru_counter += 1
                return True  # Hit
        return False  # Miss

    def add_to_cache(self, tag):
        """Insert the tag into the cache; if full, replace an existing line."""
        # Look for an empty (invalid) line first.
        for i in range(self.cache_size_lines):
            if not self.cache[i].valid:
                self.cache[i] = CacheLine(tag=tag, valid=True, dirty=False)
                if self.replacement_policy == 'LRU':
                    self.cache[i].lru_counter = self.lru_counter
                    self.lru_counter += 1
                self.cache_lines_used += 1
                return

        # Otherwise, apply the chosen replacement policy.
        if self.replacement_policy == 'FIFO':
            self._replace_fifo(tag)
        elif self.replacement_policy == 'LRU':
            self._replace_lru(tag)
        elif self.replacement_policy == 'Random':
            self._replace_random(tag)

    def _replace_fifo(self, tag):
        """FIFO replacement: remove the first cache line and append a new one."""
        replaced_line = self.cache.pop(0)
        if replaced_line.dirty:
            pass  # Write-back simulation if needed.
        self.cache.append(CacheLine(tag=tag, valid=True, dirty=False))
        if self.replacement_policy == 'LRU':  # Not expected to run, but for consistency.
            self.cache[-1].lru_counter = self.lru_counter
            self.lru_counter += 1

    def _replace_lru(self, tag):
        """LRU replacement: replace the cache line with the smallest LRU counter."""
        lru_index = 0
        min_lru_counter = self.cache[0].lru_counter
        for i in range(1, self.cache_size_lines):
            if self.cache[i].lru_counter < min_lru_counter:
                min_lru_counter = self.cache[i].lru_counter
                lru_index = i
        if self.cache[lru_index].dirty:
            pass  # Write-back simulation if needed.
        self.cache[lru_index] = CacheLine(tag=tag, valid=True, dirty=False)
        self.cache[lru_index].lru_counter = self.lru_counter
        self.lru_counter += 1

    def _replace_random(self, tag):
        """Random replacement: randomly choose a cache line to replace."""
        replace_index = random.randint(0, self.cache_size_lines - 1)
        if self.cache[replace_index].dirty:
            pass  # Write-back simulation if needed.
        self.cache[replace_index] = CacheLine(tag=tag, valid=True, dirty=False)
        if self.replacement_policy == 'LRU':
            self.cache[replace_index].lru_counter = self.lru_counter
            self.lru_counter += 1

    def access_memory(self, address, access_index, operation_type='read'):
        """Simulate a memory access: check cache and update accordingly."""
        tag = self.address_breakdown(address)
        if self.search_cache(tag, access_index):
            if operation_type == 'write':
                for line in self.cache:
                    if line.valid and line.tag == tag:
                        line.dirty = True
                        break
            return "Hit"
        else:
            self.misses += 1
            self.add_to_cache(tag)
            return "Miss"

    def simulate_accesses(self, access_sequence, operation_sequence=None):
        """Run a series of accesses and record results."""
        results = []
        if operation_sequence is None:
            operation_sequence = ['read'] * len(access_sequence)
        for i in range(len(access_sequence)):
            address = access_sequence[i]
            operation = operation_sequence[i]
            result = self.access_memory(address, i, operation)
            results.append((address, operation, result))
        return results

    def get_performance_metrics(self):
        """Return performance metrics including hit and miss ratios."""
        searches = self.searches
        misses = self.misses
        hits = self.hits
        hit_ratio = (hits / searches) * 100 if searches else 0
        miss_ratio = (misses / searches) * 100 if searches else 0
        return {
            "searches": searches,
            "misses": misses,
            "hits": hits,
            "hit_ratio": hit_ratio,
            "miss_ratio": miss_ratio
        }

    def reset_metrics(self):
        """Reset metrics and cache state for a new simulation run."""
        self.misses = 0
        self.searches = 0
        self.hits = 0
        self.lru_counter = 0
        self.cache = [CacheLine() for _ in range(self.cache_size_lines)]
        self.cache_lines_used = 0

# --- Access Pattern Generators ---
def generate_spatial_accesses(num_accesses, start_address=0, step=1):
    """Generate a sequence of spatially contiguous addresses."""
    return list(range(start_address, start_address + num_accesses * step, step))

def generate_temporal_accesses(num_accesses, base_addresses=[20, 21, 22, 23, 24, 25],
                               hot_prob=0.98, cold_start=10000):
    """
    Generate a temporal access sequence that mixes frequent (hot) accesses with occasional (cold) ones.
    With probability hot_prob (default 98%), one of the base (hot) addresses is chosen.
    With probability (1 - hot_prob) (default 2%), a new (cold) address is generated.
    """
    access_sequence = []
    cold_addr = cold_start
    for i in range(num_accesses):
        if random.random() < hot_prob:
            access_sequence.append(random.choice(base_addresses))
        else:
            access_sequence.append(cold_addr)
            cold_addr += 1
    return access_sequence

def generate_random_accesses(num_accesses, memory_size_words):
    """Generate a sequence of random addresses."""
    return [random.randint(0, memory_size_words - 1) for _ in range(num_accesses)]

# --- Simulation Parameters ---
main_memory_size_words = 64 * 1024
cache_size_words = 2 * 1024
block_size_words = 16

replacement_policies = ['FIFO', 'LRU', 'Random']
access_pattern_names = ['Spatial', 'Temporal', 'Random']
# Different numbers of accesses to simulate:
num_accesses_list = [100, 500, 1000, 2000, 5000, 10000, 50000, 100000]

# --- Run Simulations for Each Case ---
# We'll store the hit and miss ratios for each access pattern and replacement policy.
results_by_pattern = {
    pattern: {
        policy: {'hit_ratio': [], 'miss_ratio': []}
        for policy in replacement_policies
    }
    for pattern in access_pattern_names
}

# Also store full details for printing to the terminal.
details_by_pattern = {
    pattern: {
        policy: []
        for policy in replacement_policies
    }
    for pattern in access_pattern_names
}

for pattern in access_pattern_names:
    for num_accesses in num_accesses_list:
        # Generate the access sequence based on the chosen pattern.
        if pattern == 'Spatial':
            access_sequence = generate_spatial_accesses(num_accesses)
        elif pattern == 'Temporal':
            # For the temporal pattern we use our modified generator.
            # Warm up the cache with the hot set before simulation.
            hot_set = [20, 21, 22, 23, 24, 25]
            access_sequence = generate_temporal_accesses(num_accesses, base_addresses=hot_set,
                                                           hot_prob=0.98, cold_start=10000)
        elif pattern == 'Random':
            access_sequence = generate_random_accesses(num_accesses, main_memory_size_words)
        # For each replacement policy, simulate and record the metrics.
        for policy in replacement_policies:
            cache = FullyAssociativeCache(cache_size_words, block_size_words, replacement_policy=policy)
            if pattern == 'Temporal':
                # Warm up the cache with several passes over the hot addresses.
                hot_set = [20, 21, 22, 23, 24, 25]
                warmup_sequence = hot_set * 10  # Repeat a few times to load hot_set into cache
                cache.simulate_accesses(warmup_sequence)
                cache.reset_metrics()
            cache.simulate_accesses(access_sequence)
            metrics = cache.get_performance_metrics()
            results_by_pattern[pattern][policy]['hit_ratio'].append(metrics['hit_ratio'])
            results_by_pattern[pattern][policy]['miss_ratio'].append(metrics['miss_ratio'])
            details_by_pattern[pattern][policy].append(metrics)

# --- Plotting Graphs Separately ---
# For each access pattern, we now generate two separate figures:
# one for the hit ratio and one for the miss ratio.
for pattern in access_pattern_names:
    # Hit Ratio Graph for this pattern
    plt.figure(figsize=(8, 6))
    for policy in replacement_policies:
        hit_ratios = results_by_pattern[pattern][policy]['hit_ratio']
        plt.plot(num_accesses_list, hit_ratios, marker='o', label=policy)
    plt.xscale('log')
    plt.title(f'{pattern} Access Pattern - Hit Ratio')
    plt.xlabel('Number of Accesses (log scale)')
    plt.ylabel('Hit Ratio (%)')
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'cache_performance_{pattern.lower()}_hit_ratio.png')
    plt.close()

    # Miss Ratio Graph for this pattern
    plt.figure(figsize=(8, 6))
    for policy in replacement_policies:
        miss_ratios = results_by_pattern[pattern][policy]['miss_ratio']
        plt.plot(num_accesses_list, miss_ratios, marker='o', label=policy)
    plt.xscale('log')
    plt.title(f'{pattern} Access Pattern - Miss Ratio')
    plt.xlabel('Number of Accesses (log scale)')
    plt.ylabel('Miss Ratio (%)')
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'cache_performance_{pattern.lower()}_miss_ratio.png')
    plt.close()

# --- Print Details to Terminal ---
print("\n--- Detailed Cache Performance Results ---")
print(f"Cache Size: {cache_size_words} words, Block Size: {block_size_words} words")
print("-------------------------------------------------\n")

for policy in replacement_policies:
    print(f"Replacement Policy: {policy}")
    for pattern in access_pattern_names:
        print(f"  Access Pattern: {pattern}")
        for i, num_accesses in enumerate(num_accesses_list):
            metrics = details_by_pattern[pattern][policy][i]
            print(f"    Number of Accesses: {num_accesses}")
            print(f"      Searches: {metrics['searches']}")
            print(f"      Misses: {metrics['misses']}")
            print(f"      Hits: {metrics['hits']}")
            print(f"      Hit Ratio: {metrics['hit_ratio']:.2f}%")
            print(f"      Miss Ratio: {metrics['miss_ratio']:.2f}%")
        print("-" * 40)
    print("=" * 50)
