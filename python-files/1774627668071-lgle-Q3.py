# Q3 - Jobs with deadlines and  prerequisites
# Exact subset DP solution

def cnf_satisfied(cnf_formula, completed_jobs):
    """
    cnf_formula is a list of clauses.
    Each clause is a list of job numbers.

    Example:
    (J1) AND (J2 OR J3) AND (J4 OR J5)
    becomes:
    [[1], [2, 3], [4, 5]]

    completed_jobs is a set of completed job numbers.
    """
    for clause in cnf_formula:
        clause_ok = False
        for job in clause:
            if job in completed_jobs:
                clause_ok = True
                break
        if not clause_ok:
            return False
    return True


def solve_q3(jobs, T):
    """
    jobs: list of dictionaries with keys:
        duration, profit, deadline, prereq

    prereq is a CNF formula represented as list of clauses.
    Example:
        [] means no prerequisite
        [[1], [2, 3]] means (J1) AND (J2 OR J3)
    """

    n = len(jobs)
    INF = 10**9

    # dp[mask] = minimum completion time for this subset
    dp = [INF] * (1 << n)
    parent = [-1] * (1 << n)
    last_job = [-1] * (1 << n)
    profit_sum = [0] * (1 << n)

    dp[0] = 0

    # precompute profits
    for mask in range(1 << n):
        total = 0
        for i in range(n):
            if mask & (1 << i):
                total += jobs[i]["profit"]
        profit_sum[mask] = total

    for mask in range(1 << n):
        if dp[mask] == INF:
            continue

        completed = {i + 1 for i in range(n) if mask & (1 << i)}

        for i in range(n):
            if mask & (1 << i):
                continue

            job = jobs[i]
            finish_time = dp[mask] + job["duration"]

            if not cnf_satisfied(job["prereq"], completed):
                continue

            if finish_time <= T and finish_time <= job["deadline"]:
                new_mask = mask | (1 << i)
                if finish_time < dp[new_mask]:
                    dp[new_mask] = finish_time
                    parent[new_mask] = mask
                    last_job[new_mask] = i + 1

    # find best feasible subset with maximum profit
    best_mask = 0
    best_profit = 0

    for mask in range(1 << n):
        if dp[mask] != INF and profit_sum[mask] > best_profit:
            best_profit = profit_sum[mask]
            best_mask = mask

    # reconstruct order
    order = []
    current = best_mask
    while current != 0:
        order.append(last_job[current])
        current = parent[current]
    order.reverse()

    return best_profit, order


# ---------------- Q3 Test Case 1 ----------------
jobs1 = [
    {"duration": 2, "profit": 50, "deadline": 3, "prereq": []},            # J1
    {"duration": 1, "profit": 20, "deadline": 4, "prereq": []},            # J2
    {"duration": 2, "profit": 60, "deadline": 5, "prereq": [[1]]},         # J3
    {"duration": 1, "profit": 30, "deadline": 6, "prereq": [[2, 3]]},      # J4
    {"duration": 2, "profit": 40, "deadline": 7, "prereq": [[3], [1, 4]]}  # J5
]

T1 = 7
profit1, order1 = solve_q3(jobs1, T1)

print("Q3 Test Case 1")
print("Maximum Profit:", profit1)
print("Chosen Jobs in Order:", order1)
print()

# ---------------- Q3 Test Case 2 ----------------
jobs2 = [
    {"duration": 2, "profit": 20, "deadline": 3, "prereq": []},            # J1
    {"duration": 2, "profit": 25, "deadline": 4, "prereq": []},            # J2
    {"duration": 3, "profit": 70, "deadline": 7, "prereq": [[1, 2]]},      # J3
    {"duration": 1, "profit": 15, "deadline": 5, "prereq": []},            # J4
    {"duration": 2, "profit": 60, "deadline": 8, "prereq": [[3], [4, 2]]}, # J5
    {"duration": 2, "profit": 45, "deadline": 6, "prereq": [[1], [2]]}     # J6
]

T2 = 8
profit2, order2 = solve_q3(jobs2, T2)

print("Q3 Test Case 2")
print("Maximum Profit:", profit2)
print("Chosen Jobs in Order:", order2)