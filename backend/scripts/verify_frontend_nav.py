import time
from playwright.sync_api import sync_playwright, expect

def verify_carbon_dashboard():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Inject Workspace and Auth
        # Using 'breeding' workspace which has access to 'environment' module
        workspace_state = {
            "state": {
                "activeWorkspaceId": "breeding",
                "preferences": {
                    "defaultWorkspace": None,
                    "recentWorkspaces": [],
                    "showGatewayOnLogin": True,
                    "lastWorkspace": "breeding",
                    "lastChanged": "2023-10-27T10:00:00.000Z"
                },
                "hasSelectedWorkspace": True,
                "isGatewayDismissed": True
            },
            "version": 0
        }

        auth_state = {
            "state": {
                "isAuthenticated": True,
                "user": {
                    "id": 1,
                    "email": "test@bijmantra.org",
                    "full_name": "Test User",
                    "organization_id": 1,
                    "role": "admin"
                },
                "token": "fake-jwt-token"
            },
            "version": 0
        }

        # We need to set localStorage before navigation
        # Playwright doesn't allow setting localStorage directly on new context without a page
        page = context.new_page()
        page.goto("http://localhost:5173")

        page.evaluate(f"localStorage.setItem('bijmantra-workspace', '{str(workspace_state).replace(chr(39), chr(34))}')")
        page.evaluate(f"localStorage.setItem('bijmantra-auth', '{str(auth_state).replace(chr(39), chr(34))}')")

        # Navigate to Carbon Dashboard
        print("Navigating to Carbon Dashboard...")
        page.goto("http://localhost:5173/earth-systems/carbon")

        # Wait for load
        time.sleep(5)

        # Verify
        page.screenshot(path="/home/jules/verification/carbon_dashboard.png")
        print("Screenshot saved to /home/jules/verification/carbon_dashboard.png")

        browser.close()

if __name__ == "__main__":
    verify_carbon_dashboard()
