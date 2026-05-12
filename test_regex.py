import re

script = '李明盯着满屏数据，揉搓太阳穴。上司拍桌斥责："再出错就不用来了！"他握拳不语。天台黄昏，母亲发来短信："家永远是你的退路。"他仰头望见晚霞如焰。次日会议室，李明自信展示新方案："数据证明，这个方向可行。"掌声响起，荧幕微光映出他嘴角上扬的弧度。'

print("原始文本:", script)
print()

pattern = r'([^。！？]+?)[：:]"([^"]+)"'
matches = re.findall(pattern, script)
print("匹配结果:", matches)

for speaker_part, text in matches:
    print(f"说话者部分: '{speaker_part}', 对话内容: '{text}'")