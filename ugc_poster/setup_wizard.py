"""One-time setup: turns a short-lived token from Meta's Graph API Explorer into a
long-lasting Page access key, finds the linked Instagram account, and saves settings.json."""

import json

from .graph import DEFAULT_VERSION, Graph, PosterError


def run_setup(settings_path, ask=input, graph_cls=Graph):
    print("UGC poster setup. Follow docs/meta-setup.md to get these three values.")
    print("Don't send screenshots of this window to anyone: the keys work like passwords.\n")
    app_id = ask("App ID: ").strip()
    if not app_id.isdigit():
        raise PosterError("The App ID is only numbers (App settings -> Basic). "
                          "If you pasted a long code starting with EAA, that's the access token.")
    app_secret = ask("App Secret: ").strip()
    short_token = ask("Access token from Graph API Explorer: ").strip()
    if not (app_id and app_secret and short_token):
        raise PosterError("All three values are needed.")

    long_token = graph_cls(None).get(
        "oauth/access_token", grant_type="fb_exchange_token", client_id=app_id,
        client_secret=app_secret, fb_exchange_token=short_token,
    )["access_token"]
    # Page tokens fetched with a long-lived user token don't expire.
    pages = graph_cls(long_token).get(
        "me/accounts", fields="id,name,access_token,instagram_business_account{id,username}"
    ).get("data", [])
    if not pages:
        raise PosterError("No Facebook Pages found. Make sure you ticked your Page when generating the token.")

    if len(pages) == 1:
        page = pages[0]
    else:
        for n, p in enumerate(pages, 1):
            print(f"  {n}. {p['name']}")
        choice = ask("Which Page should videos post to? Type its number: ").strip()
        if not choice.isdigit() or not 1 <= int(choice) <= len(pages):
            raise PosterError("That isn't one of the numbers listed.")
        page = pages[int(choice) - 1]

    ig = page.get("instagram_business_account") or {}
    settings = {
        "graph_api_version": DEFAULT_VERSION,
        "page_id": page["id"],
        "page_name": page["name"],
        "instagram_user_id": ig.get("id", ""),
        "instagram_username": ig.get("username", ""),
        "access_token": page["access_token"],
        "platforms": {"instagram": bool(ig), "facebook": True},
        "share_to_feed": True,
    }
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")

    print(f"\nSaved. Facebook Page: {page['name']}")
    if ig:
        print(f"Instagram account: @{ig.get('username', ig['id'])}")
    else:
        print("No Instagram account is linked to this Page, so only Facebook will be used.")
        print("Link your Instagram to the Page (see docs/meta-setup.md) and run setup again.")
    return settings
