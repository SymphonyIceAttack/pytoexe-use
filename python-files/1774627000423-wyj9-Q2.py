# Q2 - Job selection with time limit
# Dynamic Programming solution

def solve_q2(jobs, T):
    """
    jobs: list of tuples (duration, profit)
    T: total available time
    returns: (max_profit, chosen_jobs_indices)
    """

    n = len(jobs)

    # dp[i][t] = maximum profit using first i jobs and time limit t
    dp = [[0 for _ in range(T + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        duration, profit = jobs[i - 1]
        for t in range(T + 1):
            dp[i][t] = dp[i - 1][t]
            if duration <= t:
                dp[i][t] = max(dp[i][t], dp[i - 1][t - duration] + profit)

    # reconstruct chosen jobs
    chosen = []
    t = T
    for i in range(n, 0, -1):
        if dp[i][t] != dp[i - 1][t]:
            chosen.append(i)   # jobs numbered from 1
            duration, _ = jobs[i - 1]
            t -= duration

    chosen.reverse()
    return dp[n][T], chosen


# Test Case 1
jobs1 = [(2, 50), (1, 10), (3, 70), (2, 40)]
T1 = 5
profit1, chosen1 = solve_q2(jobs1, T1)
print("Q2 Test Case 1")
print("Maximum Profit:", profit1)
print("Chosen Jobs:", chosen1)
print()

# Test Case 2
jobs2 = [(4, 90), (3, 70), (2, 50), (1, 20), (3, 65)]
T2 = 7
profit2, chosen2 = solve_q2(jobs2, T2)
print("Q2 Test Case 2")
print("Maximum Profit:", profit2)
print("Chosen Jobs:", chosen2)