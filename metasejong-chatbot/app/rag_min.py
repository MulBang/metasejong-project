import os
import re
from typing import Optional, Tuple, List, Dict, Iterable

# (선택) 벡터 스토어 — 없어도 동작
try:
    from langchain_community.vectorstores import FAISS  # noqa
except Exception:
    FAISS = None  # type: ignore

from langchain_core.prompts import ChatPromptTemplate

# ─────────────────────────────────────────────
# LLM (로컬 Ollama 우선) — 기본 모델: gemma3:4b
# ─────────────────────────────────────────────
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "1") == "1"
if USE_LOCAL_LLM:
    # 경고는 떠도 로컬 그대로
    from langchain_community.chat_models import ChatOllama as ChatModel

    _llm = ChatModel(
        base_url=os.getenv("OLLAMA_BASE", "http://127.0.0.1:11434"),
        model=os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        temperature=0.1,
    )
else:
    # 대비용(실행은 USE_LOCAL_LLM=1일 때 로컬만)
    from langchain_openai import ChatOpenAI as ChatModel

    _llm = ChatModel(model=os.getenv("GEN_MODEL", "gpt-4o-mini"), temperature=0.2)

# ─────────────────────────────────────────────
# Embedding/FAISS(선택)
# ─────────────────────────────────────────────
EMBED_BACKEND = os.getenv("EMBED_BACKEND", "ollama").lower()
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", "db/faiss_index")
DEBUG_RAG = os.getenv("DEBUG_RAG", "0") == "1"

_embeddings = None
_vstore = None
if FAISS is not None:

    def _build_embeddings():
        if EMBED_BACKEND == "ollama":
            try:
                from langchain_ollama import OllamaEmbeddings
            except ImportError:
                from langchain_community.embeddings import OllamaEmbeddings
            return OllamaEmbeddings(
                base_url=os.getenv("OLLAMA_BASE", "http://127.0.0.1:11434"),
                model=EMBED_MODEL,
            )
        elif EMBED_BACKEND == "sentence":
            from langchain_community.embeddings import HuggingFaceEmbeddings

            return HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        elif EMBED_BACKEND == "openai":
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(model=EMBED_MODEL)
        else:
            raise RuntimeError(f"Unknown EMBED_BACKEND: {EMBED_BACKEND}")

    try:
        _embeddings = _build_embeddings()
        _vstore = FAISS.load_local(
            VECTORSTORE_PATH, _embeddings, allow_dangerous_deserialization=True
        )
        print(f"[RAG] 🔎 FAISS loaded: {VECTORSTORE_PATH}")
    except Exception as e:
        print(f"[RAG] (info) FAISS not loaded or embeddings init failed: {e}")
        _vstore = None
else:
    _vstore = None

# ─────────────────────────────────────────────
# DB & 세션
# ─────────────────────────────────────────────
from app.nlu import expand_keywords_llm
from app.db import (
    search_menus_by_keywords,
    search_menu_candidates,
    get_dropoff_buildings,
    validate_dropoff_name,
)
from app.dialogue import get_session, Phase

# ▶ 미션 생성(선택적으로 호출 — 실패해도 사용자 메시지는 정상)
from app.db_mission import create_mission_from_selection

# ─────────────────────────────────────────────
# 0) 스몰토크/의도 키워드
# ─────────────────────────────────────────────
FOOD_HINTS = [
    "추천",
    "먹고싶",
    "먹을래",
    "든든",
    "간단",
    "매콤",
    "따뜻",
    "차가운",
    "시원",
    "덥",
    "덥다",
    "덥네",
    "밥",
    "면",
    "덮밥",
    "카레",
    "국",
    "라면",
    "모밀",
    "초밥",
    "돈까스",
    "달달",
    "디저트",
    "요거트",
    "그릭",
    "샐러드",
    "국물 없는",
    "국물없이",
    "국물 빼고",
]


def _has_food_intent(text: str) -> bool:
    t = (text or "").lower()
    return any(h in t for h in FOOD_HINTS)


