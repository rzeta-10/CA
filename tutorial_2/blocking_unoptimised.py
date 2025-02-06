import numpy as np

# Read matrices from text files
def read_matrix_from_file(filename):
    with open(filename, "r") as f:
        matrix = [list(map(int, line.split())) for line in f.readlines()]
    return np.array(matrix)

# Load matrices A and B from text files
A = read_matrix_from_file("matrix_A.txt")
B = read_matrix_from_file("matrix_B.txt")

C_unoptimized = np.zeros((A.shape[0], B.shape[1]))


# Unoptimized matrix multiplication (no blocking)
for i in range(len(A)):
    for j in range(len(B[0])):
        for k in range(len(B)):
            C_unoptimized[i][j] += A[i][k] * B[k][j]

# Print results
print("Matrix A:")
print(A)
print("Matrix B:")
print(B)


print("Result Matrix C (Unoptimized):")
print(C_unoptimized)
