from playwright.sync_api import sync_playwright, expect

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Increase viewport size to capture more content
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # Login
        print("Navigating to login...")
        page.goto("http://localhost:5173/login")

        # Check if we are already logged in (redirected to dashboard) or on login page
        if "login" in page.url:
            print("Logging in...")
            # Assuming standard login form
            page.fill('input[type="email"]', 'demo@bijmantra.org')
            page.fill('input[type="password"]', 'demo123') # Trying standard demo password
            page.click('button[type="submit"]')

            # Wait for navigation (could be dashboard or gateway)
            print("Waiting for navigation...")
            page.wait_for_url(lambda url: "dashboard" in url or "gateway" in url, timeout=15000)
            print(f"Logged in successfully. Current URL: {page.url}")

        # Navigate to GDD page
        print("Navigating to GDD page...")
        page.goto("http://localhost:5173/crop-intelligence/gdd")

        # Wait for title
        print("Waiting for page load...")
        expect(page.get_by_text("Growing Degree Days")).to_be_visible(timeout=15000)

        # Wait a bit for mock data/tabs to render
        page.wait_for_timeout(3000)

        # Take screenshot
        print("Taking screenshot...")
        page.screenshot(path="verification_gdd.png")
        print("Screenshot saved to verification_gdd.png")

        browser.close()

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Error: {e}")
