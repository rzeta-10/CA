import matplotlib
matplotlib.use('Agg')  # *** ADDED: Use Agg backend to avoid GTK issues ***
import matplotlib.pyplot as plt
import random
from collections import deque

class CacheLine:
    def __init__(self, tag=None, valid=False, dirty=False):
        self.tag = tag
        self.valid = valid
        self.dirty = dirty
        self.lru_counter = 0 # For LRU replacement

class FullyAssociativeCache:
    def __init__(self, cache_size_words, block_size_words, replacement_policy='FIFO'):
        self.cache_size_lines = cache_size_words // block_size_words
        self.block_size_words = block_size_words
        self.replacement_policy = replacement_policy
        self.cache = [CacheLine() for _ in range(self.cache_size_lines)]
        self.cache_lines_used = 0
        self.misses = 0
        self.searches = 0
        self.hits = 0
        self.lru_counter = 0 # Global LRU counter

    def address_breakdown(self, address):
        """Breaks down the address into tag and block offset."""
        block_offset_bits = 4  # log2(16) as block size is 16 words
        block_offset_mask = (1 << block_offset_bits) - 1
        block_offset = address & block_offset_mask
        tag = address >> block_offset_bits
        return tag

    def search_cache(self, tag, access_index):
        """Searches the cache for a given tag. Returns True on hit, False on miss."""
        self.searches += 1
        for i in range(len(self.cache)):
            line = self.cache[i]
            if line.valid and line.tag == tag:
                self.hits += 1
                if self.replacement_policy == 'LRU':
                    self.cache[i].lru_counter = self.lru_counter
                    self.lru_counter += 1
                return True  # Cache hit
        return False         # Cache miss

    def add_to_cache(self, tag):
        """Adds a tag to the cache based on the replacement policy."""
        # First, try to find an invalid line
        for i in range(self.cache_size_lines):
            if not self.cache[i].valid:
                self.cache[i] = CacheLine(tag=tag, valid=True, dirty=False)
                if self.replacement_policy == 'LRU':
                    self.cache[i].lru_counter = self.lru_counter
                    self.lru_counter += 1
                self.cache_lines_used += 1
                return

        # Cache is full, implement replacement policy
        if self.replacement_policy == 'FIFO':
            self._replace_fifo(tag)
        elif self.replacement_policy == 'LRU':
            self._replace_lru(tag)
        elif self.replacement_policy == 'Random':
            self._replace_random(tag)

    def _replace_fifo(self, tag):
        """FIFO replacement policy."""
        replaced_line = self.cache.pop(0) # Remove the first line (FIFO)
        if replaced_line.dirty:
            pass # Simulate write-back if needed

        self.cache.append(CacheLine(tag=tag, valid=True, dirty=False)) # Add new line at the end
        if self.replacement_policy == 'LRU':
            self.cache[-1].lru_counter = self.lru_counter
            self.lru_counter += 1


    def _replace_lru(self, tag):
        """LRU replacement policy."""
        lru_index = 0
        min_lru_counter = self.cache[0].lru_counter
        for i in range(1, self.cache_size_lines):
            if self.cache[i].lru_counter < min_lru_counter:
                min_lru_counter = self.cache[i].lru_counter
                lru_index = i

        if self.cache[lru_index].dirty:
            pass # Simulate write-back if needed

        self.cache[lru_index] = CacheLine(tag=tag, valid=True, dirty=False)
        self.cache[lru_index].lru_counter = self.lru_counter
        self.lru_counter += 1


    def _replace_random(self, tag):
        """Random replacement policy."""
        replace_index = random.randint(0, self.cache_size_lines - 1)
        if self.cache[replace_index].dirty:
            pass # Simulate write-back if needed
        self.cache[replace_index] = CacheLine(tag=tag, valid=True, dirty=False)
        if self.replacement_policy == 'LRU': # although it is random policy , but still update lru counter to maintain consistency in class
            self.cache[replace_index].lru_counter = self.lru_counter
            self.lru_counter += 1


    def access_memory(self, address, access_index, operation_type='read'):
        """Simulates a memory access."""
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
        """Simulates a sequence of memory accesses."""
        results = []
        if operation_sequence is None:
            operation_sequence = ['read'] * len(access_sequence)
        for i in range(len(access_sequence)):
            address = access_sequence[i]
            operation = operation_sequence[i]
            result = self.access_memory(address, i, operation) # Pass access index for LRU
            results.append((address, operation, result))
        return results

    def get_performance_metrics(self):
        """Calculates and returns performance metrics."""
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
        """Resets performance metrics for a new simulation run."""
        self.misses = 0
        self.searches = 0
        self.hits = 0
        self.lru_counter = 0
        self.cache = [CacheLine() for _ in range(self.cache_size_lines)] # reset cache lines also
        self.cache_lines_used = 0

