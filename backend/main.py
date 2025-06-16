from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as task_router


app = FastAPI(
    title="Kaka_Quant API",
    version="0.1.0",
    description="面向 Kaka_Quant 当前阶段任务的最小 FastAPI 封装层。",
)

# 第一版前端本地开发默认从 5173 端口访问，这里直接放开本地跨域即可。
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task_router)
