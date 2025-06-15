from fastapi import FastAPI

from backend.api.routes import router as task_router


app = FastAPI(
    title="Kaka_Quant API",
    version="0.1.0",
    description="面向 Kaka_Quant 当前阶段任务的最小 FastAPI 封装层。",
)

app.include_router(task_router)
