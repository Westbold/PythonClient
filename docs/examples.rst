Examples
========

This section provides comprehensive examples of using the TextVerified Python client.

Complete Verification Workflow
------------------------------

Here's a complete example that demonstrates the full verification workflow:

.. code-block:: python

   from textverified import TextVerified
   import time
   
   # Initialize client
   client = TextVerified(
       api_key="your_api_key",
       api_username="your_username"
   )
   
   def complete_verification_example():
       """Complete example of phone verification workflow."""
       
       # 1. List available services
       print("Available services:")
       services = client.services.list()
       for service in services[:5]:  # Show first 5
           print(f"  {service.name} (ID: {service.id}) - ${service.price}")
       
       # 2. Create a verification for a specific service
       service_id = services[0].id  # Use first available service
       print(f"\nCreating verification for service ID: {service_id}")
       
       verification = client.verifications.create(service_id=service_id)
       print(f"Verification created:")
       print(f"  ID: {verification.id}")
       print(f"  Phone: {verification.number}")
       print(f"  Status: {verification.status}")
       
       # 3. Wait for SMS (in real usage, you'd implement proper polling)
       print("\nWaiting for SMS...")
       max_attempts = 30
       attempts = 0
       
       while attempts < max_attempts:
           time.sleep(10)  # Wait 10 seconds
           attempts += 1
           
           # Check for SMS messages
           messages = client.sms.get_sms(verification_id=verification.id)
           
           if messages:
               print("SMS received:")
               for msg in messages:
                   print(f"  From: {msg.sender}")
                   print(f"  Message: {msg.message}")
                   print(f"  Time: {msg.time}")
               break
           
           print(f"  Attempt {attempts}/{max_attempts} - No SMS yet")
       
       if attempts >= max_attempts:
           print("No SMS received within timeout period")
       
       return verification
   
   # Run the example
   if __name__ == "__main__":
       complete_verification_example()

Account Management
------------------

Managing your account and billing:

.. code-block:: python

   from textverified import account, billing_cycles
   
   def account_management_example():
       """Example of account and billing management."""
       
       # Get account information
       account_info = account.me()
       print(f"Account Details:")
       print(f"  Username: {account_info.username}")
       print(f"  Balance: ${account_info.balance}")
       print(f"  Email: {account_info.email}")
       
       # Get billing cycles
       cycles = billing_cycles.list()
       print(f"\nBilling Cycles ({len(cycles)} total):")
       
       for cycle in cycles[:3]:  # Show last 3 cycles
           print(f"  Cycle ID: {cycle.id}")
           print(f"  Period: {cycle.start_date} to {cycle.end_date}")
           print(f"  Amount: ${cycle.amount}")
           print(f"  Status: {cycle.status}")
           print("  ---")

Bulk Verification Processing
---------------------------

Processing multiple verifications efficiently:

.. code-block:: python

   from textverified import TextVerified
   import concurrent.futures
   import time
   
   client = TextVerified(api_key="your_key", api_username="your_username")
   
   def create_verification(service_id):
       """Create a single verification."""
       try:
           verification = client.verifications.create(service_id=service_id)
           return {
               'success': True,
               'verification': verification,
               'error': None
           }
       except Exception as e:
           return {
               'success': False,
               'verification': None,
               'error': str(e)
           }
   
   def bulk_verification_example():
       """Example of creating multiple verifications in parallel."""
       
       # Get available services
       services = client.services.list()
       if not services:
           print("No services available")
           return
       
       # Create multiple verifications (using same service for demo)
       service_id = services[0].id
       num_verifications = 5
       
       print(f"Creating {num_verifications} verifications...")
       
       # Use ThreadPoolExecutor for parallel creation
       with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
           futures = [
               executor.submit(create_verification, service_id)
               for _ in range(num_verifications)
           ]
           
           results = []
           for future in concurrent.futures.as_completed(futures):
               result = future.result()
               results.append(result)
               
               if result['success']:
                   v = result['verification']
                   print(f"✓ Created verification {v.id} with number {v.number}")
               else:
                   print(f"✗ Failed: {result['error']}")
       
       successful = [r for r in results if r['success']]
       print(f"\nSuccessfully created {len(successful)}/{num_verifications} verifications")
       
       return successful

Service Filtering and Selection
------------------------------

Finding the right service for your needs:

.. code-block:: python

   from textverified import services
   
   def service_filtering_example():
       """Example of filtering and selecting services."""
       
       # Get all services
       all_services = services.list()
       print(f"Total services available: {len(all_services)}")
       
       # Filter by price range
       budget_services = [s for s in all_services if float(s.price) <= 1.00]
       print(f"Services under $1.00: {len(budget_services)}")
       
       # Filter by name (e.g., find social media services)
       social_keywords = ['twitter', 'facebook', 'instagram', 'telegram', 'whatsapp']
       social_services = [
           s for s in all_services 
           if any(keyword.lower() in s.name.lower() for keyword in social_keywords)
       ]
       
       print(f"Social media services: {len(social_services)}")
       for service in social_services[:5]:
           print(f"  {service.name} - ${service.price}")
       
       # Find the cheapest service
       if all_services:
           cheapest = min(all_services, key=lambda s: float(s.price))
           print(f"\nCheapest service: {cheapest.name} - ${cheapest.price}")
       
       # Find services by country (if available in service data)
       # This would depend on your specific service data structure
       
       return {
           'all': all_services,
           'budget': budget_services,
           'social': social_services
       }

