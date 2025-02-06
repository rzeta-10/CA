# Generate a 2D array (matrix) with random values
rows, cols = 1000, 1000
matrix = [[i + j for j in range(cols)] for i in range(rows)]

# Optimized loop: Iterate column-wise, then row-wise
result = 0
for j in range(cols):  # Outer loop for columns
    for i in range(rows):  # Inner loop for rows
        result += matrix[i][j]

print(result)