# Google Earth Engine (GEE) Authentication Guide

## ❓ The Question: API Key vs. OAuth2?

You asked: _"Will there be like an api key... or how will it work?"_

**Short Answer:** No, Earth Engine **cannot** be accessed with just a simple API Key (like Google Maps). It requires **OAuth2 Authentication**.

### Why?

- **Google Maps** (Client-side): Uses an API Key because it's public-facing and restricted by domain (referer).
- **Earth Engine** (Server-side/Analysis): involves heavy computation. Google requires stricter identity verification to prevent abuse and manage quotas.

---

## 🛠️ How to Set It Up

There are two main ways to handle this in BijMantra:

### Option A: Service Account (Recommended for Platforms)

This method allows your backend to "proxy" the request. The user doesn't need a GEE account; the **App** has the account.

1.  **Create Service Account**:
    - Go to [Google Cloud Console > IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
    - Click **Create Service Account**.
    - Name it (e.g., `bijmantra-earth-engine`).
    - Grant it the **Earth Engine Resource Viewer** role.
2.  **Generate Key**:
    - Click the service account > **Keys** > **Add Key** > **Create new key** (JSON).
    - Download the JSON file.
3.  **Register Service Account in GEE**:
    - Go to [Earth Engine Code Editor](https://code.earthengine.google.com/).
    - Register the service account email (ending in `.iam.gserviceaccount.com`) as a user (checking "I am a developer").
4.  **Implementation**:
    - Your **Python Backend** uses this JSON key to generate a "short-lived access token".
    - The Frontend requests this token from your backend API (`/api/auth/gee-token`).
    - Frontend calls `EarthEngineService.initialize(token)`.

### Option B: Client-Side OAuth (Quickest for Testing)

This forces the _user_ to log in with their own Google Account.

1.  **Create OAuth Client ID**:
    - Go to [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials).
    - Create Credentials > **OAuth client ID**.
    - Type: **Web Application**.
    - Authorized JavaScript origins: `http://localhost:5173` (and your production domain).
2.  **Implementation**:
    - Use a library like `@react-oauth/google`.
    - User clicks "Login with Google".
    - You get the `access_token` and pass it to `EarthEngineService.initialize(token)`.

---

## 🚀 Recommendation for BijMantra

Since you have a **Python Backend**, **Option A (Service Account)** is vastly superior because:

1.  Users don't need their own Earth Engine approval (which takes days).
2.  You control the quotas and usage.
3.  It's seamless for the user.

### Next Steps for Implementation

1.  **Backend**: Add a route (e.g., in FastAPI/Flask) that uses the `google-auth` library to sign a JWT and return a token.
2.  **Frontend**: Update `EarthEngineService` to fetch this token on startup.
