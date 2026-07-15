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


# --- extended fake supporting set/get for cursor + tombstones ---
class FakeSnap:
    def __init__(self, data): self._d = data
    @property
    def exists(self): return self._d is not None
    def to_dict(self): return self._d or {}

class FakeDoc2:
    def __init__(self, store, path): self.store, self.path = store, path
    def create(self, data):
        if self.path in self.store: raise firestore_writer.AlreadyExists("exists")
        self.store[self.path] = data
    def set(self, data): self.store[self.path] = data
    def get(self): return FakeSnap(self.store.get(self.path))

class FakeQuery:
    def __init__(self, store, col): self.store, self.col = store, col
    def where(self, field, op, value):
        self._field, self._value = field, value; return self
    def stream(self):
        for path, data in self.store.items():
            if path.startswith(self.col + "/") and data.get(self._field) == self._value:
                yield FakeSnap(data)

class FakeClient2:
    def __init__(self): self.store = {}
    def document(self, path): return FakeDoc2(self.store, path)
    def collection(self, path): return FakeQuery(self.store, path)

def _rec(sid, source, amount=10.0, month="2026-07"):
    return {"vendor": "V", "amount": amount, "category": "Misc", "date": month + "-05",
            "month": month, "source": source}

def test_write_expenses_honors_source():
    c = FakeClient()
    firestore_writer.write_expenses([_exp(source="plaid", email_id="plaid_x")], client=c)
    assert c.store["households/gray/transactions/plaid_x"]["source"] == "plaid"

def test_fetch_non_gmail_includes_plaid_and_manual():
    c = FakeClient2()
    c.store["households/gray/transactions/g1"] = _rec("g1", "gmail")
    c.store["households/gray/transactions/plaid_p1"] = _rec("plaid_p1", "plaid")
    c.store["households/gray/transactions/m1"] = _rec("m1", "manual")
    out = firestore_writer.fetch_non_gmail_transactions("2026-07", client=c)
    sources = sorted(r["source"] for r in out)
    assert sources == ["manual", "plaid"]

def test_fetch_manual_only_excludes_plaid():
    c = FakeClient2()
    c.store["households/gray/transactions/plaid_p1"] = _rec("plaid_p1", "plaid")
    c.store["households/gray/transactions/m1"] = _rec("m1", "manual")
    out = firestore_writer.fetch_manual_only_transactions("2026-07", client=c)
    assert [r["source"] for r in out] == ["manual"]

def test_cursor_roundtrip():
    c = FakeClient2()
    assert firestore_writer.read_cursor(client=c) == ""
    firestore_writer.write_cursor("CURSOR_ABC", client=c)
    assert firestore_writer.read_cursor(client=c) == "CURSOR_ABC"

def test_tombstone_removed_marks_deleted():
    c = FakeClient2()
    c.store["households/gray/transactions/plaid_p1"] = _rec("plaid_p1", "plaid")
    n = firestore_writer.tombstone_removed(["p1"], client=c)
    assert n == 1
    assert c.store["households/gray/transactions/plaid_p1"]["deleted"] is True
