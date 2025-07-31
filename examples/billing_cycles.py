from textverified import account, billing_cycles


# Get account information
account_info = account.me()
print("Account Details:")
print(f"  Username: {account_info.username}")
print(f"  Balance: ${account_info.current_balance}")

# Get billing cycles
cycles = billing_cycles.list()
print("\nBilling Cycles:")

for cycle in cycles[:3]:  # Show last 3 cycles
    print(f"  Cycle ID: {cycle.id}")
    print(f"  Ends At: {cycle.billing_cycle_ends_at}")
    print(f"  State: {cycle.state}")
    print("  ---")
