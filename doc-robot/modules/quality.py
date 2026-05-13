from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


QUALITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个回答质量评估专家。请根据以下标准评估回答的质量：
    
    评估标准：
    1. 准确性：回答是否准确反映了参考资料中的信息
    2. 完整性：回答是否覆盖了问题的关键点
    3. 相关性：回答是否与用户问题相关
    4. 清晰度：回答是否清晰易懂
    
    请给出一个0-100的分数，并提供改进建议。"""),
    ("human", """参考资料：
{context}

用户问题：{question}

回答：{answer}

请评估这个回答的质量（0-100分），并提供改进建议。"""),
])

IMPROVE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个回答优化专家。请根据参考资料和评估意见，优化以下回答，使其更准确、完整、清晰。
    
    优化原则：
    1. 必须基于参考资料，不得编造信息
    2. 提高准确性和完整性
    3. 保持回答简洁易懂
    4. 引用来源文件名"""),
    ("human", """参考资料：
{context}

用户问题：{question}

原回答：{answer}

评估意见：{feedback}

请优化这个回答："""),
])


class AnswerEvaluator:
    """回答质量评估器"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            model=LLM_MODEL,
            temperature=0.1,
        )

    def evaluate(self, context: str, question: str, answer: str) -> dict:
        """评估回答质量"""
        chain = QUALITY_PROMPT | self.llm
        response = chain.invoke({
            "context": context,
            "question": question,
            "answer": answer,
        })
        
        result = response.content
        
        # 解析分数（假设格式包含 "分数: X"）
        score = 70  # 默认分数
        feedback = ""
        
        try:
            # 尝试提取分数
            lines = result.split("\n")
            for line in lines:
                if "分数" in line or "score" in line.lower():
                    import re
                    match = re.search(r"\d+", line)
                    if match:
                        score = int(match.group())
                else:
                    feedback += line + "\n"
        except:
            feedback = result
        
        return {
            "score": min(100, max(0, score)),
            "feedback": feedback.strip(),
        }

    def improve(self, context: str, question: str, answer: str, feedback: str) -> str:
        """优化回答"""
        chain = IMPROVE_PROMPT | self.llm
        response = chain.invoke({
            "context": context,
            "question": question,
            "answer": answer,
            "feedback": feedback,
        })
        return response.content


class QualityOptimizer:
    """回答质量优化器"""
    
    def __init__(self, min_score: int = 60):
        self.evaluator = AnswerEvaluator()
        self.min_score = min_score

    def optimize(self, context: str, question: str, answer: str) -> dict:
        """评估并优化回答"""
        evaluation = self.evaluator.evaluate(context, question, answer)
        score = evaluation["score"]
        feedback = evaluation["feedback"]
        
        if score < self.min_score:
            # 需要优化
            improved_answer = self.evaluator.improve(context, question, answer, feedback)
            return {
                "answer": improved_answer,
                "original_score": score,
                "optimized": True,
                "feedback": feedback,
            }
        else:
            return {
                "answer": answer,
                "original_score": score,
                "optimized": False,
                "feedback": feedback,
            }


_optimizer: QualityOptimizer | None = None


def get_optimizer() -> QualityOptimizer:
    global _optimizer
    if _optimizer is None:
        _optimizer = QualityOptimizer(min_score=60)
    return _optimizer