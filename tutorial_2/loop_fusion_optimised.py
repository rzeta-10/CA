# Optimized version: single nested loop
matrix_a = [[1, 2, 3], [4, 5, 6]]
matrix_b = [[7, 8, 9], [10, 11, 12]]

# Single nested loop - Both operations combined
for i in range(len(matrix_a)):
    for j in range(len(matrix_a[i])):
        matrix_a[i][j] = (matrix_a[i][j] * 2) + matrix_b[i][j]

print("Optimized Matrix_a:", matrix_a)
