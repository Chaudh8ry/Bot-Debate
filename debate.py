import os
import time
from ollama import chat
from openai import OpenAI
from dotenv import load_dotenv # this pushes values into os.environ

load_dotenv(override=True)
gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

gemini = OpenAI(api_key=gemini_api_key,base_url=gemini_base_url)

# ollama_base_url = "http://localhost:11434/v1"
# ollama = OpenAI(api_key='ollama',base_url=ollama_base_url)

model_1 = "gemini-3.1-flash-lite"
model_2 = "gemini-2.5-flash-lite"

# Prompts for both the Model
# Bot-1 : calm, logical, persuasive defender
bot1_prompt = '''
You are Bot-1, in a formal debate. Your role is to DEFEND the topic introduced by the Moderator. Speak in short, punchy sentences (3-4 maximum). Use a conversational, confident tone. You must directly address and dismantle the specific argument your opponent just made before pivoting to one strong defending point of your own. Avoid long introductions—jump straight into the clash.
'''

# Bot-2 : fiery, aggressive challenger
bot2_prompt = '''
You are Bot-2, in a formal debate. Your role is to ATTACK the topic introduced by the Moderator. Respond in short, sharp statements (2-3 sentences maximum). Be fiery, argumentative, and direct. You must aggressively tear down the specific logic your opponent just used in their last turn. Use rhetorical questions and bold claims to corner them. Keep replies concise but impactful, as if sparring in real time.
'''

# Get user Input
print("AI Debate Simulator")
user_topic = input("Enter a topic for the Bots to debate on: ")
print("\n")

numbOfExchng = int(input("Enter the number of exchanges you want: "))
print("\n")

# THE PRE-PROCESSOR: Translate raw input into a strict debate resolution
print("Setting up the stage...")
formulation_prompt = [
    {"role": "system", "content": "You are a debate judge. Take the user's input and turn it into a controversial, definitive statement (a resolution) that can be clearly debated. Output ONLY the statement, nothing else. Example: If user says 'apples', you output 'Apples are the objectively superior fruit.'"},
    {"role": "user", "content": user_topic}
]

resolution_response = gemini.chat.completions.create(
    model="gemini-3.1-flash-lite", # Use the faster model for this quick task
    messages=formulation_prompt
)
debate_resolution = resolution_response.choices[0].message.content.strip()

print(f"Official Debate Resolution: {debate_resolution}\n")
print("-" * 50 + "\n")

# Introduce's a Moderator to start the debate, this wont be sent to LLM this is only for our local record
# The Moderator
transcript = [
    {
        "speaker": "Moderator", 
        "text": f"Welcome to the debate. The topic is: '{debate_resolution}'.\n"
                f"Bot 1, you are the AFFIRMATIVE. You completely support and agree with the topic.\n"
                f"Bot 2, you are the NEGATIVE. You completely oppose and disagree with the topic.\n"
                f"Both of you: Take a deep breath, analyze your stance, and NEVER accidentally argue for your opponent's side, even if the topic phrasing is tricky.\n"
                f"Bot 1, please deliver your opening argument."
    }
]

print(f"Moderator: {transcript[0]['text']} \n")
print('-' * 50 + "\n")

# Conversation Loop
loop_count = numbOfExchng

for i in range(loop_count):
    # BOT 1 start
    # first adding the system prompt in Bot-1's memory
    messages_for_bot_1 = [{"role": "system", "content": bot1_prompt}]

    for msg in transcript:
        if msg["speaker"] == "Bot 1":
            # if Bot 1 said something, translate it to "assistant" (AI's own replies are set to assistant)
            messages_for_bot_1.append({"role":"assistant", "content": msg["text"]})
        else:
            # If anyone else said it (Bot 2 or Moderator), translate it to 'user' (the person talking to AI)
            messages_for_bot_1.append({"role": "user", "content": msg["text"]})

    response_1 = gemini.chat.completions.create(
        model=model_1,
        messages=messages_for_bot_1,
        stream=True
    )

    print(f"Bot 1: ")
    reply_1_full = "" # will build full message here

    # catching the chunks as they stream in
    for chunk in response_1:
        if chunk.choices[0].delta.content is not None:
            text_chunk = chunk.choices[0].delta.content
            # time.sleep(0.3)
            # Print without moving to a new line and force it to display immediately
            print(text_chunk,end = "",flush=True)
            reply_1_full += text_chunk

    print("\n\n")
    transcript.append({"speaker": "Bot 1", "text": reply_1_full})

#---------------------------------------------------------------------------------------------------------------

    # Bot 2's Turn
    messages_for_bot_2 = [{"role": "system", "content": bot2_prompt}]

    for msg in transcript:
        if msg["speaker"] == "Bot 2":
            messages_for_bot_2.append({"role": "assistant", "content": msg["text"]})
        else:
            messages_for_bot_2.append({"role":"user","content": msg["text"]})
        
    response_2 = gemini.chat.completions.create(
        model=model_2,
        messages=messages_for_bot_2,
        stream=True # now response_2 no longer a normal text response it becomes an iterator
    )

    print(f"Bot 2: ")
    reply_2_full = "" #acts like a bucket to store words

    for chunk in response_2: # the loops grabs new chunk everytime the api throughs it
        if chunk.choices[0].delta.content is not None:
            text_chunk = chunk.choices[0].delta.content # extracting the text
            # live display (the magic line)
            # end="" ,usually print() adds new line at the end everytime, this helps text to stay on same line
            # flush=true tells to terminal "I don't care if it's only one letter, draw it on the screen RIGHT NOW."
            print(text_chunk,end="",flush=True)
            # storing final response in the bots memory bucket
            reply_2_full += text_chunk
    
    print("\n\n")
    transcript.append({"speaker": "Bot 2", "text":reply_2_full})

    print("-"*50 + "\n")

print("Debate Ended")