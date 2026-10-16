# Sesame — Home Assistant integration

Open the gates, doors and barriers managed by a [Sesame](https://github.com/ericguichard/hass-sesame)
access-control backend from Home Assistant, as native **button** entities — and,
through HA's bridges, from Apple Home and Google Home too.

The integration is **deployment-agnostic**: it talks only to your Sesame server's
HTTP API (`/api/integration/whoami` + `/api/ouvrir`), never to the relay hardware,
and it exposes one button **per access point your server reports** — whatever they
are called. Authorization, logging and the open-pulse stay in the backend where
they belong.

## What you get

- A **Sesame — \<your name\>** device with one **button** per access point your
  server exposes (the buttons are named from what the server returns; nothing is
  hard-coded in the integration).
- **Availability**: if your token is revoked or the server is unreachable, the
  buttons go *unavailable* instead of silently failing.
- **Seasonal closure** (0.4.0): when the server marks an access point as closed
  for the season, its button goes *unavailable* (greyed out) within one poll
  (1 min) and comes back on its own when the server reopens it. A press in
  between gets a clear "closed for the season" error, not a fault.
- **Unreachable equipment** (0.5.0): when the server's health probe reports an
  access point's on-site equipment as unreachable, its button goes *unavailable*
  within one poll (1 min) and comes back as soon as the server sees it again.
- **Re-authentication**: revoke a token and HA simply prompts you for a new one —
  no reconfiguration.
- **Re-exposure** to Apple Home / Google Home via HA's standard bridges.

> **Buttons, not locks.** Sesame exposes no open/closed state, so a `lock`/`cover`
> would show an invented state. A button is the honest object: press = momentary
> open. A press the backend refuses (or that can't reach the access point) surfaces
> as an error in HA.

## Install (via HACS)

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/ericguichard/hass-sesame`,
   category **Integration**.
2. Install **Sesame**, then restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → Sesame**.
4. Enter your **Sesame server URL** and an **API token**, then submit.

## Token & privacy

- Create an API token in your Sesame portal (under your account's API tokens). It
  is shown once at creation — paste it straight into HA.
- HA stores it encrypted in `.storage`; it is never logged or displayed again.
- Revoke it any time from the server (or an admin can): the buttons go unavailable
  and HA asks for a new token. Your HA config is never touched.

## Requirements

- Home Assistant **2024.12** or newer.
- A Sesame server that exposes the API-token feature and the
  `/api/integration/whoami` + `/api/ouvrir` endpoints.

## Status

`0.3.0` — public release. HA domain `sesame_gate` (`sesame` is taken by a core
integration). Scope: a button per access point, availability, and reauth. Out of
scope: open/closed-state entities, opening history in HA, and one HA instance
shared by multiple accounts (each account uses its own HA + token).

## License

[MIT](LICENSE).
