# Unoptimized Matrix Multiplication (no blocking)
import numpy as np

# Random 3x3 matrices
A = np.random.randint(1, 10, (3, 3))
B = np.random.randint(1, 10, (3, 3))

# Result matrix initialization
C = np.zeros((3, 3))

# Triple nested loop (unoptimized)
for i in range(len(A)):
    for j in range(len(B[0])):
        for k in range(len(B)):
            C[i][j] += A[i][k] * B[k][j]

print("Matrix A:")
print(A)
print("Matrix B:")
print(B)
print("Result Matrix C (Unoptimized):")
print(C)
