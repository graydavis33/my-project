# plaid_client.py
"""Thin read-only wrapper over the Plaid Transactions API. All decision logic
lives in plaid_sync/category_map; this only talks to Plaid."""

import os
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

_ENVS = {"sandbox": plaid.Environment.Sandbox, "production": plaid.Environment.Production}


def _api():
    cfg = plaid.Configuration(
        host=_ENVS[os.getenv("PLAID_ENV", "production")],
        api_key={"clientId": os.environ["PLAID_CLIENT_ID"], "secret": os.environ["PLAID_SECRET"]},
    )
    return plaid_api.PlaidApi(plaid.ApiClient(cfg))


def create_link_token():
    req = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="gray"),
        client_name="Payday Checklist",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en",
    )
    return _api().link_token_create(req).link_token


def exchange_public_token(public_token):
    req = ItemPublicTokenExchangeRequest(public_token=public_token)
    return _api().item_public_token_exchange(req).access_token


def sync_transactions(access_token, cursor=""):
    """Page /transactions/sync to exhaustion. Returns (added, removed_ids, next_cursor).
    'modified' are folded into 'added' (create-only write skips ones already stored)."""
    added, removed = [], []
    api = _api()
    while True:
        kwargs = {"access_token": access_token}
        if cursor:
            kwargs["cursor"] = cursor
        resp = api.transactions_sync(TransactionsSyncRequest(**kwargs))
        added += [t.to_dict() for t in resp.added]
        added += [t.to_dict() for t in resp.modified]
        removed += [t.transaction_id for t in resp.removed]
        cursor = resp.next_cursor
        if not resp.has_more:
            break
    return added, removed, cursor
