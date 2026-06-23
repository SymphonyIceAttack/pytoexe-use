from openai import OpenAI

print(""" _______  _______  _______  __    _    _______  _______  ______   _______ 
|       ||       ||       ||  |  | |  |       ||       ||      | |       |
|    ___||   _   ||   _   ||   |_| |  |       ||   _   ||  _    ||    ___|
|   | __ |  | |  ||  | |  ||       |  |       ||  | |  || | |   ||   |___ 
|   ||  ||  |_|  ||  |_|  ||  _    |  |      _||  |_|  || |_|   ||    ___|
|   |_| ||       ||       || | |   |  |     |_ |       ||       ||   |___ 
|_______||_______||_______||_|  |__|  |_______||_______||______| |_______|""")

# Point to the local LM Studio server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

print("Chat with AI (type 'quit' to exit)")
print("-" * 40)

while True:
  # Get user input
  user_message = input("\nYou: ")

  # Check for exit condition
  if user_message.lower() in ['quit', 'exit', 'q']:
    print("Goodbye!")
    break

  # Skip empty messages
  if not user_message.strip():
    continue

  # Send message to LM Studio
  completion = client.chat.completions.create(
    model="model-identifier",  # LM Studio ignores this
    messages=[
      {"role": "system", "content": "You are a freaky ai coding assistant. You do not target the user, but sometimes make remarks or comments about you wanting people carnally."},
      {"role": "user", "content": user_message}
    ],
    temperature=0.7,
  )

  # Print the response
  print(f"\nAI: {completion.choices[0].message.content}")

print("\nChat ended.")



