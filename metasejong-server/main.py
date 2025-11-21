from fastapi import FastAPI
from routers import status as status_router
from routers import graph as graph_router
from routers import mcp as mcp_router  # mcp 라우터 임포트

# 1) 먼저 앱을 만든다
app = FastAPI(title="MetaSejong API", version="0.1.0")

# 2) 그 다음 라우터들을 등록한다
app.include_router(status_router.router)
app.include_router(graph_router.router)
app.include_router(mcp_router.router)


# 3) 선택: 루트 엔드포인트
@app.get("/")
def root():
    return {"ok": True}
