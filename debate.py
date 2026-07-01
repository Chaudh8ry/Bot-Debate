import os
import time
from prompts import bot1_prompt,bot2_prompt,judge_prompt,closing_prompt
from openai import OpenAI
import re # for searching
from dotenv import load_dotenv # this pushes values into os.environ

load_dotenv(override=True)
gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

gemini = OpenAI(api_key=gemini_api_key,base_url=gemini_base_url)

model_1 = "gemini-3.1-flash-lite"
model_2 = "gemini-2.5-flash-lite"

# Get user Input
print("AI Debate Simulator")
user_topic = input("Enter a topic for the Bots to debate on: ")
print("\n")

numbOfExchng = int(input("Enter the number of exchanges you want: "))
print("\n")

# THE PRE-PROCESSOR: Translate raw input into a strict debate resolution
print("Setting up the stage...")
formulation_prompt = [
    {"role": "system", "content": "You are a debate judge.If a user put's a input that is not specific or kinda vague and cant be concluded what exactly to draw from this topic then turn the user input into a controversial, definitive statement (a resolution) that can be clearly debated. Output ONLY the statement, nothing else. Example: If user says 'apples', you output 'Apples are the objectively superior fruit.'"},
    {"role": "user", "content": user_topic}
]

resolution_response = gemini.chat.completions.create(
    model="gemini-3.5-flash", # Use the faster model for this quick task
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

# Tracking scoring of Bot's
bot1_total = 0
bot2_total = 0

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
            # end="" means Print without moving to a new line and force it to display immediately
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

    # Judge's Turn 
    last_two = transcript[-2:] #grabs only Bot 1 and Bot 2's last message
    judge_input = f"Bot 1 said: {last_two[0]['text']} \n\nBot 2 said {last_two[1]['text']}"

    judge_message = [
        {"role": "system", "content": judge_prompt},
        {"role": "user", "content": judge_input}
    ]

    judge_response = gemini.chat.completions.create(
        model="gemini-3.5-flash",
        messages=judge_message
    )

    verdict = judge_response.choices[0].message.content.strip()
    print(f"Judge:\n{verdict}")
    print("-"*50 + "\n")

    # Parse score to track total
    # re.search() looks inside the string verdict for the pattern.
    # Pattern breakdown:
        # BOT 1 SCORE: → literal text it expects.
        # \s* → zero or more whitespace characters (spaces, tabs, newlines).
        # (\d+) → one or more digits, captured in a group.
    b1 = re.search(r'BOT 1 SCORE:\s*(\d+)',verdict)
    b2 = re.search(r'BOT 2 SCORE:\s*(\d+)',verdict)
    # extract and add score
    if b1:
        bot1_total += int(b1.group(1))
    if b2:
        bot2_total += int(b2.group(1))


# CLOSING ARGUMENTS
print("=" * 50)
print("CLOSING ARGUMENTS")
print("=" * 50 + "\n")

closing_prompt = "The debate is now over. Deliver your closing argument in exactly 5 sentences. Summarize your strongest points and why your side won."

# Bot 1 closing
messages_for_bot_1.append({"role": "user", "content": closing_prompt})
closing_1 = gemini.chat.completions.create(
    model=model_1,
    messages=messages_for_bot_1,
    stream=True
)

print("Bot 1 (Closing): ")
closing_1_full = ""
for chunk in closing_1:
    if chunk.choices[0].delta.content is not None:
        text_chunk = chunk.choices[0].delta.content
        print(text_chunk, end="", flush=True)
        closing_1_full += text_chunk
print("\n\n")

# Bot 2 closing
messages_for_bot_2.append({"role": "user", "content": closing_prompt})
closing_2 = gemini.chat.completions.create(  # switch ollama to gemini here
    model=model_1,
    messages=messages_for_bot_2,
    stream=True
)
print("Bot 2 (Closing): ")
closing_2_full = ""
for chunk in closing_2:
    if chunk.choices[0].delta.content is not None:
        text_chunk = chunk.choices[0].delta.content
        print(text_chunk, end="", flush=True)
        closing_2_full += text_chunk
print("\n\n")

# FINAL VERDICT
print("=" * 50)
print("FINAL VERDICT")
print("=" * 50 + "\n")

final_judge_messages = [
    {"role": "system", "content": "You are a debate judge delivering a final verdict."},
    {"role": "user", "content": 
        f"Total scores after {loop_count} rounds:\n"
        f"Bot 1: {bot1_total} points\n"
        f"Bot 2: {bot2_total} points\n\n"
        f"Bot 1 closing: {closing_1_full}\n\n"
        f"Bot 2 closing: {closing_2_full}\n\n"
        f"Declare the overall winner with a 3-sentence justification."
    }
]

final_verdict = gemini.chat.completions.create(
    model="gemini-3.5-flash",
    messages=final_judge_messages
)
print(f"⚖️  Final Verdict:\n{final_verdict.choices[0].message.content.strip()}")
print("\nDebate Ended")

print("Debate Ended")