def _is_small_talk(text: str) -> bool:
    """인사/감사만 있을 때만 True. 음식 의도와 함께면 False(추천 진행)."""
    if not text:
        return False
    t = text.strip().lower()
    GREET = {"안녕", "안녕하세요", "하이", "헬로", "hello", "hi"}
    THANKS = {"고마워", "감사", "감사합니다", "땡큐", "thanks", "thank you"}
    BYE = {"잘가", "안녕히계세요", "바이", "bye"}

    simple_small = any(t == kw or t.startswith(kw) for kw in list(GREET | THANKS | BYE))
    if not simple_small:
        return False
    return not _has_food_intent(text)


def _small_talk_reply(text: str) -> str:
    t = text.strip().lower()
    if "감사" in t or "고마워" in t or "thanks" in t:
        return "도움이 되어 기뻐요! 필요하시면 메뉴 추천도 해드릴게요. 🙂"
    if "안녕" in t or "hello" in t or "hi" in t or "하이" in t:
        return "안녕하세요! 오늘은 어떤 걸 드시고 싶으세요?"
    if "잘가" in t or "바이" in t or "bye" in t:
        return "좋은 하루 보내세요! 다음에 또 뵐게요. 👋"
    return (
        "안녕하세요! 편하게 말씀해 주세요. 원하시면 취향에 맞춰 메뉴도 추천해 드릴게요."
    )


# ─────────────────────────────────────────────
# 1) 공감 멘트(1~2문장, 고유명사/가격 금지)
# ─────────────────────────────────────────────
FORBIDDEN_TOKENS_HINT = [
    "원",
    "menu_id",
    "building",
    "chungmu",
    "dasan",
    "yeongsil",
    "parkinggate",
]


def _category_hint_from_text(user_text: str) -> str:
    t = (user_text or "").lower()
    if any(
        k in t
        for k in [
            "달달",
            "디저트",
            "단거",
            "스윗",
            "케익",
            "케이크",
            "요거트",
            "초코",
            "그릭",
        ]
    ):
        return "달콤한 디저트"
    if any(
        k in t for k in ["시원", "차가", "냉", "더워", "더운 날", "덥", "덥다", "덥네"]
    ):
        return "시원한 음식"
    if any(k in t for k in ["따뜻", "추워", "쌀쌀", "따땃", "뜨끈", "국물"]):
        return "따뜻한 국물 요리"
    if any(k in t for k in ["든든", "배부", "양 많", "포만감"]):
        return "든든한 식사"
    if any(k in t for k in ["가벼", "간단", "조금만", "샐러드", "다이어트"]):
        return "가벼운 식사"
    return ""


def _category_hint_from_menu(top: Dict) -> str:
    name = (top.get("menu_name") or "").lower()

    def has_any(words):
        return any(w in name for w in words)

    if has_any(["냉면", "물냉", "비빔냉", "냉우동", "소바", "모밀"]):
        return "시원한 면 요리"
    if has_any(["찌개", "탕", "국", "라면", "라멘", "우동", "순두부", "칼국수"]):
        return "따뜻한 국물 요리"
    if has_any(["카레", "덮밥", "동", "돈부리"]):
        return "든든한 덮밥"
    if has_any(["샐러드", "요거트", "그릭", "볼"]):
        return "가벼운 식사"
    return ""


def _sanitize_opening_line(s: str) -> str:
    if not s:
        return ""
    low = s.lower()
    if any(tok in low for tok in FORBIDDEN_TOKENS_HINT):
        return ""
    s = " ".join(s.split())
    parts = [p.strip() for p in re.split(r"[.!?]+", s) if p.strip()]
    if not parts:
        return ""
    clipped = " ".join([p + "." for p in parts[:2]])
    if len(clipped) > 220:
        clipped = clipped[:220].rstrip() + "…"
    return clipped


def _friendly_opening_generic(user_text: str, category_hint: str = "") -> str:
    sys = (
        "너는 한국어로 1~2문장만 말하는 도우미야. "
        "무조건 한국어와 존댓말을 사용해. "
        "사용자 말에 자연스럽게 반응하고, 대략적인 음식 종류(예: 따뜻한 국물 요리, 시원한 면 요리 등)만 언급해. "
        "구체적인 메뉴명/식당명/건물명/가격/수치를 언급하지 마. "
        "문장 끝은 마침표, 이모지는 최대 1개."
    )
    hint_line = f"\n권장 카테고리(선택): {category_hint}" if category_hint else ""
    human = f"사용자 입력: {user_text}{hint_line}\n조건을 지켜 1~2문장으로."
    try:
        msg = ChatPromptTemplate.from_messages(
            [("system", sys), ("human", human)]
        ).format_messages()
        out = _llm.invoke(msg).content.strip()
        out = _sanitize_opening_line(out)
        if out:
            return out
    except Exception:
        pass
    return "취향을 반영해서 추천해 드릴게요!"


