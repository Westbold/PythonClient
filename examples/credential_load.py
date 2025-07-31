# Make sure you have the textverified package installed
# pip install textverified
#
# Credentials are required to use the TextVerified API.
# They are automatically loaded from the environment variables
# TEXTVERIFIED_API_KEY and TEXTVERIFIED_API_USERNAME.
# or can be set using the configure method.

from textverified import account as tv_account

# Get account details
account_info = tv_account.me()
print("Username:", account_info.username)
print("Balance:", account_info.current_balance)
