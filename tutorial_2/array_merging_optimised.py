import random

# Define a structure-like class
class Merge:
    def __init__(self, val, key):
        self.val = val
        self.key = key

# Generate two large arrays of random integers
val = [random.randint(1, 100) for _ in range(1000000)]
key = [random.randint(1, 100) for _ in range(1000000)]

# Merge the arrays into a list of objects
merged_array = [Merge(v, k) for v, k in zip(val, key)]

# Perform element-wise summation using the merged array
result = [item.val + item.key for item in merged_array]

print(result[:10])


