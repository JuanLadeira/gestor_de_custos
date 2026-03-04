import factory

from app.tenant.models import Tenant


class TenantFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Tenant
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    nome = factory.Faker("company", locale="pt_BR")
    descricao = factory.Faker("catch_phrase", locale="pt_BR")
