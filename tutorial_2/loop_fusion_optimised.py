import numpy as np

def read_matrix_from_file(filename):
    with open(filename, "r") as f:
        matrix = [list(map(int, line.split())) for line in f.readlines()]
    return np.array(matrix)
# Optimized version: single nested loop
matrix_a = read_matrix_from_file("matrix_A.txt")
matrix_b = read_matrix_from_file("matrix_B.txt")

# Single nested loop - Both operations combined
for i in range(len(matrix_a)):
    for j in range(len(matrix_a[i])):
        matrix_a[i][j] = (matrix_a[i][j] * 2) + matrix_b[i][j]

print("Optimized Matrix_a:", matrix_a)
