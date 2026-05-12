import os
import json
import requests
from dotenv import load_dotenv
from typing import List
from models import Dialogue, Narration, Action, ScriptResponse

load_dotenv()

class WriterAgent:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_base_url = os.getenv("API_BASE_URL", "https://api.example.com/v1/chat/completions")
        self.model_name = os.getenv("MODEL_NAME", "gpt-4")

    def _call_llm(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        system_prompt = """你是一位专业的漫剧编剧。请将用户提供的原始文本转换为结构化的剧本数据。

输出格式要求：
{
  "dialogues": [{"speaker": "角色名", "text": "对话内容", "position": "center"}],
  "narrations": [{"text": "旁白内容", "position": "top"}],
  "actions": [{"description": "动作描述", "position": "bottom"}],
  "characters": [{"name": "角色1", "description": "根据剧本内容描述该角色的性格、外貌特征和行为特点"}, {"name": "角色2", "description": "..."}]
}

说明：
- dialogues: 人物对话，包含说话者、文本内容和显示位置
- narrations: 旁白叙述，包含文本和显示位置
- actions: 动作描述，描述场景中的动作
- characters: 角色列表，每个角色包含name（角色名称）和description（详细描述，包括性格、外貌、行为特点等）
- position 可选值: top, center, bottom"""
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 8192
        }
        
        try:
            print(f"[DEBUG] Calling LLM API: {self.api_base_url}")
            response = requests.post(self.api_base_url, headers=headers, json=payload, timeout=60)
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response text: {response.text[:500]}")
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            elif "output" in result:
                return result["output"]["text"]
            else:
                raise ValueError("Unexpected API response format")
        except Exception as e:
            print(f"LLM API call failed: {e}")
            import traceback
            traceback.print_exc()
            return self._parse_text_directly(prompt)

    def _parse_text_directly(self, raw_text: str) -> str:
        dialogues = []
        narrations = []
        actions = []
        characters = set()
        
        import re
        
        lines = raw_text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            pattern1 = r'^([^：:]+?)[：:]\s*["“]([^"”]+)["”]'
            match = re.match(pattern1, line)
            if match:
                speaker = match.group(1).strip()
                text = match.group(2).strip()
                
                speaker = self._clean_speaker(speaker)
                
                if self._is_character_name(speaker):
                    characters.add(speaker)
                    dialogues.append({
                        "speaker": speaker,
                        "text": text,
                        "position": "center"
                    })
                    processed_lines.append({'type': 'dialogue', 'speaker': speaker, 'content': text})
                    continue
            
            pattern2 = r'^["“]([^"”]+)["”]$'
            match = re.match(pattern2, line)
            if match:
                text = match.group(1).strip()
                
                probable_speaker = self._find_probable_speaker(characters, processed_lines)
                
                if probable_speaker and self._looks_like_dialogue(text):
                    characters.add(probable_speaker)
                    dialogues.append({
                        "speaker": probable_speaker,
                        "text": text,
                        "position": "center"
                    })
                    processed_lines.append({'type': 'dialogue', 'speaker': probable_speaker, 'content': text})
                else:
                    narrations.append({
                        "text": text,
                        "position": "top"
                    })
                    processed_lines.append({'type': 'narration', 'content': text})
                continue
            
            if '：' in line and not line.startswith('"') and not line.startswith('“'):
                idx = line.index('：')
                speaker = line[:idx].strip()
                text = line[idx+1:].strip()
                
                text = text.strip('"“”')
                
                if self._is_character_name(speaker) and text:
                    characters.add(speaker)
                    dialogues.append({
                        "speaker": speaker,
                        "text": text,
                        "position": "center"
                    })
                    processed_lines.append({'type': 'dialogue', 'speaker': speaker, 'content': text})
                    continue
            
            if self._is_character_name(line):
                characters.add(line)
                processed_lines.append({'type': 'character', 'content': line})
                continue
            
            speaker = self._extract_speaker_from_action(line)
            if speaker:
                characters.add(speaker)
            
            processed_lines.append({'type': 'action', 'content': line})
            actions.append({
                "description": line,
                "position": "bottom"
            })
        
        character_descriptions = {}
        for char in characters:
            description = self._generate_character_description(char, raw_text)
            character_descriptions[char] = description
        
        characters_with_desc = [{"name": char, "description": character_descriptions[char]} for char in characters]
        
        result = {
            "dialogues": dialogues,
            "narrations": narrations,
            "actions": actions,
            "characters": characters_with_desc
        }
        
        return json.dumps(result)
    
    def _parse_text_directly_fallback(self, raw_text: str) -> ScriptResponse:
        json_str = self._parse_text_directly(raw_text)
        try:
            data = json.loads(json_str)
            
            dialogues = [Dialogue(**d) for d in data.get("dialogues", [])]
            raw_characters = data.get("characters", [])
            
            characters_with_desc = []
            for char in raw_characters:
                if isinstance(char, str):
                    char_name = char
                    # 根据角色的对话内容生成描述
                    char_dialogues = [d for d in dialogues if d.speaker == char_name]
                    description = self._generate_description_from_dialogues(char_name, char_dialogues)
                    characters_with_desc.append({
                        "name": char_name,
                        "description": description
                    })
                else:
                    characters_with_desc.append(char)
            
            return ScriptResponse(
                dialogues=dialogues,
                narrations=[Narration(**n) for n in data.get("narrations", [])],
                actions=[Action(**a) for a in data.get("actions", [])],
                characters=characters_with_desc
            )
        except Exception as e:
            print(f"本地解析失败: {e}")
            return self._generate_fallback_response()
    
    def _clean_speaker(self, speaker: str) -> str:
        action_verbs = ['咽气前抓住他的手腕', '拍桌斥责', '发来短信', '说', '道', '斥责', '问', '答', '喊道', '怒吼', '低语', '微笑', '摇头', '拍桌', '握紧剑柄', '回头望', '看着', '指向']
        
        for verb in action_verbs:
            if verb in speaker:
                speaker = speaker.replace(verb, '').strip()
                break
        
        return speaker
    
    def _extract_speaker_from_action(self, text: str) -> str:
        role_keywords = ['少年', '少女', '男子', '女子', '老人', '小孩', '师父', '师傅', '徒弟', '师兄', '师姐', '师弟', '师妹', '父亲', '母亲', '哥哥', '姐姐', '弟弟', '妹妹', '上司', '下属', '老板', '经理']
        
        for keyword in role_keywords:
            if keyword in text:
                return keyword
        
        return None
    
    def _is_character_name(self, text: str) -> bool:
        if len(text) > 10:
            return False
        
        if any(char in text for char in ['。', '，', '！', '？', '；', '、', '：', ':']):
            return False
        
        if text.startswith('"') or text.startswith('“') or text.startswith('(') or text.startswith('（'):
            return False
        
        common_roles = ['少年', '少女', '男子', '女子', '老人', '小孩', '师父', '师傅', '徒弟', '师兄', '师姐', '师弟', '师妹', '父亲', '母亲', '哥哥', '姐姐', '弟弟', '妹妹', '上司', '下属', '老板', '经理']
        if text in common_roles:
            return True
        
        if text == text.strip() and text:
            return True
        
        return False
    
    def _looks_like_dialogue(self, text: str) -> bool:
        dialogue_patterns = ['你们', '我', '你', '他', '她', '我们', '他们', '说', '道', '问', '答', '是', '不是', '要', '不要']
        return any(pattern in text for pattern in dialogue_patterns)
    
    def _find_probable_speaker(self, characters, processed_lines):
        action_keywords = ['跪', '站', '坐', '走', '跑', '看', '望', '握', '拿', '举', '挥', '回头', '转身', '说', '喊', '叫']
        
        for line in reversed(processed_lines[-5:]):
            if line.get('type') == 'character':
                return line.get('content')
        
        if characters:
            recent_speakers = []
            for line in reversed(processed_lines[-5:]):
                if line.get('type') == 'dialogue':
                    recent_speakers.append(line.get('speaker'))
            
            if recent_speakers:
                last_speaker = recent_speakers[0]
                
                has_new_action = False
                for line in reversed(processed_lines[-3:]):
                    if line.get('type') == 'action':
                        content = line.get('content', '')
                        if any(keyword in content for keyword in action_keywords):
                            new_speaker = self._extract_speaker_from_action(content)
                            if new_speaker and new_speaker != last_speaker:
                                return new_speaker
                return last_speaker
            
            return list(characters)[-1]
        
        for line in reversed(processed_lines[-3:]):
            content = line.get('content', '')
            speaker = self._extract_speaker_from_action(content)
            if speaker:
                return speaker
        
        return '少年' if '少年' in str(processed_lines) else None

    def _generate_character_description(self, character_name: str, raw_text: str) -> str:
        import re
        
        descriptions = []
        
        keywords = {
            '老人': '年长者，白发苍苍，面容慈祥',
            '少年': '年轻男子，充满活力',
            '少女': '年轻女子，清纯可爱',
            '中年': '中年人，成熟稳重',
            '青年': '青年人，朝气蓬勃',
            '男子': '男性角色',
            '女子': '女性角色',
            '女孩': '年轻女孩',
            '男孩': '年轻男孩',
            '师傅': '师傅，技艺高超',
            '徒弟': '徒弟，勤奋好学',
            '老板': '老板，精明干练',
            '员工': '员工，认真负责',
            '老师': '老师，学识渊博',
            '学生': '学生，勤奋好学',
            '医生': '医生，救死扶伤',
            '护士': '护士，温柔体贴',
            '警察': '警察，正义勇敢',
            '船长': '船长，经验丰富',
            '红衣': '穿着红色衣服',
            '白衣': '穿着白色衣服',
            '黑衣': '穿着黑色衣服',
            '孟婆': '地府孟婆，掌管忘川',
            '无常': '黑白无常，勾魂使者',
            '殿主': '殿主，地位尊贵',
            '公子': '公子，风度翩翩',
            '小姐': '小姐，大家闺秀',
            '将军': '将军，威武勇猛',
            '侠客': '侠客，行侠仗义',
            '书生': '书生，温文尔雅',
            '道士': '道士，道法高深',
            '和尚': '和尚，慈悲为怀',
        }
        
        for keyword, desc in keywords.items():
            if keyword in character_name:
                descriptions.append(desc)
        
        if not descriptions:
            descriptions.append('角色描述')
        
        return '，'.join(descriptions)
    
    def _generate_description_from_dialogues(self, character_name: str, dialogues: list) -> str:
        descriptions = []
        
        # 先获取基础描述
        base_desc = self._generate_character_description(character_name, "")
        if base_desc != '角色描述':
            descriptions.append(base_desc)
        
        # 根据对话内容分析性格
        if dialogues:
            all_text = ' '.join([d.text for d in dialogues])
            
            # 分析语气
            angry_words = ['该死', '混蛋', '滚', '找死', '可恶', '岂有此理', '放肆', '大胆', '气死我了']
            gentle_words = ['温柔', '轻轻', '缓缓', '柔声', '轻声', '微笑', '轻轻道', '温柔道']
            sad_words = ['伤心', '难过', '流泪', '哭泣', '悲伤', '痛心', '心碎']
            happy_words = ['开心', '高兴', '笑容', '欢喜', '愉快', '兴奋']
            wise_words = ['道', '曰', '善', '然', '诺', '罢了', '也罢', '须知', '切记']
            fierce_words = ['怒喝', '大喝', '厉声', '怒斥', '怒视', '拔剑', '紧握']
            
            has_angry = any(word in all_text for word in angry_words)
            has_gentle = any(word in all_text for word in gentle_words)
            has_sad = any(word in all_text for word in sad_words)
            has_happy = any(word in all_text for word in happy_words)
            has_wise = any(word in all_text for word in wise_words)
            has_fierce = any(word in all_text for word in fierce_words)
            
            if has_angry:
                descriptions.append('性格暴躁')
            if has_gentle:
                descriptions.append('性格温柔')
            if has_sad:
                descriptions.append('多愁善感')
            if has_happy:
                descriptions.append('性格开朗')
            if has_wise:
                descriptions.append('智慧深沉')
            if has_fierce:
                descriptions.append('气势威严')
            
            # 根据对话长度判断角色重要性
            if len(dialogues) >= 5:
                descriptions.append('主要角色')
            elif len(dialogues) >= 2:
                descriptions.append('重要角色')
        
        if not descriptions:
            descriptions.append('角色描述')
        
        return '，'.join(descriptions)

    def process_script(self, raw_text: str) -> ScriptResponse:
        try:
            print(f"[DEBUG process_script] Calling _call_llm with text: {raw_text[:50]}")
            llm_response = self._call_llm(raw_text)
            print(f"[DEBUG process_script] LLM response: {llm_response[:200] if llm_response else 'None'}")
            data = json.loads(llm_response)
            
            dialogues = [Dialogue(**d) for d in data.get("dialogues", [])]
            narrations = [Narration(**n) for n in data.get("narrations", [])]
            actions = [Action(**a) for a in data.get("actions", [])]
            
            raw_characters = data.get("characters", [])
            characters = []
            for char in raw_characters:
                if isinstance(char, str):
                    # 根据角色的对话内容生成个性化描述
                    char_dialogues = [d for d in dialogues if d.speaker == char]
                    description = self._generate_description_from_dialogues(char, char_dialogues)
                    characters.append({
                        "name": char,
                        "description": description
                    })
                else:
                    # 如果AI已经返回了描述，检查是否需要增强
                    char_name = char.get("name", "")
                    char_dialogues = [d for d in dialogues if d.speaker == char_name]
                    if char.get("description") and char.get("description") != '角色描述':
                        characters.append(char)
                    else:
                        description = self._generate_description_from_dialogues(char_name, char_dialogues)
                        characters.append({
                            "name": char_name,
                            "description": description
                        })
            
            return ScriptResponse(
                dialogues=dialogues,
                narrations=narrations,
                actions=actions,
                characters=characters
            )
        except (json.JSONDecodeError, Exception) as e:
            print(f"LLM解析失败，使用本地解析: {e}")
            return self._parse_text_directly_fallback(raw_text)

    def _generate_fallback_response(self) -> ScriptResponse:
        return ScriptResponse(
            dialogues=[
                Dialogue(speaker="角色A", text="你好", position="center"),
                Dialogue(speaker="角色B", text="你也好", position="center")
            ],
            narrations=[
                Narration(text="这是一段旁白", position="top")
            ],
            actions=[
                Action(description="某人做了一个动作", position="bottom")
            ],
            characters=[{"name": "角色A", "description": "角色描述"}, {"name": "角色B", "description": "角色描述"}]
        )
