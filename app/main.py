from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.custo import router as custo_router
from app.custo_fixo import router as custo_fixo_router
from app.logger import logger
from app.mes_referencia import router as mes_referencia_router
from app.pagamento_rateio import router as pagamento_rateio_router
from app.tenant import router as tenant_router
from app.usuario import router as usuario_router


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
app.include_router(tenant_router.router)
app.include_router(usuario_router.router)
app.include_router(mes_referencia_router.router)
app.include_router(custo_fixo_router.router)
app.include_router(custo_router.router)
app.include_router(pagamento_rateio_router.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