Error Handling Patterns
----------------------

Proper error handling for production use:

.. code-block:: python

   from textverified import TextVerified, verifications
   from textverified.textverified import TextVerifiedException
   import requests
   import time
   
   def robust_verification_example():
       """Example with comprehensive error handling."""
       
       max_retries = 3
       retry_delay = 5  # seconds
       
       for attempt in range(max_retries):
           try:
               # Attempt to create verification
               verification = verifications.create(service_id=1)
               print(f"Verification created successfully: {verification.id}")
               return verification
               
           except TextVerifiedException as e:
               print(f"TextVerified API error (attempt {attempt + 1}): {e}")
               
               if "insufficient balance" in str(e).lower():
                   print("Account balance too low - stopping retries")
                   break
               elif "service not available" in str(e).lower():
                   print("Service unavailable - stopping retries")
                   break
               
           except requests.exceptions.ConnectionError as e:
               print(f"Connection error (attempt {attempt + 1}): {e}")
               
           except requests.exceptions.Timeout as e:
               print(f"Timeout error (attempt {attempt + 1}): {e}")
               
           except Exception as e:
               print(f"Unexpected error (attempt {attempt + 1}): {e}")
           
           if attempt < max_retries - 1:
               print(f"Retrying in {retry_delay} seconds...")
               time.sleep(retry_delay)
               retry_delay *= 2  # Exponential backoff
       
       print("All retry attempts failed")
       return None

SMS Message Processing
---------------------

Advanced SMS message handling:

.. code-block:: python

   import re
   from textverified import sms
   
   def extract_verification_code(message_text):
       """Extract verification code from SMS message."""
       
       # Common patterns for verification codes
       patterns = [
           r'\b(\d{4,8})\b',           # 4-8 digit codes
           r'code[:\s]+(\d+)',         # "code: 123456"
           r'verify[:\s]+(\d+)',       # "verify: 123456"
           r'otp[:\s]+(\d+)',          # "otp: 123456"
           r'pin[:\s]+(\d+)',          # "pin: 123456"
       ]
       
       for pattern in patterns:
           match = re.search(pattern, message_text.lower())
           if match:
               return match.group(1)
       
       return None
   
   def sms_processing_example(verification_id):
       """Example of processing SMS messages for verification codes."""
       
       messages = sms.get_sms(verification_id=verification_id)
       
       if not messages:
           print("No SMS messages found")
           return None
       
       print(f"Found {len(messages)} SMS message(s):")
       
       verification_codes = []
       
       for i, message in enumerate(messages, 1):
           print(f"\nMessage {i}:")
           print(f"  From: {message.sender}")
           print(f"  Time: {message.time}")
           print(f"  Text: {message.message}")
           
           # Try to extract verification code
           code = extract_verification_code(message.message)
           if code:
               print(f"  📱 Verification code found: {code}")
               verification_codes.append(code)
           else:
               print("  ❓ No verification code detected")
       
       if verification_codes:
           print(f"\n✅ Extracted codes: {verification_codes}")
           return verification_codes[0]  # Return first found code
       else:
           print("\n❌ No verification codes found in any message")
           return None

Configuration Management
-----------------------

Managing different environments and configurations:

.. code-block:: python

   import os
   from dataclasses import dataclass
   from textverified import TextVerified
   
   @dataclass
   class Config:
       api_key: str
       api_username: str
       environment: str = "production"
       timeout: int = 30
       max_retries: int = 3
   
   def load_config() -> Config:
       """Load configuration from environment or config file."""
       
       return Config(
           api_key=os.environ.get("TEXTVERIFIED_API_KEY", ""),
           api_username=os.environ.get("TEXTVERIFIED_API_USERNAME", ""),
           environment=os.environ.get("ENVIRONMENT", "production"),
           timeout=int(os.environ.get("TEXTVERIFIED_TIMEOUT", "30")),
           max_retries=int(os.environ.get("TEXTVERIFIED_MAX_RETRIES", "3"))
       )
   
   def configuration_example():
       """Example of using configuration management."""
       
       config = load_config()
       
       if not config.api_key or not config.api_username:
           raise ValueError("Missing required configuration")
       
       print(f"Environment: {config.environment}")
       print(f"Timeout: {config.timeout}s")
       print(f"Max retries: {config.max_retries}")
       
       # Initialize client with configuration
       client = TextVerified(
           api_key=config.api_key,
           api_username=config.api_username
       )
       
       # Use client with configuration-aware settings
       # (timeout and retries would be implemented in your wrapper)
       
       return client
