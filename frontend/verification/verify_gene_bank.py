import os
from playwright.sync_api import Page, expect, sync_playwright

def test_gene_bank_dashboard(page: Page):
    # Capture console logs
    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
    page.on("pageerror", lambda err: print(f"Browser error: {err}"))

    # Mock the API responses
    # 1. Mock Vault Conditions
    page.route("**/api/v2/vault-sensors/conditions", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='''{
            "conditions": [
                {
                    "vault_id": "v1",
                    "vault_name": "Test Vault 1",
                    "status": "normal",
                    "current_readings": {"temperature": 4, "humidity": 35}
                },
                {
                    "vault_id": "v2",
                    "vault_name": "Test Vault 2",
                    "status": "critical",
                    "current_readings": {"temperature": -10, "humidity": 80}
                }
            ],
            "count": 2
        }'''
    ))

    # 2. Mock Viability Tests
    page.route("**/api/v2/seed-bank/viability-tests", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='''[
            {
                "test_id": "t1",
                "lot_id": "LOT-001",
                "test_date": "2024-12-31",
                "status": "pending"
            },
            {
                "test_id": "t2",
                "lot_id": "LOT-002",
                "test_date": "2024-01-01",
                "status": "completed",
                "germination_percent": 95
            }
        ]'''
    ))

    # 3. Mock other calls
    page.route("**/api/v2/seed-inventory/summary", lambda route: route.fulfill(
        status=200, body='{"total_lots": 100, "lots_needing_test": 5}'))
    page.route("**/api/v2/sensors/stats", lambda route: route.fulfill(
        status=200, body='{"active_alerts": 1}'))
    page.route("**/api/v2/seed-bank/regeneration-tasks*", lambda route: route.fulfill(
        status=200, body='[]'))
    page.route("**/api/v2/seed-bank/exchanges*", lambda route: route.fulfill(
        status=200, body='[]'))

    # Mock login endpoint
    page.route("**/api/auth/login", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='''{
            "access_token": "mock-token",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "email": "test@example.com",
                "full_name": "Test User",
                "organization_id": 1,
                "is_active": true
            }
        }'''
    ))

    print("Navigating to test dashboard...")
    page.goto("http://localhost:5173/genebank-dashboard-test")

    # Dump body text
    print(f"Page content: {page.content()}")

    if "login" in page.url:
        print("Redirected to login. Logging in...")
        page.fill("input[type='email']", "test@example.com")
        page.fill("input[type='password']", "password")
        page.click("button[type='submit']")
        page.wait_for_url(lambda url: "login" not in url)
        if "genebank-dashboard-test" not in page.url:
             page.goto("http://localhost:5173/genebank-dashboard-test")

    print(f"Current URL: {page.url}")

    # Assertions
    expect(page.get_by_text("Gene Bank Dashboard")).to_be_visible()

    os.makedirs("/home/jules/verification", exist_ok=True)
    page.screenshot(path="/home/jules/verification/gene_bank_dashboard.png")
    print("Verification successful!")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_gene_bank_dashboard(page)
        except Exception as e:
            print(f"Error: {e}")
            if 'page' in locals():
                page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
