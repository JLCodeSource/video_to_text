import os
from pathlib import Path

from openai import OpenAI

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    msg = "OpenAI API key not provided."
    raise ValueError(msg)

client = OpenAI(api_key=api_key)

# Generate voice 1
response1 = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=(
        "I have always wondered, why is it that every single programmer starts their "
        "journey by making the computer say hello world? Is there some kind of secret tradition behind it?"
    ),
)

# Explicit Gap: Using a string of periods/dashes creates a more forced pause
response_gap = client.audio.speech.create(model="tts-1", voice="alloy", input=". . . . . .")

# Voice 2: Onyx (Deep, low-pitched, very different from Alloy)
response2 = client.audio.speech.create(
    model="tts-1",
    voice="onyx",
    input=(
        "It is simpler than you think. It originated back in nineteen seventy eight just to test if the compiler "
        "was installed correctly. Now, it is just how we say welcome to the craft."
    ),
)
# Combine binary data
output_file = Path("hello_conversation.mp3")
with open(output_file, "wb") as f:
    f.write(response1.content)
    f.write(response_gap.content)
    f.write(response2.content)

print(f"Success! Audio saved to {output_file}")
