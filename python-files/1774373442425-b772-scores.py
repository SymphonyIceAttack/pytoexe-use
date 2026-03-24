open_price = float(input("Open Price: "))
buy = float(input("Buy Level: "))
t1 = float(input("Target 1: "))
t2 = float(input("Target 2: "))
sl = float(input("Stop Loss: "))

risk = buy - sl
reward1 = t1 - buy
reward2 = t2 - buy

rr1 = reward1 / risk
rr2 = reward2 / risk

risk_pct = (risk / buy) * 100
t1_pct = (reward1 / buy) * 100
t2_pct = (reward2 / buy) * 100

diff = buy - open_price
diff_pct = (diff / open_price) * 100

print("\n--- Results ---")
print(f"Risk: {risk:.2f}")
print(f"Reward T1: {reward1:.2f} | RR: 1:{rr1:.2f}")
print(f"Reward T2: {reward2:.2f} | RR: 1:{rr2:.2f}")
print(f"Risk %: {risk_pct:.2f}%")
print(f"T1 %: {t1_pct:.2f}% | T2 %: {t2_pct:.2f}%")
print(f"Entry vs Open: {diff:.2f} ({diff_pct:.2f}%)")