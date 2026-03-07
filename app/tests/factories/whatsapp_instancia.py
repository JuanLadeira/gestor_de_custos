import factory

from app.tests.factories.tenant import TenantFactory
from app.whatsapp.models import ConexaoStatus, WhatsappInstancia


class WhatsappInstanciaFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = WhatsappInstancia
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    instance_name = factory.Sequence(lambda n: f"instancia-{n}")
    status = ConexaoStatus.CRIADA
    tenant = factory.SubFactory(TenantFactory)
    tenant_id = factory.LazyAttribute(lambda obj: obj.tenant.id)
