# cache_simulator.py
import random

class FullyAssociativeCache:
    def __init__(self, capacity, replacement_policy='LRU'):
        self.capacity = capacity
        self.cache = []  # list of block numbers (order matters, e.g., for LRU)
        self.replacement_policy = replacement_policy.upper()
        self.hit_count = 0
        self.miss_count = 0
        self.total_comparisons = 0

    def access(self, block_number):
        """
        Simulate an access to the cache with a given block number.
        Returns the number of comparisons made during the search.
        """
        comparisons = 0
        hit_index = None

        # Linear search through the cache
        for i, blk in enumerate(self.cache):
            comparisons += 1
            if blk == block_number:
                hit_index = i
                break

        if hit_index is not None:
            # Cache hit: For LRU, update ordering by moving block to front.
            if self.replacement_policy == 'LRU':
                self.cache.pop(hit_index)
                self.cache.insert(0, block_number)
            self.hit_count += 1
        else:
            # Cache miss: Insert block, replacing one if necessary.
            if len(self.cache) >= self.capacity:
                self.replace_block(block_number)
            else:
                self.cache.insert(0, block_number)
            self.miss_count += 1

        self.total_comparisons += comparisons
        return comparisons

    def replace_block(self, block_number):
        """
        Replace a block in the cache based on the replacement policy.
        """
        if self.replacement_policy == 'LRU':
            # Remove least recently used (the last element)
            self.cache.pop()
        elif self.replacement_policy == 'FIFO':
            # Remove the oldest block (simulate FIFO by removing the last element)
            self.cache.pop()
        elif self.replacement_policy == 'RANDOM':
            # Remove a random block
            random_index = random.randint(0, len(self.cache) - 1)
            self.cache.pop(random_index)
        else:
            # Default: LRU
            self.cache.pop()
        self.cache.insert(0, block_number)

    def reset(self):
        """
        Reset cache contents and statistics.
        """
        self.cache = []
        self.hit_count = 0
        self.miss_count = 0
        self.total_comparisons = 0

    def get_stats(self):
        total_accesses = self.hit_count + self.miss_count
        avg = self.total_comparisons / total_accesses if total_accesses > 0 else 0
        return {
            'hits': self.hit_count,
            'misses': self.miss_count,
            'total_comparisons': self.total_comparisons,
            'average_comparisons': avg
        }

    def __str__(self):
        stats = self.get_stats()
        return (f"Hits: {stats['hits']} | Misses: {stats['misses']} | "
                f"Total Comparisons: {stats['total_comparisons']} | "
                f"Avg Comparisons: {stats['average_comparisons']:.2f}")