def _opening(user_text: str, category_hint: str = "") -> str:
    try:
        return _friendly_opening_generic(user_text, category_hint=category_hint)
    except Exception:
        return "요청 이해했어요. 취향에 맞춰 추천을 준비해볼게요!"


# ─────────────────────────────────────────────
# 2) 추천 블록(메인 1 + 대안 1) — menu_id 제거
# ─────────────────────────────────────────────
def _pick_one_alternative(menu_rows: List[Dict]) -> Optional[Dict]:
    if len(menu_rows) < 2:
        return None
    top = menu_rows[0]
    tb, tr = top["building_name"], top["restaurant_name"]
    for r in menu_rows[1:]:
        if r["building_name"] == tb and r["restaurant_name"] != tr:
            return r
    for r in menu_rows[1:]:
        if r["building_name"] == tb and r["restaurant_name"] == tr:
            return r
    return menu_rows[1]


def _render_recommend_block(rows: List[Dict]) -> str:
    if not rows:
        return "등록된 메뉴에서 관련 항목을 찾지 못했어요. 건물/식당/메뉴 특징을 조금 더 알려주실까요?"
    main = rows[0]
    rec = f"추천: {main['building_name']} {main['restaurant_name']}의 {main['menu_name']} / {main['price']}원"
    alt = _pick_one_alternative(rows)
    alt_line = ""
    if alt:
        if (
            alt["building_name"] == main["building_name"]
            and alt["restaurant_name"] == main["restaurant_name"]
        ):
            alt_line = f"\n아니면 {alt['menu_name']}({alt['price']}원)는 어떠신가요?"
        elif alt["building_name"] == main["building_name"]:
            alt_line = f"\n아니면 {alt['restaurant_name']}의 {alt['menu_name']}({alt['price']}원)는 어떠신가요?"
        else:
            alt_line = f"\n아니면 {alt['building_name']} {alt['restaurant_name']}의 {alt['menu_name']}({alt['price']}원)는 어떠신가요?"
    guide = "\n\n마음에 드는 메뉴명을 그대로 말씀해 주세요."
    return rec + alt_line + guide


# ─────────────────────────────────────────────
# 3) 후보 중 '메뉴명으로 선택'
# ─────────────────────────────────────────────
def _pick_from_candidates_by_name(utter: str, cands: List[Dict]) -> Optional[Dict]:
    if not utter or not cands:
        return None
    u = "".join(utter.lower().split())
    scored: List[Tuple[int, Dict]] = []
    for r in cands:
        key = "".join(str(r.get("menu_name", "")).lower().split())
        if key and key in u:
            scored.append((len(key), r))
    if not scored:
        return None
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[0][1]


# ─────────────────────────────────────────────
# 3.5) 의도 플래그 + 재정렬
# ─────────────────────────────────────────────
def _detect_intent_flags(text: str) -> Dict[str, bool]:
    t = (text or "").lower()
    return {
        "want_cold": any(
            k in t for k in ["시원", "차가", "냉", "더워", "덥", "덥다", "덥네"]
        ),
        "want_warm": any(k in t for k in ["따뜻", "추워", "쌀쌀", "뜨끈", "국물"]),
        "no_soup": any(k in t for k in ["국물 없는", "국물없이", "국물 빼고"]),
        "sweet": any(
            k in t
            for k in ["달달", "단거", "디저트", "요거트", "그릭", "초코", "케이크"]
        ),
        "hearty": any(k in t for k in ["든든", "배부", "양 많", "포만감"]),
        "light": any(k in t for k in ["가벼", "간단", "조금만", "샐러드", "다이어트"]),
    }