# --- Access Pattern Generators ---
def generate_spatial_accesses(num_accesses, start_address=0, step=1):
    return list(range(start_address, start_address + num_accesses * step, step))

def generate_temporal_accesses(num_accesses, base_addresses=[20, 21, 22], repeat_pattern=[1, 1, 1, 2, 2, 3]):
    access_sequence = []
    pattern_len = len(repeat_pattern)
    base_len = len(base_addresses)
    for i in range(num_accesses):
        base_index = repeat_pattern[i % pattern_len] - 1 # -1 to adjust index to start from 0
        access_sequence.append(base_addresses[base_index % base_len]) # Modulo for base address selection
    return access_sequence


def generate_random_accesses(num_accesses, memory_size_words):
    return [random.randint(0, memory_size_words - 1) for _ in range(num_accesses)]

# --- Simulation Parameters ---
main_memory_size_words = 64 * 1024
cache_size_words = 2 * 1024
block_size_words = 16
num_accesses = 1000
replacement_policies = ['FIFO', 'LRU', 'Random']
access_pattern_names = ['Spatial', 'Temporal', 'Random']
access_patterns = {
    'Spatial': generate_spatial_accesses(num_accesses),
    'Temporal': generate_temporal_accesses(num_accesses),
    'Random': generate_random_accesses(num_accesses, main_memory_size_words)
}

results_data = {}

# --- Run Simulations and Collect Data ---
for policy_name in replacement_policies:
    results_data[policy_name] = {}
    for pattern_name in access_pattern_names:
        cache = FullyAssociativeCache(cache_size_words, block_size_words, replacement_policy=policy_name)
        access_sequence = access_patterns[pattern_name]
        cache.simulate_accesses(access_sequence)
        metrics = cache.get_performance_metrics()
        results_data[policy_name][pattern_name] = metrics
        results_data[policy_name][pattern_name]['access_sequence_length'] = len(access_sequence)


# --- Print Terminal Results ---
print("--- Cache Performance Results ---")
print(f"Cache Size: {cache_size_words} words, Block Size: {block_size_words} words, Accesses: {num_accesses}\n")

for policy_name in replacement_policies:
    print(f"Replacement Policy: {policy_name}")
    for pattern_name in access_pattern_names:
        metrics = results_data[policy_name][pattern_name]
        print(f"  Access Pattern: {pattern_name}")
        print(f"    Searches: {metrics['searches']}")
        print(f"    Misses: {metrics['misses']}")
        print(f"    Hits: {metrics['hits']}")
        print(f"    Hit Ratio: {metrics['hit_ratio']:.2f}%")
        print(f"    Miss Ratio: {metrics['miss_ratio']:.2f}%")
    print("-" * 30)

# --- Plotting ---
bar_width = 0.25
x_positions = range(len(access_pattern_names))

fig, ax = plt.subplots(figsize=(10, 6))

for i, policy_name in enumerate(replacement_policies):
    hit_ratios = [results_data[policy_name][pattern_name]['hit_ratio'] for pattern_name in access_pattern_names]
    position = [x + bar_width * i for x in x_positions]
    ax.bar(position, hit_ratios, bar_width, label=policy_name)

ax.set_xlabel("Access Patterns")
ax.set_ylabel("Hit Ratio (%)")
ax.set_title("Cache Hit Ratio Comparison by Replacement Policy and Access Pattern")
ax.set_xticks([x + bar_width for x in x_positions])
ax.set_xticklabels(access_pattern_names)
ax.legend()
ax.grid(axis='y', linestyle='--')
plt.tight_layout()

# Save as PNG
plt.savefig('cache_hit_ratio_comparison.png')
# Save as JPEG
# plt.savefig('cache_hit_ratio_comparison.jpeg') # or 'cache_hit_ratio_comparison.jpg'

plt.show()


fig, ax = plt.subplots(figsize=(10, 6))

for i, policy_name in enumerate(replacement_policies):
    miss_ratios = [results_data[policy_name][pattern_name]['miss_ratio'] for pattern_name in access_pattern_names]
    position = [x + bar_width * i for x in x_positions]
    ax.bar(position, miss_ratios, bar_width, label=policy_name)

ax.set_xlabel("Access Patterns")
ax.set_ylabel("Miss Ratio (%)")
ax.set_title("Cache Miss Ratio Comparison by Replacement Policy and Access Pattern")
ax.set_xticks([x + bar_width for x in x_positions])
ax.set_xticklabels(access_pattern_names)
ax.legend()
ax.grid(axis='y', linestyle='--')
plt.tight_layout()

# Save as PNG
plt.savefig('cache_miss_ratio_comparison.png')
# Save as JPEG
# plt.savefig('cache_miss_ratio_comparison.jpeg') # or 'cache_miss_ratio_comparison.jpg'

plt.show()