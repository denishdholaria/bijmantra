import Keycloak from "keycloak-js";

import {
  AUTH_PROVIDER,
  KEYCLOAK_CLIENT_ID,
  KEYCLOAK_REALM,
  KEYCLOAK_URL,
} from "@/config";

export interface KeycloakAuthSession {
  authenticated: boolean;
  token: string | null;
}

type TokenListener = (token: string | null) => void;

let keycloak: Keycloak | null = null;
let initPromise: Promise<KeycloakAuthSession> | null = null;
let refreshInterval: number | null = null;
const tokenListeners = new Set<TokenListener>();

export function isKeycloakAuthEnabled() {
  return AUTH_PROVIDER === "keycloak";
}

export function subscribeKeycloakToken(listener: TokenListener) {
  tokenListeners.add(listener);
  return () => tokenListeners.delete(listener);
}

function emitToken(token: string | null) {
  for (const listener of tokenListeners) {
    listener(token);
  }
}

function getOrCreateKeycloak() {
  if (keycloak) {
    return keycloak;
  }

  keycloak = new Keycloak({
    url: KEYCLOAK_URL,
    realm: KEYCLOAK_REALM,
    clientId: KEYCLOAK_CLIENT_ID,
  });

  keycloak.onAuthRefreshSuccess = () => emitToken(keycloak?.token ?? null);
  keycloak.onAuthLogout = () => emitToken(null);
  keycloak.onTokenExpired = () => {
    void refreshKeycloakToken().catch(() => {
      keycloak?.clearToken();
      emitToken(null);
    });
  };

  return keycloak;
}

function browserOrigin() {
  if (typeof window === "undefined") {
    return "";
  }

  return window.location.origin;
}

function clearRefreshInterval() {
  if (refreshInterval !== null) {
    window.clearInterval(refreshInterval);
    refreshInterval = null;
  }
}

function startRefreshInterval() {
  if (typeof window === "undefined" || refreshInterval !== null) {
    return;
  }

  refreshInterval = window.setInterval(() => {
    void refreshKeycloakToken().catch(() => {
      keycloak?.clearToken();
      emitToken(null);
      clearRefreshInterval();
    });
  }, 30_000);
}

export async function initializeKeycloakAuth(): Promise<KeycloakAuthSession> {
  if (!isKeycloakAuthEnabled()) {
    return { authenticated: false, token: null };
  }

  if (initPromise) {
    return initPromise;
  }

  const client = getOrCreateKeycloak();
  initPromise = client
    .init({
      onLoad: "check-sso",
      pkceMethod: "S256",
      flow: "standard",
      responseMode: "query",
      checkLoginIframe: false,
      silentCheckSsoRedirectUri: `${browserOrigin()}/silent-check-sso.html`,
    })
    .then(async (authenticated) => {
      if (!authenticated) {
        clearRefreshInterval();
        emitToken(null);
        return { authenticated: false, token: null };
      }

      await refreshKeycloakToken();
      startRefreshInterval();
      emitToken(client.token ?? null);
      return {
        authenticated: true,
        token: client.token ?? null,
      };
    })
    .catch((error) => {
      initPromise = null;
      clearRefreshInterval();
      emitToken(null);
      throw error;
    });

  return initPromise;
}

export async function loginWithKeycloak(redirectUri?: string) {
  if (!isKeycloakAuthEnabled()) {
    return;
  }

  await getOrCreateKeycloak().login({
    redirectUri: redirectUri ?? `${browserOrigin()}/gateway`,
  });
}

export async function logoutFromKeycloak(redirectUri?: string) {
  if (!isKeycloakAuthEnabled()) {
    return;
  }

  clearRefreshInterval();
  await getOrCreateKeycloak().logout({
    redirectUri: redirectUri ?? `${browserOrigin()}/login`,
  });
}

export async function refreshKeycloakToken(minValiditySeconds = 30) {
  if (!keycloak?.authenticated) {
    return false;
  }

  const refreshed = await keycloak.updateToken(minValiditySeconds);
  emitToken(keycloak.token ?? null);
  return refreshed;
}

export function clearKeycloakSession() {
  clearRefreshInterval();
  keycloak?.clearToken();
  emitToken(null);
}
