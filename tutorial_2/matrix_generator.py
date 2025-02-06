import numpy as np

# User input for matrix size
N = 30

# Generate a random NxN matrix
A = np.random.randint(1, 10, (N, N))
B = np.random.randint(1, 10, (N, N))

# Save matrices to a text file
with open("matrix_A.txt", "w") as f:
    for row in A:
        f.write(' '.join(map(str, row)) + '\n')

with open("matrix_B.txt", "w") as f:
    for row in B:
        f.write(' '.join(map(str, row)) + '\n')

print("Matrices A and B have been saved to 'matrix_A.txt' and 'matrix_B.txt'")
