# BijMantra Keycloak Local Auth

This directory contains the local Keycloak realm import for the Keycloak authentication migration.

## Start

```bash
make dev-auth
```

Keycloak will be available at:

- Admin console: `http://localhost:8084/admin`
- Realm issuer: `http://localhost:8084/realms/bijmantra`
- JWKS: `http://localhost:8084/realms/bijmantra/protocol/openid-connect/certs`

Default local-only credentials:

- Keycloak bootstrap admin: `admin` / `admin`
- BijMantra realm user: `admin@bijmantra.org` / `Admin123!`

These credentials are for local development only. Production must override the bootstrap admin password and must not rely on the local realm import as-is.

The local realm import pins the BijMantra realm user's Keycloak subject to
`00000000-0000-4000-8000-000000000001`. The backend admin seeder maps that subject to the local
`admin@bijmantra.org` user through `auth_identities`, so local Keycloak tokens can resolve to the
same BijMantra organization and superuser account without guessing from email.

## Realm Contents

- Realm: `bijmantra`
- SPA client: `bijmantra-web`
  - Public client
  - Authorization code flow
  - PKCE S256
  - Redirect URI: `http://localhost:5656/*`
- API audience client: `bijmantra-api`
- Realm roles:
  - `bijmantra-admin`
  - `bijmantra-user`

## Backend Settings

The backend Keycloak verifier reads:

```text
KEYCLOAK_ENABLED=true
KEYCLOAK_ISSUER=http://localhost:8084/realms/bijmantra
KEYCLOAK_AUDIENCE=bijmantra-api
KEYCLOAK_JWKS_URL=http://localhost:8084/realms/bijmantra/protocol/openid-connect/certs
KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT=00000000-0000-4000-8000-000000000001
ALLOW_LOCAL_PASSWORD_LOGIN_IN_PRODUCTION=false
```

`ALLOW_LOCAL_PASSWORD_LOGIN_IN_PRODUCTION` must stay `false` for normal production operation. Set it
to `true` only as an explicit break-glass action for the legacy `/api/auth/login` password path.

## Frontend Settings

The React frontend enables Keycloak mode with:

```text
VITE_AUTH_PROVIDER=keycloak
VITE_KEYCLOAK_URL=http://localhost:8084
VITE_KEYCLOAK_REALM=bijmantra
VITE_KEYCLOAK_CLIENT_ID=bijmantra-web
```

When `VITE_AUTH_PROVIDER=keycloak` or `VITE_KEYCLOAK_ENABLED=true`, the browser uses the Keycloak
JavaScript adapter with authorization code flow and PKCE S256. The local password form is hidden unless
`VITE_LOCAL_PASSWORD_LOGIN_ENABLED=true` is set explicitly for a controlled break-glass or development path.

Do not enable this in production until a live Keycloak browser login/logout smoke is complete.
