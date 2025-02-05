import random

class FullyAssociativeCache:
    def __init__(self, capacity, replacement_policy, block_size=16):
        self.capacity = capacity
        self.replacement_policy = replacement_policy
        self.block_size = block_size
        self.cache = []
        self.cache_set = set()  # To quickly check if a block is in the cache
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_comparisons': 0,
            'average_comparisons': 0.0
        }

    def access(self, block_number):
        self.stats['total_comparisons'] += 1
        if block_number in self.cache_set:
            self.stats['hits'] += 1
            # Move the block to the end to simulate LRU
            if self.replacement_policy == "LRU":
                self.cache.remove(block_number)
                self.cache.append(block_number)
        else:
            self.stats['misses'] += 1
            if len(self.cache_set) >= self.capacity:
                self.evict()
            self.cache_set.add(block_number)
            self.cache.append(block_number)

    def evict(self):
        if self.replacement_policy == "LRU":
            # Implement LRU eviction logic
            evicted_block = self.cache.pop(0)
        elif self.replacement_policy == "FIFO":
            # Implement FIFO eviction logic
            evicted_block = self.cache.pop(0)
        elif self.replacement_policy == "Random":
            # Implement Random eviction logic
            evicted_block = self.cache.pop(random.randint(0, len(self.cache) - 1))
        self.cache_set.remove(evicted_block)

    def get_stats(self):
        # Calculate average comparisons
        if self.stats['hits'] + self.stats['misses'] > 0:
            self.stats['average_comparisons'] = self.stats['total_comparisons'] / (self.stats['hits'] + self.stats['misses'])
        return self.stats