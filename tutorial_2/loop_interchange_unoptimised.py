# Generate a 2D array (matrix) with random values
rows, cols = 1000, 1000
matrix = [[i + j for j in range(cols)] for i in range(rows)]  #i+j to compare that execution value of loops is same for fair comparison

# Unoptimized loop: Iterate row-wise, then column-wise
result = 0
for i in range(rows):  # Outer loop for rows
    for j in range(cols):  # Inner loop for columns
        result += matrix[i][j]

print(result)
