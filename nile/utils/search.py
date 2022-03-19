# Fuzzy search for installing and for future GUI searching


def calculate_distance(s, t):
    # Initialize matrix of zeros
    rows = len(s) + 1
    cols = len(t) + 1
    distance = [[0 for j in range(cols)] for i in range(rows)]

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1, cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row - 1] == t[col - 1]:
                cost = 0  # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
            else:
                cost = 2
            distance[row][col] = min(
                distance[row - 1][col] + 1,  # Cost of deletions
                distance[row][col - 1] + 1,  # Cost of insertions
                distance[row - 1][col - 1] + cost,
            )  # Cost of substitutions
    Ratio = ((len(s) + len(t)) - distance[row][col]) / (len(s) + len(t))
    return Ratio
