#!/usr/bin/env python3
"""
Debug script to test Pollinations AI API integration
"""

import asyncio
import aiohttp
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_pollinations_api():
    """Test Pollinations AI API with different authentication methods."""
    
    api_key = "D6ivBlSgXRsU1F7r"
    
    # Test different API endpoints and authentication methods
    test_configs = [
        {
            'name': 'Method 1: Bearer Token',
            'url': 'https://text.pollinations.ai/',
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
                'User-Agent': 'AutoBot-Assembly/1.0'
            }
        },
        {
            'name': 'Method 2: API Key Header',
            'url': 'https://text.pollinations.ai/',
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Key': api_key,
                'User-Agent': 'AutoBot-Assembly/1.0'
            }
        },
        {
            'name': 'Method 3: No Auth (Free tier)',
            'url': 'https://text.pollinations.ai/',
            'headers': {
                'Content-Type': 'application/json',
                'User-Agent': 'AutoBot-Assembly/1.0'
            }
        },
        {
            'name': 'Method 4: Simple POST',
            'url': 'https://text.pollinations.ai/',
            'headers': {
                'User-Agent': 'AutoBot-Assembly/1.0'
            }
        }
    ]
    
    payload = {
        'messages': [
            {
                'role': 'system',
                'content': 'You are a helpful assistant.'
            },
            {
                'role': 'user',
                'content': 'Say hello in JSON format with a "message" field.'
            }
        ],
        'model': 'openai'
    }
    
    for config in test_configs:
        print(f"\n🧪 Testing {config['name']}")
        print(f"URL: {config['url']}")
        print(f"Headers: {config['headers']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config['url'],
                    json=payload,
                    headers=config['headers'],
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    print(f"Status: {response.status}")
                    print(f"Response Headers: {dict(response.headers)}")
                    
                    response_text = await response.text()
                    print(f"Response Length: {len(response_text)}")
                    print(f"Response Preview: {response_text[:200]}...")
                    
                    if response.status == 200:
                        print("✅ SUCCESS!")
                        return config, response_text
                    else:
                        print(f"❌ FAILED: {response.status}")
                        
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
    
    # Test alternative endpoints
    print(f"\n🧪 Testing Alternative Endpoints")
    
    alternative_urls = [
        'https://text.pollinations.ai/openai',
        'https://api.pollinations.ai/text',
        'https://pollinations.ai/api/text'
    ]
    
    for url in alternative_urls:
        print(f"\n🔍 Testing URL: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={'User-Agent': 'AutoBot-Assembly/1.0'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        response_text = await response.text()
                        print(f"✅ SUCCESS with {url}!")
                        print(f"Response: {response_text[:200]}...")
                        return {'url': url}, response_text
                        
        except Exception as e:
            print(f"❌ Exception with {url}: {e}")
    
    print("\n❌ All API tests failed")
    return None, None

async def main():
    """Main test function."""
    print("🚀 Starting Pollinations AI Debug Test")
    print("=" * 50)
    
    working_config, response = await test_pollinations_api()
    
    if working_config:
        print(f"\n🎉 Found working configuration!")
        print(f"Config: {working_config}")
        print(f"Response sample: {response[:300]}...")
    else:
        print(f"\n💡 Recommendations:")
        print("1. Check if API key is valid and active")
        print("2. Verify API endpoint URL")
        print("3. Check network connectivity")
        print("4. Try without authentication (free tier)")
        print("5. Check Pollinations AI documentation for changes")

if __name__ == "__main__":
    asyncio.run(main())