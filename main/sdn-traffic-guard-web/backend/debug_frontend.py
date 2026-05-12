import requests
import json

def test_with_different_tokens():
    base_url = "http://localhost:8000"
    
    # 测试不同的token值
    test_cases = [
        ("1", "用户ID 1"),
        ("2", "用户ID 2"),
        ("invalid_token", "无效token"),
        ("", "空token"),
        (None, "无token")
    ]
    
    for token, description in test_cases:
        print(f"\n=== 测试 {description} ===")
        
        headers = {}
        if token is not None:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            # 测试conversations
            response = requests.get(f"{base_url}/api/ai/conversations", headers=headers)
            print(f"conversations状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"响应: {response.text}")
            
            # 测试rag/stats
            response = requests.get(f"{base_url}/api/ai/rag/stats")
            print(f"rag/stats状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"响应: {response.text}")
                
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    test_with_different_tokens()