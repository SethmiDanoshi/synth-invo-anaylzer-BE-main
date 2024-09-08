from django_cassandra_engine.models import DjangoCassandraModel
from cassandra.cqlengine import columns
import uuid
from datetime import datetime

class Invoice(DjangoCassandraModel):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    issuer = columns.UUID(default=uuid.uuid4)
    recipient = columns.UUID(default=uuid.uuid4)
    source_format = columns.Text()
    internal_format = columns.Text()
    created_at = columns.DateTime(default=datetime.now)
    archived = columns.Boolean(default=False)
    archived_at = columns.DateTime(default=None, required=False)
    archived_by = columns.Text(required=False)


