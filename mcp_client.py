import requests
import json

def test_server():
    print("Testing GitHub MCP Server...")
    print("=" * 50)
    
    # Test 1: Root endpoint
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        print(f"✓ Root endpoint: {response.status_code} - {response.json()}")
    except requests.ConnectionError:
        print("✗ Cannot connect to server. Make sure it's running:")
        print("  uvicorn gitbuh_server:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False
    
    # Test 2: Health endpoint
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        print(f"✓ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False
    
    # Test 3: List open issues via JSON-RPC
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "list_open_issues",
            "params": {},
            "id": 1
        }
        
        response = requests.post('http://localhost:8000/', json=payload, timeout=10)
        result = response.json()
        
        print(f"✓ JSON-RPC response: {response.status_code}")
        
        # Check if we got a valid response
        if 'result' in result:
            issues = result['result']
            print(f"✓ Found {len(issues)} open issues")
            for issue in issues:
                print(f"  - {issue.get('title', 'No title')} (#{issue.get('number', '?')})")
        elif 'error' in result:
            print(f"✗ Tool error: {result['error']}")
        else:
            print(f"✗ Unexpected response format: {result}")
            
    except Exception as e:
        print(f"✗ Tool call failed: {e}")
        return False
    
    return True

# Test list_open_issues tool
payload = {
        "jsonrpc": "2.0",
        "method": "list_open_issues",
        "params": {},
        "id": 1
    }
    
try:
        response = requests.post('http://localhost:8000/', json=payload)
        print("List issues response:", response.json())
except Exception as e:
        print(f"Error calling tool: {e}")

# Test create_issue tool

create_payload = {
        "jsonrpc": "2.0",
        "method": "create_issue",
        "params": {
            "title": "Test Issue from Client",
            "body": "This is a test issue created from the client."
        },
        "id": 2
    }
    
try:
        create_response = requests.post('http://localhost:8000/', json=create_payload)
        print("Create issue response:", create_response.json())
except Exception as e:
        print(f"Error creating issue: {e}")        

if __name__ == "__main__":
    success = test_server()
    if success:
        print("\n✓ Server test completed successfully!")
    else:
        print("\n✗ Server test failed.")