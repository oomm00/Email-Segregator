from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext


def test_migration_revisions():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    assert len(heads) >= 1
    assert "001" in heads


def test_migration_revision_order():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revisions = list(script.walk_revisions())
    assert len(revisions) >= 1
    assert revisions[-1].revision == "001"
    assert revisions[-1].down_revision is None
