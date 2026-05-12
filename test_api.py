import requests
import json

test_text = '''少年浑身是血，跪在悬崖边，面前是倒在血泊中的师父。
师父咽气前抓住他的手腕："你血脉......是被封印的魔尊之力......去......去找极北冰原的守墓人......"
少年握紧剑柄，眼中没有泪水，只有赤红。
他回头望向山脚火把通明、喊杀震天的同门。
"今日你们追杀的是魔种。"
"明日归来——便是你们跪迎的魔尊。"'''

# 测试后端API
try:
    # 1. 创建项目
    create_response = requests.post('http://localhost:8000/projects', 
        data='title=测试项目&description=测试',
        headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    if create_response.status_code == 200:
        project_data = create_response.json()
        project_id = project_data['id']
        print(f"✅ 项目创建成功: {project_id}")
        
        # 2. 解析剧本
        script_response = requests.post(f'http://localhost:8000/projects/{project_id}/script',
            json={'raw_text': test_text},
            headers={'Content-Type': 'application/json'})
        
        if script_response.status_code == 200:
            result = script_response.json()
            print(f"\n✅ 剧本解析成功")
            print(f"\n角色: {result.get('characters', [])}")
            print(f"对话数: {len(result.get('dialogues', []))}")
            print(f"旁白数: {len(result.get('narrations', []))}")
            print(f"动作数: {len(result.get('actions', []))}")
            
            print(f"\n完整响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 剧本解析失败: {script_response.status_code}")
            print(script_response.text)
    else:
        print(f"❌ 项目创建失败: {create_response.status_code}")
        print(create_response.text)
        
except Exception as e:
    print(f"❌ 错误: {e}")