def _rerank(
    rows: List[Dict], keywords: List[str], intent: Dict[str, bool] | None = None
) -> List[Dict]:
    if not rows:
        return rows
    intent = intent or {}
    boosts, penalties = [], []

    if intent.get("want_cold"):
        boosts += [
            "냉",
            "냉면",
            "물냉",
            "비빔냉",
            "모밀",
            "소바",
            "냉우동",
            "샐러드",
            "요거트",
            "그릭",
            "아이스",
        ]
        penalties += [
            "찌개",
            "탕",
            "국",
            "국물",
            "라면",
            "라멘",
            "우동",
            "칼국수",
            "뜨끈",
            "순두부",
        ]
    if intent.get("want_warm"):
        boosts += [
            "찌개",
            "탕",
            "국",
            "국물",
            "라면",
            "라멘",
            "우동",
            "칼국수",
            "순두부",
            "뜨끈",
            "따뜻",
        ]
    if intent.get("no_soup"):
        penalties += [
            "찌개",
            "탕",
            "국",
            "국물",
            "라면",
            "라멘",
            "우동",
            "칼국수",
            "순두부",
        ]
    if intent.get("sweet"):
        boosts += ["요거트", "그릭", "디저트", "초코", "쿠키", "케이크"]
    if intent.get("hearty"):
        boosts += ["덮밥", "카레", "정식", "한식", "비빔밥", "돈까스", "함박"]
    if intent.get("light"):
        boosts += ["샐러드", "요거트", "그릭", "볼", "라이트"]

    def _score_row(row: Dict) -> int:
        fields = " ".join(
            str(x)
            for x in [
                row.get("menu_name", ""),
                row.get("restaurant_name", ""),
                row.get("restaurant_category", ""),
                row.get("building_name", ""),
            ]
        ).lower()
        s = 0
        for kw in keywords or []:
            k = str(kw).lower().strip()
            if not k:
                continue
            if k in fields:
                s += 3
            s += sum(1 for tok in fields.split() if k == tok)
        for b in boosts:
            if b and b in fields:
                s += 5
        for p in penalties:
            if p and p in fields:
                s -= 4
        return s

    try:
        scored = [(_score_row(r), r) for r in rows]
        scored.sort(key=lambda x: (-x[0], x[1].get("menu_id", 0)))
        return [r for _, r in scored]
    except Exception:
        return rows


