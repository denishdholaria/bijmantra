import { beforeEach, describe, expect, it, vi } from "vitest";

const user = {
  id: 1,
  email: "admin@bijmantra.org",
  full_name: "System Administrator",
  organization_id: 1,
  organization_name: "BijMantra HQ",
  is_demo: false,
  is_active: true,
  is_superuser: true,
  roles: ["superuser"],
  permissions: ["*"],
};

async function loadKeycloakStore() {
  vi.resetModules();

  const apiClient = {
    getToken: vi.fn(() => null),
    setToken: vi.fn(),
    validateToken: vi.fn(),
    authService: {
      login: vi.fn(),
      me: vi.fn().mockResolvedValue(user),
    },
  };

  const keycloakAuth = {
    clearKeycloakSession: vi.fn(),
    initializeKeycloakAuth: vi.fn().mockResolvedValue({
      authenticated: true,
      token: "keycloak-access-token",
    }),
    isKeycloakAuthEnabled: vi.fn(() => true),
    loginWithKeycloak: vi.fn().mockResolvedValue(undefined),
    logoutFromKeycloak: vi.fn().mockResolvedValue(undefined),
    subscribeKeycloakToken: vi.fn(() => vi.fn()),
  };

  vi.doMock("@/config", () => ({
    AUTH_PROVIDER: "keycloak",
    LOCAL_PASSWORD_LOGIN_ENABLED: false,
  }));
  vi.doMock("@/lib/api-client", () => ({ apiClient }));
  vi.doMock("@/lib/auth-lifecycle", () => ({
    clearTenantClientState: vi.fn().mockResolvedValue(undefined),
  }));
  vi.doMock("@/lib/keycloak-auth", () => keycloakAuth);

  const { useAuthStore } = await import("./auth");
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    isAuthInitialized: false,
    isLoading: false,
    error: null,
    _hasHydrated: true,
  });

  return { apiClient, keycloakAuth, useAuthStore };
}

describe("useAuthStore Keycloak mode", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.clearAllMocks();
  });

  it("initializes the Keycloak session and loads the BijMantra user profile", async () => {
    const { apiClient, keycloakAuth, useAuthStore } = await loadKeycloakStore();

    await useAuthStore.getState().initializeAuth();

    expect(keycloakAuth.initializeKeycloakAuth).toHaveBeenCalled();
    expect(apiClient.setToken).toHaveBeenCalledWith("keycloak-access-token");
    expect(apiClient.authService.me).toHaveBeenCalled();
    expect(useAuthStore.getState()).toMatchObject({
      token: "keycloak-access-token",
      user,
      isAuthenticated: true,
      isAuthInitialized: true,
    });
  });

  it("starts Keycloak login instead of local password login", async () => {
    const { apiClient, keycloakAuth, useAuthStore } = await loadKeycloakStore();

    await useAuthStore.getState().loginWithIdentityProvider();

    expect(keycloakAuth.loginWithKeycloak).toHaveBeenCalled();
    expect(apiClient.authService.login).not.toHaveBeenCalled();
  });

  it("clears local state before redirecting to Keycloak logout", async () => {
    const { apiClient, keycloakAuth, useAuthStore } = await loadKeycloakStore();

    useAuthStore.setState({
      authProvider: "keycloak",
      token: "keycloak-access-token",
      user,
      isAuthenticated: true,
    });

    await useAuthStore.getState().logout();

    expect(apiClient.setToken).toHaveBeenCalledWith(null);
    expect(keycloakAuth.logoutFromKeycloak).toHaveBeenCalled();
    expect(useAuthStore.getState()).toMatchObject({
      token: null,
      user: null,
      isAuthenticated: false,
    });
  });
});
