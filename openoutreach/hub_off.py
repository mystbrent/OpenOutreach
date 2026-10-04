"""The switch that keeps this install off the central contacts store.

`OPENOUTREACH_HUB=off` makes the finder's hub client a no-op for this process. The client
is `openoutfind.contacts.service`, a pinned dependency, so this replaces attributes on that
module rather than editing it.

Two of the three names are choke points. Every POST the client makes goes through `_send`,
and `resolve`, `contribute` and `share_profiles` all stop early when `token_in_hand`
answers "". Both are looked up as module globals at call time, so a caller that imported
`resolve` or `register_operator` by name before this ran is neutralised too. `hub_balance`
is replaced so that `status --json` says the switch is on — which is what a host program
checks before it trusts this install.
"""
import os

SWITCH = "OPENOUTREACH_HUB"

#: Every attribute `apply` replaces. `tests/test_hub_off.py` asserts each still exists on
#: the pinned client, so a rename upstream fails the suite instead of re-enabling the hub.
PATCHED = ("token_in_hand", "_send", "hub_balance")


def requested() -> bool:
    return os.environ.get(SWITCH, "").strip().lower() == "off"


def apply() -> bool:
    """Neutralise the hub client if the switch is on. Returns whether it was applied.

    Raises rather than continuing when a patched name is missing: running with half the
    switch applied is the one outcome nobody asked for.
    """
    if not requested():
        return False

    from openoutfind.contacts import service

    missing = [name for name in PATCHED if not hasattr(service, name)]
    if missing:
        raise RuntimeError(
            f"{SWITCH}=off cannot be honoured: openoutfind.contacts.service no longer has "
            + ", ".join(missing))

    service.token_in_hand = lambda config, *, mint=True: ""
    service._send = lambda path, body, lead=None, headers=None: None
    service.hub_balance = lambda: {"balance": None, "known": False, "disabled": True}
    return True
