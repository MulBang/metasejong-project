# scripts/build_faiss.py
import os
from typing import List, Dict
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# ─────────────────────────────────────────────────────────
# 0) ENV & 기본 경로
# ─────────────────────────────────────────────────────────
load_dotenv()
DB_URL = os.getenv("DB_URL")
VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", "db/faiss_index")

# 임베딩 백엔드: ollama | sentence | openai
EMBED_BACKEND = os.getenv("EMBED_BACKEND", "ollama").lower()
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://127.0.0.1:11434")


# ─────────────────────────────────────────────────────────
# 1) 임베딩 로더
# ─────────────────────────────────────────────────────────
def get_embeddings():
    """로컬-완전무료(ollama/sentence) 우선, 필요시 openai."""
    if EMBED_BACKEND == "ollama":
        # 권장: pip install -U langchain-ollama
        try:
            from langchain_ollama import OllamaEmbeddings  # 최신 패키지
        except ImportError:
            from langchain_community.embeddings import (  # 폴백
                OllamaEmbeddings,
            )
        return OllamaEmbeddings(base_url=OLLAMA_BASE, model=EMBED_MODEL)

    elif EMBED_BACKEND == "sentence":
        # pip install sentence-transformers
        from langchain_community.embeddings import HuggingFaceEmbeddings

        # EMBED_MODEL 예: "all-MiniLM-L6-v2"
        return HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    elif EMBED_BACKEND == "openai":
        # 유료; OPENAI_API_KEY 필요
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=EMBED_MODEL)

    else:
        raise RuntimeError(f"Unknown EMBED_BACKEND: {EMBED_BACKEND}")


# ─────────────────────────────────────────────────────────
# 2) DB에서 문서 재료 뽑기 (네 실제 스키마에 맞춤)
# ─────────────────────────────────────────────────────────
def fetch_rows() -> Dict[str, List[Dict]]:
    """
    menus: menus JOIN restaurants JOIN buildings
    pois : pois  JOIN buildings
    """
    eng = create_engine(DB_URL, pool_pre_ping=True, future=True)
    out: Dict[str, List[Dict]] = {"menus": [], "pois": []}

    with eng.connect() as cx:
        # menus + restaurants + buildings
        menus = (
            cx.execute(
                text(
                    """
                SELECT
                  m.id   AS menu_id,
                  m.name AS menu_name,
                  m.price AS menu_price,
                  r.id   AS restaurant_id,
                  r.name AS restaurant_name,
                  r.category AS restaurant_category,
                  b.id   AS building_id,
                  b.name AS building_name
                FROM menus m
                JOIN restaurants r ON r.id = m.restaurant_id
                JOIN buildings   b ON b.id = r.building_id
            """
                )
            )
            .mappings()
            .all()
        )
        out["menus"] = list(menus)

        # pois + buildings
        pois = (
            cx.execute(
                text(
                    """
                SELECT
                  p.id, p.label, p.x, p.y, p.node_id,
                  b.id AS building_id, b.name AS building_name
                FROM pois p
                JOIN buildings b ON b.id = p.building_id
            """
                )
            )
            .mappings()
            .all()
        )
        out["pois"] = list(pois)

    return out


# ─────────────────────────────────────────────────────────
# 3) 텍스트로 변환
# ─────────────────────────────────────────────────────────
def _s(v) -> str:
    return "" if v is None else str(v)


def to_documents(menus: List[Dict], pois: List[Dict]) -> List[Document]:
    docs: List[Document] = []

    # 메뉴 문서
    for r in menus:
        txt = (
            f"[MENU] 건물:{_s(r.get('building_name'))} | "
            f"식당:{_s(r.get('restaurant_name'))}({_s(r.get('restaurant_category'))}) | "
            f"메뉴:{_s(r.get('menu_name'))} | "
            f"가격:{_s(r.get('menu_price'))}"
        )
        docs.append(
            Document(
                page_content=txt,
                metadata={
                    "type": "menu",
                    "menu_id": r.get("menu_id"),
                    "restaurant_id": r.get("restaurant_id"),
                    "building_id": r.get("building_id"),
                },
            )
        )

    # POI 문서
    for r in pois:
        txt = (
            f"[POI] 건물:{_s(r.get('building_name'))} | "
            f"라벨:{_s(r.get('label'))} | "
            f"좌표:({_s(r.get('x'))},{_s(r.get('y'))})"
        )
        docs.append(
            Document(
                page_content=txt,
                metadata={
                    "type": "poi",
                    "poi_id": r.get("id"),
                    "building_id": r.get("building_id"),
                    "node_id": r.get("node_id"),
                },
            )
        )

    return docs


# ─────────────────────────────────────────────────────────
# 4) 메인: 임베딩 → FAISS 저장
# ─────────────────────────────────────────────────────────
def main():
    os.makedirs(VECTORSTORE_PATH, exist_ok=True)

    tables = fetch_rows()
    menus = tables["menus"]
    pois = tables["pois"]

    if not menus and not pois:
        print("[build_faiss] No data found in menus/pois. (docs=0)")

    docs = to_documents(menus, pois)
    print(
        f"[build_faiss] docs(menus={len(menus)}, pois={len(pois)}) → total={len(docs)}"
    )

    embeddings = get_embeddings()
    vs = FAISS.from_documents(docs, embeddings)
    vs.save_local(VECTORSTORE_PATH)
    print(f"[build_faiss] Saved FAISS index at: {VECTORSTORE_PATH}, docs={len(docs)}")


if __name__ == "__main__":
    main()
