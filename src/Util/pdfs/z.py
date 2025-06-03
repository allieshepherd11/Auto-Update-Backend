import pandas as pd
import Levenshtein

def fuzzy_match_self(s1, s2, max_distance=2):
    m, n = len(s1), len(s2)
    # Initialize DP table and operation pointer table.
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    ptr = [[None] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
        if i > 0:
            ptr[i][0] = 'delete'
    for j in range(n + 1):
        dp[0][j] = j
        if j > 0:
            ptr[0][j] = 'insert'
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
                ptr[i][j] = 'match'
            else:
                substitution = dp[i - 1][j - 1] + 1
                deletion = dp[i - 1][j] + 1
                insertion = dp[i][j - 1] + 1
                min_cost = min(substitution, deletion, insertion)
                dp[i][j] = min_cost
                if min_cost == substitution:
                    ptr[i][j] = 'substitute'
                elif min_cost == deletion:
                    ptr[i][j] = 'delete'
                else:
                    ptr[i][j] = 'insert'
    
    # If overall edit distance exceeds our tolerance, no match.
    if dp[m][n] > max_distance:
        return False

    # Backtrack to recover one optimal sequence of operations.
    operations = []
    i, j = m, n
    while i > 0 or j > 0:
        op = ptr[i][j]
        if op == 'match':
            i -= 1
            j -= 1
        elif op == 'substitute':
            operations.append(('substitute', s1[i - 1], s2[j - 1]))
            i -= 1
            j -= 1
        elif op == 'delete':
            operations.append(('delete', s1[i - 1]))
            i -= 1
        elif op == 'insert':
            operations.append(('insert', s2[j - 1]))
            j -= 1
    operations.reverse()  # Now in order from beginning to end.

    # Check each operation: if any mismatched character is a digit, return False.
    for op in operations:
        if op[0] == 'substitute':
            # If either char is a digit (and the characters differ by definition)
            if op[1].isdigit() or op[2].isdigit():
                return False
        elif op[0] == 'delete':
            if op[1].isdigit():
                return False
        elif op[0] == 'insert':
            if op[1].isdigit():
                return False

    return True

def fuzzy_match(s1, s2, max_distance=2):
    return Levenshtein.distance(s1, s2) <= max_distance

df_jr = pd.read_csv('roe.csv')
df_ptn = pd.read_csv('ptn_summary.csv')

print(df_jr)
print(df_ptn)
ptn_wells = [w.replace(' ','').replace('#','').strip() for w in df_ptn['Well Name'].fillna('').tolist()]
jr_wells = [w.replace(' ','').replace('#','').strip() for w in df_jr['Well Name'].fillna('').tolist()]


matches = list()
for w in ptn_wells: 
    for wjr in jr_wells:
        max_dist = 4 if len(w) > 8 else 1

        if fuzzy_match_self(w,wjr,max_dist):
            print(w,wjr)
            matches.append((w,wjr))

print(len(matches))
print(len(ptn_wells))