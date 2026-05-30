import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  instances: [] as Array<{
    token?: string;
    authenticated: boolean;
    init: ReturnType<typeof vi.fn>;
    login: ReturnType<typeof vi.fn>;
    logout: ReturnType<typeof vi.fn>;
    updateToken: ReturnType<typeof vi.fn>;
    clearToken: ReturnType<typeof vi.fn>;
  }>,
}));

vi.mock("@/config", () => ({
  AUTH_PROVIDER: "keycloak",
  KEYCLOAK_URL: "http://localhost:8084",
  KEYCLOAK_REALM: "bijmantra",
  KEYCLOAK_CLIENT_ID: "bijmantra-web",
}));

vi.mock("keycloak-js", () => {
  const KeycloakMock = vi.fn(function KeycloakMock() {
    const instance = {
      authenticated: true,
      token: "keycloak-access-token",
      init: vi.fn().mockResolvedValue(true),
      login: vi.fn().mockResolvedValue(undefined),
      logout: vi.fn().mockResolvedValue(undefined),
      updateToken: vi.fn().mockResolvedValue(false),
      clearToken: vi.fn(),
    };
    mocks.instances.push(instance);
    return instance;
  });

  return {
    default: KeycloakMock,
  };
});

describe("keycloak-auth", () => {
  beforeEach(() => {
    vi.resetModules();
    mocks.instances.length = 0;
  });

  it("initializes Keycloak with authorization code + PKCE and silent SSO", async () => {
    const { initializeKeycloakAuth } = await import("./keycloak-auth");

    const session = await initializeKeycloakAuth();
    const instance = mocks.instances[0];

    expect(instance.init).toHaveBeenCalledWith(
      expect.objectContaining({
        onLoad: "check-sso",
        flow: "standard",
        pkceMethod: "S256",
        responseMode: "query",
        silentCheckSsoRedirectUri: "http://localhost:3000/silent-check-sso.html",
      }),
    );
    expect(instance.updateToken).toHaveBeenCalledWith(30);
    expect(session).toEqual({
      authenticated: true,
      token: "keycloak-access-token",
    });
  });

  it("redirects login and logout through Keycloak", async () => {
    const { loginWithKeycloak, logoutFromKeycloak } = await import("./keycloak-auth");

    await loginWithKeycloak();
    await logoutFromKeycloak();

    const instance = mocks.instances[0];
    expect(instance.login).toHaveBeenCalledWith({
      redirectUri: "http://localhost:3000/gateway",
    });
    expect(instance.logout).toHaveBeenCalledWith({
      redirectUri: "http://localhost:3000/login",
    });
  });
});
