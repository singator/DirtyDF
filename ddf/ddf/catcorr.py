import random
import numpy as np
import pandas as pd

"""
This python file manages the change in mutual information for two categorical variables. Used in the CatCorr Stainer.
"""

def new_mutual_cols(df, max_n = 5000, min_inf = 0.5):
    df = df.copy()

    # Record label names
    y_name, x_name = df.columns
    # Get contingency table
    table = pd.crosstab(df[y_name],
                        df[x_name],
                        margins=False)
    x_index = table.index
    y_index = table.columns
    # Convert table to numpy array
    table = table.to_numpy()
    old_mut = MutInf(table)
    # Record old row & column sums
    rowsum_old, colsum_old = get_row_col_sums(table)

    # Perform simulated annealing
    table, new_mut = simul_anneal(table, max_n=max_n, min_inf=min_inf)
    # New row & columns sums
    rowsum_new, colsum_new = get_row_col_sums(table)

    if not (np.array_equal(rowsum_old, rowsum_new) and np.array_equal(colsum_old, colsum_new)):
        raise Exception("Marginals not the same")

    # Convert to dataframe to return
    df = pd.DataFrame(table)
    # Reset field names
    df.index = x_index
    df.columns = y_index

    # Unpivot frequency table
    df = df.stack()
    df = df.index.repeat(df).to_frame().reset_index(drop=True)

    # Return Dataframe
    return (df, old_mut, new_mut)

def get_row_col_sums(x):
    """
    Get the row and column sums respectively. Where X is a 2d numpy array
    """
    return (x.sum(axis=1), x.sum(axis=0))

def entropy_pair(table):
    total=table.sum()
    probs = []
    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            probs.append(table[i,j]/total)
    return np.sum([-p * np.log2(p) for p in probs if p > 0])


def MutInf(table):
    """
    Computes the mutual information using Shannon entropy & mutual information.
    Input is a contingency table (as numpy array)
    """
    # Get the entropy of the marginals
    rowsums, colsums = get_row_col_sums(table)
    ent_x = sum([-i * np.log2(i) for i in (rowsums / rowsums.sum()) if i > 0])
    ent_y = sum([-i * np.log2(i) for i in (colsums / colsums.sum()) if i > 0])
    # Get mutual information
    return ent_x + ent_y - entropy_pair(table)


def gen_number(x):
    table = x.copy()
    nrows, ncols = table.shape
    RR = random.sample(range(0, nrows), 2)
    CC = random.sample(range(0, ncols), 2)
    org_values = [table[RR[0], CC[0]], table[RR[1], CC[1]]]

    while org_values[0] < 1 or org_values[1] < 1:
        RR = random.sample(range(0, nrows), 2)
        CC = random.sample(range(0, ncols), 2)
        org_values = [table[RR[0], CC[0]], table[RR[1], CC[1]]]

    table[RR[0], CC[0]] = table[RR[0], CC[0]] - 1
    table[RR[1], CC[1]] = table[RR[1], CC[1]] - 1

    table[RR[0], CC[1]] = table[RR[0], CC[1]] + 1
    table[RR[1], CC[0]] = table[RR[1], CC[0]] + 1
    return table

def simul_anneal(initital_table, obj=MutInf, gen_fn=gen_number, max_n=5000, min_inf = 0.5, temp=10):
    """
    Performs simmulated annealing to increase the mutual information of two categorical variables
    """
    # Copy of initial point
    best = initital_table.copy()
    # Evaluate Initial point
    best_eval = obj(best)
    # CUrrent Working Solution
    curr, curr_eval = best, best_eval
    n=0
    # Run the algorithm while the mutual information isn't sufficient and the max number of iterations hasn't been reached
    while n<max_n and best_eval < min_inf:
        # Take a step
        cand = gen_fn(curr)
        # Evaluate new candidate point
        cand_eval = obj(cand)
        # Check for new best solution
        if cand_eval > best_eval:
            best, best_eval = cand, cand_eval
        # Difference between candidate and current point evaluation
        diff=cand_eval-curr_eval
        # calculate temperature
        t = temp/float(n+1)
        # Metropolis acceptance criterion
        metropolis=np.exp(diff/t)
        if diff > 0 or random.uniform(0,1) < metropolis:
            curr, curr_eval = cand, cand_eval
        n+=1
    return best, best_eval