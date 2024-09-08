from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel
import uuid
from datetime import datetime
import json

class Template(DjangoCassandraModel):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    supplier = columns.UUID(default=uuid.uuid4)
    template_name = columns.Text()
    template_content = columns.Text()
    uploaded_at = columns.DateTime(default=datetime.now)
    mapping = columns.Text(default=None)
    created_at = columns.DateTime(default=datetime.now)
    mapped_status = columns.Boolean(default=False)
    mapped_by = columns.UUID(default = None)
    mapped_at = columns.DateTime(default=datetime.now)

    @property
    def mapping_dict(self):
        return json.loads(self.mapping) if self.mapping else {}
