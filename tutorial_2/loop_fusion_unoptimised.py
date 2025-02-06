# Unoptimized version: separate loops
matrix_a = [[1, 2, 3], [4, 5, 6]]
matrix_b = [[7, 8, 9], [10, 11, 12]]

# First loop - Multiply elements of matrix_a by 2
for i in range(len(matrix_a)):
    for j in range(len(matrix_a[i])):
        matrix_a[i][j] *= 2

# Second loop - Add elements of matrix_b to matrix_a
for i in range(len(matrix_b)):
    for j in range(len(matrix_b[i])):
        matrix_a[i][j] += matrix_b[i][j]

print("Unoptimized Matrix_a:", matrix_a)
