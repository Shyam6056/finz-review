import csv, random
random.seed(7)
rows = []
def add(m, d, desc, amt): rows.append((f"2025-{m:02d}-{d:02d}", desc, round(amt, 2)))
for m in range(1, 5):
    boost = 1.15 if m >= 3 else 1.0
    food = 1.35 if m >= 3 else 1.0
    add(m, 1, "Rent - Main Street Property", -45000)
    for d in range(2, 28, 3): add(m, d, "POS Settlement Card Sales", random.randint(28000, 38000) * boost)
    for d in (5, 12, 19, 26): add(m, d, "Zomato Payout", random.randint(12000, 18000) * boost)
    for d in (3, 8, 13, 18, 23):
        add(m, d, "Fresh Farms Vegetable Supplier", -random.randint(6000, 9000) * food)
        add(m, d + 1, "Metro Wholesale Food", -random.randint(5000, 8000) * food)
    add(m, 4, "Eco Packaging Boxes", -random.randint(3000, 4500))
    add(m, 10, "BESCOM Electricity Bill", -random.randint(7000, 9000))
    add(m, 11, "Airtel Broadband", -1499)
    add(m, 15, "Google Ads", -random.randint(4000, 6000))
    add(m, 16, "Notion Subscription", -800)
    add(m, 20, "Bank Service Charges", -350)
    add(m, 5, "Loan EMI HDFC", -20000)
    add(m, 25, "Owner Drawings", -25000)
    add(m, 28, "Payroll - Staff Salaries", -85000)
    add(m, 28, "Salary - Chef Ramesh", -30000)
add(2, 14, "Payment to R Kumar", -9000)
add(2, 18, "Refund from Metro Wholesale", 2500)
add(3, 9, "UPI 9876543210 misc", -3200)
add(3, 22, "Payment to XYZ Traders", -52000)
add(3, 12, "Purchase Kitchen Oven", -60000)
rows.append(next(r for r in rows if r[0] == "2025-02-15" and "Google" in r[1]))
rows.sort()
with open("sample_transactions.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "description", "amount"]); w.writerows(rows)
print("Created sample_transactions.csv")