# ─────────────────────────────────────────────
# 4) 메인 핸들러
# ─────────────────────────────────────────────
async def handle_chat(text: str, user_xy: Optional[Tuple[float, float]] = None):
    # 0) 스몰토크 (인사/감사만)
    if _is_small_talk(text):
        return {"type": "answer", "content": _small_talk_reply(text)}

    sid = "single"
    st = get_session(sid)
    phase = st.get("phase", Phase.RECOMMEND)

    # ── RECOMMEND
    if phase == Phase.RECOMMEND:
        try:
            kw = expand_keywords_llm(text)
        except Exception:
            kw = [text]

        try:
            menu_rows = await search_menus_by_keywords(kw, top_k=12)
        except Exception:
            menu_rows = await search_menu_candidates(text, top_k=12)

        intent = _detect_intent_flags(text)
        menu_rows = _rerank(menu_rows, kw, intent=intent)

        if DEBUG_RAG:
            print("[RAG][input]", text)
            print("[RAG][menus]", len(menu_rows), menu_rows[:3] if menu_rows else None)

        if not menu_rows:
            cat_hint = _category_hint_from_text(text)
            opening = _opening(text, category_hint=cat_hint)
            body = "등록된 메뉴에서 관련 항목을 찾지 못했어요. 건물/식당/메뉴 특징을 조금 더 알려주실까요?"
            return {"type": "answer", "content": f"{opening}\n\n{body}"}

        st["candidates"] = menu_rows
        st["phase"] = Phase.CONFIRM_ORDER

        cat_hint = _category_hint_from_text(text) or _category_hint_from_menu(
            menu_rows[0]
        )
        opening = _opening(text, category_hint=cat_hint)
        block = _render_recommend_block(menu_rows)
        return {"type": "answer", "content": f"{opening}\n\n{block}"}

    # ── CONFIRM_ORDER
    elif phase == Phase.CONFIRM_ORDER:
        chosen = _pick_from_candidates_by_name(text, st.get("candidates", []))

        if not chosen:
            text_norm = text.strip().lower()
            is_new_intent = (
                any(h in text_norm for h in FOOD_HINTS) and len(text_norm) >= 2
            )
            if is_new_intent:
                try:
                    kw = expand_keywords_llm(text)
                except Exception:
                    kw = [text]
                try:
                    menu_rows = await search_menus_by_keywords(kw, top_k=12)
                except Exception:
                    menu_rows = await search_menu_candidates(text, top_k=12)
                intent = _detect_intent_flags(text)
                menu_rows = _rerank(menu_rows, kw, intent=intent)
                if menu_rows:
                    st["candidates"] = menu_rows
                    st["phase"] = Phase.CONFIRM_ORDER
                    cat_hint = _category_hint_from_text(
                        text
                    ) or _category_hint_from_menu(menu_rows[0])
                    opening = _opening(text, category_hint=cat_hint)
                    block = _render_recommend_block(menu_rows)
                    return {"type": "answer", "content": f"{opening}\n\n{block}"}

        if chosen:
            st["menu_choice"] = chosen
            st["phase"] = Phase.DISPATCH
            msg = (
                f"→ {chosen['building_name']} {chosen['restaurant_name']}의 "
                f"{chosen['menu_name']} / {chosen['price']}원\n\n"
                f"이 메뉴로 주문할까요? (네/아니오)"
            )
            return {"type": "answer", "content": msg}

        cands = st.get("candidates", [])[:3]
        hint = ", ".join(c["menu_name"] for c in cands) if cands else ""
        return {
            "type": "answer",
            "content": (
                "어떤 메뉴로 할지 메뉴명으로 말씀해 주세요."
                + (f"\n후보 힌트: {hint}" if hint else "")
            ),
        }

    # ── DISPATCH
    elif phase == Phase.DISPATCH:
        ans = text.strip().lower()
        yes_words = {"네", "예", "응", "좋아", "ㅇㅋ", "ok", "그래", "맞아"}
        no_words = {"아니오", "아니", "노", "싫어", "취소"}

        if ans in yes_words:
            st["phase"] = Phase.ASK_PICKUP
            drops = await get_dropoff_buildings()
            if drops:
                names = ", ".join(d["name"] for d in drops)
                return {
                    "type": "answer",
                    "content": f"좋습니다. 수령하실 건물 이름을 알려주세요. ({names})",
                }
            else:
                return {
                    "type": "answer",
                    "content": "수령 가능한 드롭오프 건물 정보가 없어요.",
                }

        if ans in no_words:
            st["phase"] = Phase.RECOMMEND
            return {
                "type": "answer",
                "content": "알겠어요. 다시 추천해볼게요. 원하시는 키워드를 말해 주세요!",
            }

        return {"type": "answer", "content": "주문을 진행할까요? (네/아니오)"}

    # ── ASK_PICKUP
    elif phase == Phase.ASK_PICKUP:
        b = await validate_dropoff_name(text.strip())
        if not b:
            return {
                "type": "answer",
                "content": "죄송해요, 해당 건물을 찾지 못했어요. 드롭오프 건물 이름을 정확히 알려주세요.",
            }

        chosen = st.get("menu_choice")

        # ▶ (선택) 실제 미션 생성 시도 — 실패해도 사용자 메시지는 동일하게 제공
        try:
            _ = await create_mission_from_selection(
                user_msg=f"chatbot_order:{chosen['menu_name']}",
                menu_id=chosen.get("menu_id"),
                restaurant_id=chosen.get("restaurant_id"),
                pickup_poi_id=None,  # 자동
                dropoff_poi_id=None,  # 자동
                dropoff_building_id=b["id"],
                user_xy=user_xy,
            )
        except Exception:
            pass

        st["phase"] = Phase.RECOMMEND  # 다음 대화를 위해 초기화

        # ✅ 요청한 포맷으로 변경
        return {
            "type": "answer",
            "content": (
                f"[{chosen['restaurant_name']}/{chosen['building_name']}] -> [{b['name']}]\n"
                f"배달 시작할게요!"
            ),
        }

    # 안전망
    st["phase"] = Phase.RECOMMEND
    return {
        "type": "answer",
        "content": "처음부터 다시 도와드릴게요. 무엇을 드시고 싶으세요?",
    }
