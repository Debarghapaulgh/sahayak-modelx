import asyncio
import sys
import os
from google.antigravity import Agent, LocalAgentConfig

# Load environment variables from .env if present
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, val = line.strip().split("=", 1)
                val = val.strip("'\"")
                os.environ[key] = val

def run_linter(path: str) -> str:
    """Runs linting and formatting validation on a specific path.

    Args:
        path: The directory or file path to lint.
    """
    import subprocess
    import os
    
    # Adjust path if 'src/' was passed but it doesn't exist, using 'synthetictutor' as fallback
    target_path = path
    if path == "src/" and not os.path.exists("src") and os.path.exists("synthetictutor"):
        target_path = "synthetictutor"
        
    print(f"\n[Tool Execution] Running black linter on: {target_path}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", target_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return f"Linting passed for {target_path}."
        else:
            return f"Linting issues found in {target_path} (Black check failed).\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
    except Exception as e:
        return f"Linter execution failed for {target_path}: {str(e)}"

async def execute_task(prompt: str):
    # Configure Agent
    config = LocalAgentConfig(
        model="gemini-3.6-flash",
        system_instructions="You are an autonomous senior engineer adhering to production best practices.",
        tools=[run_linter]
    )

    # Lifecycle context
    async with Agent(config) as agent:
        response = await agent.chat(prompt)
        
        # Stream thoughts if available
        print("\n--- Thought Stream ---")
        try:
            async for thought in response.thoughts:
                sys.stdout.write(thought)
                sys.stdout.flush()
        except Exception as e:
            print(f"(Thought streaming not supported or error: {e})")
        print("\n----------------------")

        # Stream response tokens
        print("\n--- Response Stream ---")
        async for token in response:
            sys.stdout.write(token)
            sys.stdout.flush()
        print("\n----------------------")

if __name__ == "__main__":
    prompt = "Inspect the repo structure, run linter on src/, and suggest improvements."
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    asyncio.run(execute_task(prompt))
