import { render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

async function loadProtectedRoute() {
  vi.resetModules();

  const keycloakAuth = {
    clearKeycloakSession: vi.fn(),
    initializeKeycloakAuth: vi.fn(),
    isKeycloakAuthEnabled: vi.fn(() => true),
    loginWithKeycloak: vi.fn().mockResolvedValue(undefined),
    logoutFromKeycloak: vi.fn(),
    subscribeKeycloakToken: vi.fn(() => vi.fn()),
  };

  vi.doMock("@/config", () => ({
    AUTH_PROVIDER: "keycloak",
    LOCAL_PASSWORD_LOGIN_ENABLED: false,
  }));
  vi.doMock("@/lib/api-client", () => ({
    apiClient: {
      getToken: vi.fn(() => null),
      setToken: vi.fn(),
      validateToken: vi.fn(),
      authService: {
        login: vi.fn(),
        me: vi.fn(),
      },
    },
  }));
  vi.doMock("@/lib/auth-lifecycle", () => ({
    clearTenantClientState: vi.fn().mockResolvedValue(undefined),
  }));
  vi.doMock("@/lib/keycloak-auth", () => keycloakAuth);

  const { useAuthStore } = await import("@/store/auth");
  const { ProtectedRoute } = await import("./ProtectedRoute");
  useAuthStore.setState({
    authProvider: "keycloak",
    user: null,
    token: null,
    isAuthenticated: false,
    isAuthInitialized: true,
    isLoading: false,
    error: null,
    _hasHydrated: true,
  });

  return { keycloakAuth, ProtectedRoute };
}

describe("ProtectedRoute in Keycloak mode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts Keycloak login for unauthenticated protected content", async () => {
    const { keycloakAuth, ProtectedRoute } = await loadProtectedRoute();

    const { queryByText } = render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>Private content</div>
        </ProtectedRoute>
      </MemoryRouter>,
    );

    expect(queryByText("Private content")).toBeNull();
    await waitFor(() => expect(keycloakAuth.loginWithKeycloak).toHaveBeenCalled());
  });
});
