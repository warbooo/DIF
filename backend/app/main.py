from __future__ import annotations

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 加载环境变量
load_dotenv()

from .routes import auth, doc, history, doc_progress, ocr, ocr_evaluation, text_completion, user, logs, document_intelligence, pdf_processing, performance_analysis, async_tasks, sr_comparison, dashboard, evaluation, batch, sr_recommend, image_enhance
from .services.storage import init_storage
from .db.session import init_db
from .services.ocr_subprocess import close_ocr_service, get_ocr_service
from .services.ocr_postprocessing import get_post_processor
from .middleware.logging import LoggingMiddleware


app = FastAPI(title="DocIntelliFix", version="0.1.0")

# 允许前端开发阶段跨域（生产环境请收紧）
# 使用通配符允许所有来源（开发阶段）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # 使用通配符时不能为 True
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件（在 CORS 之后）
app.add_middleware(LoggingMiddleware)


@app.on_event("startup")
def on_startup() -> None:
    print("="*70)
    print("DocIntelliFix 启动中...")
    print("="*70)
    
    # 打印数据库配置
    from .core.settings import settings
    print(f"[Startup] 数据库配置：{settings.DATABASE_URL}")
    print(f"[Startup] 数据目录：{settings.DATA_DIR}")
    
    # 初始化存储和数据目录
    init_storage()
    init_db()
    
    # 预加载 AI 模型（避免第一次请求时的延迟）
    print("\n[Startup] 预加载 AI 模型...")
    
    # 预加载 Swin2SR 超分模型
    print("[Startup] 预加载 Swin2SR 超分模型...")
    try:
        from .services.swin2sr_service import Swin2SRService
        # 初始化超分服务（会自动加载模型）- 使用 RealWorldSR 作为默认
        swin2sr = Swin2SRService(sr_model_type="realworld", target_scale=4)
        if swin2sr.initialized and len(swin2sr.models) > 0:
            print("[Startup] OK Swin2SR 超分模型预加载完成！")
        else:
            print("[Startup] WARNING Swin2SR 超分模型未完全初始化，将在首次使用时加载")
    except Exception as e:
        print(f"[Startup] WARNING Swin2SR 超分模型预加载失败：{e}，将在首次使用时加载")
    
    # 预加载 OCR 模型
    print("[Startup] 预加载 OCR 模型...")
    ocr_service = get_ocr_service()  # 初始化 OCR 服务，预加载模型
    print("[Startup] OCR 模型预加载完成！")
    
    # 预加载 MacBERT 模型（用于文本补全和 OCR 后处理）
    # 用户配置：R9000P 2021H (RTX 3060)，GPU 显存充足，可以预加载
    print("[Startup] 预加载 PyCorrector MacBERT 模型...")
    try:
        from .services.ocr_postprocessing import get_spell_corrector
        corrector = get_spell_corrector()
        if corrector:
            print("[Startup] OK PyCorrector MacBERT 模型预加载完成！")
        else:
            print("[Startup] WARNING PyCorrector MacBERT 模型预加载失败，将在首次使用时加载")
    except Exception as e:
        print(f"[Startup] WARNING PyCorrector MacBERT 模型预加载失败：{e}，将在首次使用时加载")
    
    print("\n" + "="*70)
    print("✓ DocIntelliFix 启动完成 ✓")
    print("="*70)
    print("\n[Startup] 已预加载的模型：")
    print("  ✓ Swin2SR 超分模型（图片修复功能）")
    print("  ✓ RapidOCR 模型（OCR 识别功能）")
    print("  ✓ MacBERT 模型（文本补全和 OCR 后处理）")
    print("\n" + "="*70)


@app.on_event("shutdown")
def on_shutdown() -> None:
    print("\n" + "="*70)
    print("DocIntelliFix 关闭中...")
    print("="*70)
    
    # 关闭 AI 模型服务
    print("[Shutdown] 关闭 OCR 服务...")
    close_ocr_service()
    
    print("✓ 所有服务已关闭 ✓")
    print("="*70)

app.include_router(auth.router)
app.include_router(doc.router)
app.include_router(history.router)
app.include_router(doc_progress.router)
app.include_router(ocr.router)
app.include_router(ocr_evaluation.router)
app.include_router(text_completion.router)
app.include_router(user.router)
app.include_router(logs.router)
app.include_router(document_intelligence.router)
app.include_router(pdf_processing.router)
app.include_router(performance_analysis.router)
app.include_router(async_tasks.router)
app.include_router(sr_comparison.router)
app.include_router(dashboard.router)
app.include_router(evaluation.router)
app.include_router(batch.router)
app.include_router(sr_recommend.router)
app.include_router(image_enhance.router)
