import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("EMBEDDING_BACKEND", "tfidf")
os.environ["LLM_PROVIDER"] = "none"
os.environ["LLM_API_KEY"] = ""
os.environ.setdefault("PYTHONHASHSEED", "0")

import pytest

from app.expert_system.knowledge_base import KnowledgeBase
from app.expert_system.service import ComplianceService
from app.schemas.facts import Fact, FactStore


@pytest.fixture(scope="session")
def kb() -> KnowledgeBase:
    return KnowledgeBase.from_file()


@pytest.fixture(scope="session")
def service(kb: KnowledgeBase) -> ComplianceService:
    return ComplianceService(kb)


def make_store(**facts) -> FactStore:
    store = FactStore()
    for name, item in facts.items():
        if isinstance(item, tuple):
            value, unit = item
        else:
            value, unit = item, None
        store.add(Fact(name=name, value=value, unit=unit))
    return store


@pytest.fixture
def facts_factory():
    return make_store
