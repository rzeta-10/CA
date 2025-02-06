import random

# Generate two large arrays of random integers
val = [random.randint(1, 100) for _ in range(1000000)]
key = [random.randint(1, 100) for _ in range(1000000)]


# Perform element-wise summation
result = [val[i] + key[i] for i in range(len(val))]

print(result[:10]) 
