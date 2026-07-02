import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.admin import router as admin_router
from app.assinatura import router as assinatura_router
from app.auth import router as auth_router
from app.custo import router as custo_router
from app.custo_fixo import router as custo_fixo_router
from app.logger import logger
from app.settings import Settings
from app.mes_referencia import router as mes_referencia_router
from app.pagamento_rateio import router as pagamento_rateio_router
from app.plano import router as plano_router
from app.stripe_webhooks import router as stripe_router
from app.tenant import router as tenant_router
from app.whatsapp import router as whatsapp_router
from app.usuario import router as usuario_router
from app.campanha import router as campanha_router
from app.authz import router as authz_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando a aplicacao Gestor de Custos...")
    yield
    logger.info("Encerrando a aplicacao Gestor de Custos...")


app = FastAPI(
    title="Gestor de Custos Compartilhados",
    description="API para gestao de custos compartilhados entre usuarios",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://frontend:5173",  # Docker service name
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(plano_router.router)
app.include_router(assinatura_router.router)
app.include_router(stripe_router.router)
app.include_router(tenant_router.router)
app.include_router(usuario_router.router)
app.include_router(authz_router.router)
app.include_router(mes_referencia_router.router)
app.include_router(custo_fixo_router.router)
app.include_router(custo_router.router)
app.include_router(pagamento_rateio_router.router)
app.include_router(whatsapp_router.router)
app.include_router(campanha_router.router)

settings = Settings()
os.makedirs(os.path.join(settings.UPLOAD_DIR, "comprovantes"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
