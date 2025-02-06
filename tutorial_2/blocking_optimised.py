import numpy as np

# Read matrices from text files
def read_matrix_from_file(filename):
    with open(filename, "r") as f:
        matrix = [list(map(int, line.split())) for line in f.readlines()]
    return np.array(matrix)

# Load matrices A and B from text files
A = read_matrix_from_file("matrix_A.txt")
B = read_matrix_from_file("matrix_B.txt")

# Initialize result matrices
C_optimized = np.zeros((A.shape[0], B.shape[1]))

# Block size for optimized multiplication
block_size = 2  

# Optimized matrix multiplication with blocking
for i in range(0, len(A), block_size):
    for j in range(0, len(B[0]), block_size):
        for k in range(0, len(B), block_size):
            # Compute the block multiplication
            for ii in range(i, min(i + block_size, len(A))):
                for jj in range(j, min(j + block_size, len(B[0]))):
                    for kk in range(k, min(k + block_size, len(B))):
                        C_optimized[ii][jj] += A[ii][kk] * B[kk][jj]


# Print results
print("Matrix A:")
print(A)
print("Matrix B:")
print(B)

print("Result Matrix C (Optimized with Blocking):")
print(C_optimized)
