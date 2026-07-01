"""Aggregate import of every ORM model.

Importing this module guarantees that all mapper classes are registered with
SQLAlchemy's registry, so string-based ``relationship()`` targets (e.g.
``Custo.mes_referencia -> "MesReferencia"``) can be resolved. The FastAPI app
registers everything transitively through its routers, but Celery workers have a
narrower import graph, so they import this module explicitly at boot.
"""

from app.admin import models as admin_models  # noqa: F401
from app.assinatura import models as assinatura_models  # noqa: F401
from app.authz import models as authz_models  # noqa: F401
from app.campanha import models as campanha_models  # noqa: F401
from app.custo import models as custo_models  # noqa: F401
from app.custo_fixo import models as custo_fixo_models  # noqa: F401
from app.mes_referencia import models as mes_referencia_models  # noqa: F401
from app.pagamento_rateio import models as pagamento_rateio_models  # noqa: F401
from app.plano import models as plano_models  # noqa: F401
from app.tenant import models as tenant_models  # noqa: F401
from app.usuario import models as usuario_models  # noqa: F401
from app.whatsapp import models as whatsapp_models  # noqa: F401
