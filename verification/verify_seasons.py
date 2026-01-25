import re
from playwright.sync_api import sync_playwright, expect

def test_seasons_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Mock API responses
        # 1. Mock Seasons list
        page.route(re.compile(r".*/brapi/v2/seasons\?.*"), lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='''
            {
                "metadata": {
                    "pagination": {
                        "currentPage": 0,
                        "pageSize": 20,
                        "totalCount": 2,
                        "totalPages": 1
                    },
                    "status": []
                },
                "result": {
                    "data": [
                        {
                            "seasonDbId": "season_1",
                            "seasonName": "Spring 2025",
                            "year": 2025,
                            "additionalInfo": {}
                        },
                        {
                            "seasonDbId": "season_2",
                            "seasonName": "Winter 2024",
                            "year": 2024,
                            "additionalInfo": {}
                        }
                    ]
                }
            }
            '''
        ))

        # 2. Mock User Profile/Auth check if needed (api/auth/me)
        page.route(re.compile(r".*/api/auth/me"), lambda route: route.fulfill(status=200))

        # 3. Mock Workspace Preferences
        page.route(re.compile(r".*/api/v2/profile/workspace.*"), lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"status": "success", "data": {"default_workspace": "breeding"}}'
        ))

        # Setup Authentication in localStorage
        page.goto("http://localhost:3000/login")
        page.evaluate("""() => {
            localStorage.setItem('auth_token', 'mock_token');
            localStorage.setItem('bijmantra-auth', JSON.stringify({
                state: {
                    user: { id: 1, email: 'demo@bijmantra.org', full_name: 'Demo User' },
                    token: 'mock_token',
                    isAuthenticated: true
                },
                version: 0
            }));
            // Also set workspace
            localStorage.setItem('bijmantra-workspace', JSON.stringify({
                state: {
                    activeWorkspaceId: 'breeding',
                    preferences: { defaultWorkspace: 'breeding' }
                },
                version: 0
            }));
        }""")

        # Navigate to Seasons page
        print("Navigating to /seasons...")
        page.goto("http://localhost:3000/seasons")

        # Wait for content
        print("Waiting for Seasons heading...")
        expect(page.get_by_role("heading", name="Seasons")).to_be_visible(timeout=15000)

        # Check for mocked data
        print("Verifying mocked data...")
        expect(page.get_by_text("Spring 2025")).to_be_visible()
        expect(page.get_by_text("Winter 2024")).to_be_visible()

        # Take screenshot
        print("Taking screenshot...")
        page.screenshot(path="verification/seasons_page.png")
        print("Screenshot saved to verification/seasons_page.png")

        browser.close()

if __name__ == "__main__":
    test_seasons_page()
