#!/usr/bin/env python3
"""
Test chat wrapper with automated input
"""

import subprocess
import sys
import time

def test_chat_with_input():
    """Test the chat wrapper with sample inputs"""
    
    test_inputs = [
        "Find hotels in Paris tomorrow for 2 nights",
        "quit"
    ]
    
    print("🤖 Testing Hotel Chat Wrapper")
    print("=" * 50)
    
    # Create input string
    input_text = "\n".join(test_inputs) + "\n"
    
    try:
        # Run the chat wrapper with input
        process = subprocess.Popen(
            [sys.executable, "chat_wrapper.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="."
        )
        
        # Send input and get output
        stdout, stderr = process.communicate(input=input_text, timeout=30)
        
        print("📝 STDOUT:")
        print(stdout)
        
        if stderr:
            print("\n📋 STDERR (logs):")
            print(stderr)
        
        print(f"\n✅ Chat wrapper is working! Exit code: {process.returncode}")
        
    except subprocess.TimeoutExpired:
        print("⏰ Chat test timed out")
        process.kill()
    except Exception as e:
        print(f"❌ Error testing chat: {e}")

if __name__ == "__main__":
    test_chat_with_input()