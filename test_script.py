import requests

script = '李明盯着满屏数据，揉搓太阳穴。上司拍桌斥责："再出错就不用来了！"他握拳不语。天台黄昏，母亲发来短信："家永远是你的退路。"他仰头望见晚霞如焰。次日会议室，李明自信展示新方案："数据证明，这个方向可行。"掌声响起，荧幕微光映出他嘴角上扬的弧度。'

r = requests.post('http://localhost:8000/projects/a7de095c-cf29-4f2c-9db7-3a997431df81/script', json={'raw_text': script})
print(r.json())