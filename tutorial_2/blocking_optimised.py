# Optimized Matrix Multiplication (with Blocking)
import numpy as np

# Random 3x3 matrices (For simplicity, 3x3 is used, but blocking is useful for larger matrices)
A = np.random.randint(1, 10, (3, 3))
B = np.random.randint(1, 10, (3, 3))

# Result matrix initialization
C = np.zeros((3, 3))

# Block size (For large matrices, this would be larger)
block_size = 2  # You can adjust block size based on the matrix size and cache

# Optimized matrix multiplication with blocking
for i in range(0, len(A), block_size):
    for j in range(0, len(B[0]), block_size):
        for k in range(0, len(B), block_size):
            # Compute the block multiplication
            for ii in range(i, min(i + block_size, len(A))):
                for jj in range(j, min(j + block_size, len(B[0]))):
                    for kk in range(k, min(k + block_size, len(B))):
                        C[ii][jj] += A[ii][kk] * B[kk][jj]

print("Matrix A:")
print(A)
print("Matrix B:")
print(B)
print("Result Matrix C (Optimized with Blocking):")
print(C)
