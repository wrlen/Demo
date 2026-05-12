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

print("=== 直接调用process_script ===")
result = agent.process_script(test_text)

print(f"角色: {result.characters}")
print(f"对话数: {len(result.dialogues)}")
print(f"旁白数: {len(result.narrations)}")
print(f"动作数: {len(result.actions)}")

print("\n=== 对话详情 ===")
for d in result.dialogues:
    print(f"  - {d.speaker}: {d.text}")

print("\n=== 旁白详情 ===")
for n in result.narrations:
    print(f"  - {n.text}")

print("\n=== 动作详情 ===")
for a in result.actions:
    print(f"  - {a.description}")
