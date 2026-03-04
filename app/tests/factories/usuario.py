import factory

from app.tests.factories.tenant import TenantFactory
from app.usuario.models import Usuario


class UsuarioFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Usuario
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    password = factory.Faker("password")
    nome = factory.Faker("name", locale="pt_BR")
    ativo = True
    tenant = factory.SubFactory(TenantFactory)
    tenant_id = factory.LazyAttribute(lambda obj: obj.tenant.id)
