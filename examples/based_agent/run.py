import time
from swarm import Swarm
from swarm.repl import run_demo_loop
from agents import based_agent

def run_autonomous_loop(agent, interval=20):
    client = Swarm()
    messages = []
    
    print("Starting autonomous Based Agent loop...")
    
    while True:
        # Generate a thought
        thought = f"It's been {interval} seconds. What should I do now? I should do some sort of onchain interaction based on my capabilities. Let's have fun with it! I'm not going to ask anyone for help, I'm just going to do something cool. There will be no user input, just the agent thinking and acting."
        messages.append({"role": "user", "content": thought})
        
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Thinking: {thought}")
        
        # Run the agent
        response = client.run(
            agent=agent,
            messages=messages,
            stream=True
        )
        
        # Process and print the response
        for chunk in response:
            if "tool_calls" in chunk and chunk["tool_calls"]:
                for tool_call in chunk["tool_calls"]:
                    if "function" in tool_call:
                        function_name = tool_call["function"]["name"]
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Executing: {function_name}")
        
        # Wait for the specified interval
        time.sleep(interval)

if __name__ == "__main__":
    # Uncomment the desired mode
    # run_demo_loop(based_agent, stream=True)  # Interactive CLI mode
    run_autonomous_loop(based_agent)  # Autonomous mode
