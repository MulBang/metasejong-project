# app/nlu.py
import json
from typing import List
import os

USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "1") == "1"
if USE_LOCAL_LLM:
    from langchain_community.chat_models import ChatOllama as ChatModel

    _llm = ChatModel(
        base_url=os.getenv("OLLAMA_BASE", "http://127.0.0.1:11434"),
        model=os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        temperature=0.1,
    )
else:
    from langchain_openai import ChatOpenAI as ChatModel

    _llm = ChatModel(model=os.getenv("GEN_MODEL", "gpt-4o-mini"), temperature=0.2)

PROMPT = (
    "너는 사용자의 음식 의도를 키워드로 추출하는 역할이야. "
    "예를 들어 '덮밥이 먹고 싶어' → ['덮밥','카레','돈부리','라이스','라이스볼'] "
    "‘초밥’ → ['초밥','스시','사시미','연어','광어'] 처럼, "
    "동의어나 유사 카테고리 3~7개를 한글 위주로 JSON 배열로만 출력해. "
    "설명 금지, 예시 금지, 말줄임표 금지. 반드시 JSON 배열만."
)


def expand_keywords_llm(text: str) -> List[str]:
    msg = [("system", PROMPT), ("user", text.strip())]
    try:
        out = _llm.invoke(msg).content.strip()
        arr = json.loads(out)
        # 문자열만 필터
        return [str(x).strip() for x in arr if isinstance(x, (str,))]
    except Exception:
        # 실패 시 최소한 원문만
        return [text.strip()]
