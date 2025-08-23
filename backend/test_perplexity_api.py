#!/usr/bin/env python3
"""
Test script for Perplexity API integration
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_perplexity_api():
    """Test the Perplexity API with different models"""
    
    # Get API key from environment
    api_key = os.getenv('SONAR_API_KEY')
    if not api_key:
        print("❌ SONAR_API_KEY not found in .env file")
        return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Set up the API endpoint and headers
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test cases with different models
    test_cases = [
        {
            "name": "Sonar Pro (General)",
            "model": "sonar-pro",
            "query": "What are the main airports in Shanghai, China? Please list their IATA codes."
        },
        {
            "name": "Sonar Deep Research (Detailed)",
            "model": "sonar-deep-research", 
            "query": "What are all the airport codes for Shanghai, China including both international and domestic airports?"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n=== Testing {test_case['name']} ===")
        
        payload = {
            "model": test_case["model"],
            "messages": [
                {"role": "user", "content": test_case["query"]}
            ],
            "max_tokens": 200,
            "temperature": 0.1
        }
        
        try:
            print(f"📡 Making API call to {test_case['model']}...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                print("✅ API call successful!")
                print(f"📝 Response content:")
                print("-" * 50)
                print(content)
                print("-" * 50)
                
                # Check if response contains airport codes
                import re
                codes = re.findall(r'\b[A-Z]{3}\b', content)
                if codes:
                    print(f"🛩️  Found airport codes: {codes}")
                else:
                    print("⚠️  No 3-letter airport codes found in response")
                    
            else:
                print(f"❌ API call failed: {response.status_code}")
                print(f"Error response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out (30s)")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_simple_query():
    """Test with a simple query to check basic API connectivity"""
    
    api_key = os.getenv('SONAR_API_KEY')
    if not api_key:
        print("❌ SONAR_API_KEY not found")
        return
    
    print(f"\n=== Simple Connectivity Test ===")
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "user", "content": "Hello, what is 2+2?"}
        ],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Simple test successful: {content}")
            return True
        else:
            print(f"❌ Simple test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Simple test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Perplexity API Integration...")
    print("=" * 60)
    
    # First try a simple test
    if test_simple_query():
        # If simple test works, try the full tests
        test_perplexity_api()
    else:
        print("\n⚠️  Skipping detailed tests due to simple test failure")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")