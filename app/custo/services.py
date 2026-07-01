import hashlib
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.custo.importacao_nubank import LinhaFatura, parse_nubank_csv
from app.custo.models import Custo, TipoCusto
from app.custo.schemas import CustoCreate, CustoUpdate
from app.database import AsyncDBSession
from app.mes_referencia.services import MesReferenciaService


@dataclass
class ResultadoImport:
    criados: int
    ignorados: int
    meses_afetados: int


class CustoService:
    def __init__(self, session: AsyncSession, mes_service: MesReferenciaService | None = None):
        self.session = session
        self.mes_service = mes_service or MesReferenciaService(session)

    async def get_all(self, mes_referencia_id: int | None = None) -> list[Custo]:
        query = select(Custo).order_by(Custo.data_vencimento)
        if mes_referencia_id:
            query = query.where(Custo.mes_referencia_id == mes_referencia_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, custo_id: int) -> Custo | None:
        return await self.session.get(Custo, custo_id)

    async def get_scoped(self, custo_id: int, tenant_id: int) -> Custo | None:
        from app.mes_referencia.models import MesReferencia

        result = await self.session.execute(
            select(Custo)
            .join(MesReferencia, MesReferencia.id == Custo.mes_referencia_id)
            .where(Custo.id == custo_id, MesReferencia.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: CustoCreate) -> Custo:
        custo = Custo(
            descricao=data.descricao,
            valor=data.valor,
            data_vencimento=data.data_vencimento,
            tipo=data.tipo,
            mes_referencia_id=data.mes_referencia_id,
        )
        self.session.add(custo)
        await self.session.flush()
        await self.session.refresh(custo)
        return custo

    async def update(self, custo: Custo, data: CustoUpdate) -> Custo:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(custo, key, value)

        await self.session.flush()
        await self.session.refresh(custo)
        return custo

    async def delete(self, custo: Custo) -> None:
        await self.session.delete(custo)

    @staticmethod
    def _fingerprint(linha: LinhaFatura) -> str:
        base = f"{linha.data.isoformat()}|{linha.titulo}|{linha.valor}|{linha.ocorrencia}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    async def importar_fatura(self, conteudo: bytes, tenant_id: int) -> ResultadoImport:
        linhas = parse_nubank_csv(conteudo)
        criados = 0
        ignorados = 0
        meses: set[int] = set()
        for linha in linhas:
            mes = await self.mes_service.get_or_create(tenant_id, linha.data.year, linha.data.month)
            meses.add(mes.id)
            fp = self._fingerprint(linha)
            existe = await self.session.execute(
                select(Custo.id).where(
                    Custo.mes_referencia_id == mes.id, Custo.import_fingerprint == fp
                )
            )
            if existe.scalar_one_or_none() is not None:
                ignorados += 1
                continue
            self.session.add(Custo(
                descricao=linha.titulo,
                valor=linha.valor,
                data_vencimento=linha.data,
                tipo=TipoCusto.CARTAO_CREDITO,
                mes_referencia_id=mes.id,
                import_fingerprint=fp,
            ))
            await self.session.flush()
            criados += 1
        return ResultadoImport(criados=criados, ignorados=ignorados, meses_afetados=len(meses))


def get_custo_service(session: AsyncDBSession) -> CustoService:
    return CustoService(session)


CustoServiceDep = Annotated[CustoService, Depends(get_custo_service)]
