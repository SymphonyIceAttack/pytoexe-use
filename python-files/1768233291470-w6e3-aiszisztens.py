# DEMO: csak sablon válaszok
def chatbot_demo(message):
    print("DEMO bot válasz: Köszönjük érdeklődését, hamarosan válaszolunk!")

# PRO: AI válaszok
import openai

openai.api_key = "YOUR_API_KEY"

def chatbot_pro(message):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=message,
        max_tokens=50
    )
    print(response.choices[0].text.strip())