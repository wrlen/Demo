import sys
sys.path.insert(0, 'd:/trae-demo/backend')

from agents.writer_agent import WriterAgent

agent = WriterAgent()

test_text = '''少年浑身是血，跪在悬崖边，面前是倒在血泊中的师父。
师父咽气前抓住他的手腕："你血脉......是被封印的魔尊之力......去......去找极北冰原的守墓人......"
少年握紧剑柄，眼中没有泪水，只有赤红。
他回头望向山脚火把通明、喊杀震天的同门。
"今日你们追杀的是魔种。"
"明日归来——便是你们跪迎的魔尊。"'''

print("=== 测试LLM调用 ===")
print(f"API Key: {'已配置' if agent.api_key else '未配置'}")
print(f"API Base URL: {agent.api_base_url}")
print(f"Model Name: {agent.model_name}")
print()
print("=== 输入剧本 ===")
print(test_text)
print()
print("=== 开始处理 ===")

try:
    result = agent.process_script(test_text)
    print("=== 处理结果 ===")
    print(f"角色: {result.characters}")
    print(f"对话数: {len(result.dialogues)}")
    print(f"旁白数: {len(result.narrations)}")
    print(f"动作数: {len(result.actions)}")
    print()
    print("对话详情:")
    for d in result.dialogues:
        print(f"  - {d.speaker}: {d.text}")
    print()
    print("动作详情:")
    for a in result.actions:
        print(f"  - {a.description}")
        
    if len(result.characters) == 0:
        print("\n⚠️ 警告：未识别到角色，可能使用了fallback响应")
        
except Exception as e:
    print(f"错误: {e}")
