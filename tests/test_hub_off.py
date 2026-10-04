"""The hub switch: with it on, nothing this install does reaches the central store."""
from types import SimpleNamespace

import pytest

from openoutreach import hub_off


@pytest.fixture
def service():
    """The finder's hub client, restored after each test — `apply` mutates the module."""
    from openoutfind.contacts import service as module

    saved = {name: getattr(module, name) for name in hub_off.PATCHED}
    yield module
    for name, value in saved.items():
        setattr(module, name, value)


@pytest.fixture
def wire(service, monkeypatch):
    """Record every HTTP call the hub client attempts, and give it a token to use."""
    calls = []

    def record(url, **kwargs):
        calls.append(url)
        return SimpleNamespace(status_code=500, json=lambda: {}, raise_for_status=lambda: None)

    monkeypatch.setattr(service.requests, "get", record)
    monkeypatch.setattr(service.requests, "post", record)
    config = SimpleNamespace(operator_country_code="US", contacts_api_token="tok")
    monkeypatch.setattr(service, "SiteConfig", SimpleNamespace(load=lambda: config))
    # `_register` asks who the operator is; answer without a database.
    monkeypatch.setattr(service, "get_active_user", lambda: SimpleNamespace(email="op@example.test"))
    return calls


LEAD = SimpleNamespace(profile_url="https://example.test/in/ann", country_code="US")


def test_without_the_switch_the_client_does_call_the_hub(service, wire, monkeypatch):
    """The control: proves the recorder would catch a call."""
    monkeypatch.delenv(hub_off.SWITCH, raising=False)

    assert hub_off.apply() is False
    service.resolve(LEAD)

    assert len(wire) == 1 and wire[0].startswith(service.HUB_URL)


def test_with_the_switch_no_request_reaches_the_hub(service, wire, monkeypatch):
    monkeypatch.setenv(hub_off.SWITCH, "off")

    assert hub_off.apply() is True
    assert service.resolve(LEAD) is None
    service.contribute(LEAD, ["ann@example.test"], "bettercontact")
    service.share_profiles([{"contact_linkedin_profile_url": LEAD.profile_url}], "US")
    assert service.register_operator() is False
    assert service._send("register", {"operator_email": "op@example.test"}) is None

    assert wire == []


def test_status_reports_the_switch(service, monkeypatch):
    monkeypatch.setenv(hub_off.SWITCH, "off")
    hub_off.apply()

    assert service.hub_balance() == {"balance": None, "known": False, "disabled": True}


def test_every_patched_name_still_exists_on_the_pinned_client():
    """A pin bump that renames one must fail here, not silently re-enable the hub."""
    from openoutfind.contacts import service as module

    for name in hub_off.PATCHED:
        assert callable(getattr(module, name)), name


def test_a_renamed_choke_point_refuses_to_run(service, monkeypatch):
    monkeypatch.setenv(hub_off.SWITCH, "off")
    monkeypatch.delattr(service, "_send")

    with pytest.raises(RuntimeError, match="_send"):
        hub_off.apply()

    monkeypatch.undo()


def test_every_verb_applies_the_switch(db, monkeypatch):
    from openoutreach import __main__ as cli

    applied = []
    monkeypatch.setattr(hub_off, "apply", lambda: applied.append(True) or True)

    cli._hand_the_children_their_environment()

    assert applied == [True]
