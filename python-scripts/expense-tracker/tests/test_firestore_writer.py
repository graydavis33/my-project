import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-unit-tests")

import firestore_writer


class FakeDoc:
    def __init__(self, store, path): self.store, self.path = store, path
    def create(self, data):
        if self.path in self.store:
            raise firestore_writer.AlreadyExists("exists")
        self.store[self.path] = data

class FakeClient:
    def __init__(self): self.store = {}
    def document(self, path): return FakeDoc(self.store, path)


def _exp(eid="e1", **kw):
    d = {"email_id": eid, "date": "2026-07-07", "vendor": "Bodega", "amount": 12.0, "category": "Misc"}
    d.update(kw); return d

def test_writes_new_expense():
    c = FakeClient()
    n = firestore_writer.write_expenses([_exp()], client=c)
    assert n == 1
    doc = c.store["households/gray/transactions/e1"]
    assert doc["vendor"] == "Bodega" and doc["deleted"] is False
    assert doc["month"] == "2026-07" and doc["source"] == "gmail"
    assert "is_alert" not in doc  # internal flag not persisted

def test_skips_existing_doc():
    c = FakeClient()
    firestore_writer.write_expenses([_exp()], client=c)
    n = firestore_writer.write_expenses([_exp(vendor="Changed")], client=c)
    assert n == 0
    assert c.store["households/gray/transactions/e1"]["vendor"] == "Bodega"  # never overwritten

def test_no_env_returns_none_client():
    os.environ.pop("FIREBASE_SERVICE_ACCOUNT", None)
    assert firestore_writer.get_client() is None
