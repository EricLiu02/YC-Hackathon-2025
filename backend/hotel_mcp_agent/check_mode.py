#!/usr/bin/env python3
"""
Check hotel MCP server API key configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_config():
    """Check API key configuration"""
    
    print("🔍 Checking Hotel MCP Server Configuration")
    print("=" * 50)
    
    # Check for required API keys
    search_key1 = os.getenv('SEARCH_API_KEY')
    search_key2 = os.getenv('SEARCHAPI_KEY') 
    perplexity_key = os.getenv('PERPLEXITY_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"🔑 SEARCH_API_KEY: {'✅ Found' if search_key1 else '❌ Not found'}")
    print(f"🔑 SEARCHAPI_KEY: {'✅ Found' if search_key2 else '❌ Not found'}")
    print(f"🔑 PERPLEXITY_API_KEY: {'✅ Found' if perplexity_key else '❌ Not found'}")
    print(f"🔑 OPENAI_API_KEY: {'✅ Found' if openai_key else '❌ Not found'}")
    
    # Check if SearchAPI key is available
    if search_key1 or search_key2:
        used_key = "SEARCH_API_KEY" if search_key1 else "SEARCHAPI_KEY"
        print(f"\n✅ SearchAPI configured using {used_key}")
        print(f"   • Real hotel data from Google Hotels")
        print(f"   • Live pricing and availability")
        print(f"   • Current amenities and reviews")
        
        if perplexity_key:
            print(f"✅ Location enrichment enabled")
        else:
            print(f"⚠️  Location enrichment disabled (no PERPLEXITY_API_KEY)")
            
        if openai_key:
            print(f"✅ Chat summaries enabled")
        else:
            print(f"⚠️  Chat summaries disabled (no OPENAI_API_KEY)")
            
        print(f"\n🚀 To run the server:")
        print(f"   uv run python fast_server.py")
        
        return True
    else:
        print(f"\n❌ SearchAPI key required!")
        print(f"   • Get key from: https://www.searchapi.io/")
        print(f"   • Set SEARCH_API_KEY or SEARCHAPI_KEY in .env file")
        print(f"   • Server will not start without this key")
        
        return False

if __name__ == "__main__":
    check_config()