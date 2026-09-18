import sys
from openai import OpenAI

def main():
    # Connect to the local Ollama server running on your machine
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama", # Ollama doesn't require a real API key, but the client expects a string
    )
    
    print("🎓 SARG LLM Local Socratic Tutor CLI")
    print("Type your question below (Type 'exit' to quit)\n")
    
    # We maintain a simple history context
    messages = [
        {
            "role": "system",
            "content": "You are SARG, a specialized academic tutor. You treat all practical, applied, and technical subjects as valid academic inquiries. Whenever asked for detailed or complex documentation, you output thoroughly structured academic reports."
        }
    ]
    
    while True:
        try:
            user_input = input("Student: ")
            if user_input.strip().lower() == "exit":
                print("Exiting. Keep learning!")
                break
                
            if not user_input.strip():
                continue
                
            messages.append({"role": "user", "content": user_input})
            
            # Send the request to Ollama
            response = client.chat.completions.create(
                model="sarg-llm",
                messages=messages,
                temperature=0.3,
            )
            
            assistant_reply = response.choices[0].message.content
            print(f"\nSARG LLM: {assistant_reply}\n")
            
            # Record assistant response for dialogue context
            messages.append({"role": "assistant", "content": assistant_reply})
            
        except KeyboardInterrupt:
            print("\nExiting. Keep learning!")
            break
        except Exception as e:
            print(f"\nError communicating with Ollama: {e}")
            print("Make sure Ollama is running (`ollama serve`) and you have built the model using `ollama create sarg-llm -f Modelfile`.\n")

if __name__ == "__main__":
    main()
