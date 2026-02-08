# 🪸 Great Barrier Reef Protocol: Full UI Audit

**Objective**: Visit every single page (200+) in the application to ensure no "White Screen of Death" (WSOD) or critical runtime errors exist after the Great Major Refactoring.

**Assignee**: JULES

## 1. Preparation

### A. Extract Routes

We cannot guess 200 URLs. We must extract them from the source code.
Run this Python script to parse `frontend/src/routes/*.tsx` and generate a list of checkable paths.

**Create file: `extract_routes.py` in root**

```python
import glob
import re
import json
import os

def extract_routes():
    route_files = glob.glob("frontend/src/routes/*.tsx")
    routes = []

    # Regex to find: { path: '/some/path', ... }
    # Handles simple quotes and varying spacing
    path_pattern = re.compile(r"path:\s*['\"]([^'\"]+)['\"]")

    print(f"🔍 Scanning {len(route_files)} route files...")

    for file_path in route_files:
        with open(file_path, 'r') as f:
            content = f.read()
            matches = path_pattern.findall(content)
            for match in matches:
                # Filter out wildcards or params for now if simple check is desired
                # Or keep them and instructing test to use default IDs
                if '*' in match:
                    continue

                # Replace dynamic params with dummy ID '1' for testing
                # e.g., /people/:id -> /people/1
                clean_path = re.sub(r':[a-zA-Z0-9_]+', '1', match)

                if clean_path not in routes:
                    routes.append(clean_path)

    # Sort for consistent testing
    routes.sort()

    output_path = "frontend/e2e/all_routes.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(routes, f, indent=2)

    print(f"✅ Extracted {len(routes)} unique routes to {output_path}")

if __name__ == "__main__":
    extract_routes()
```

Run it:

```bash
python extract_routes.py
```

## 2. The Test Suite

Create a dynamic Playwright test that iterates over `all_routes.json`.

**Create file: `frontend/e2e/tests/great_barrier_reef.spec.ts`**

```typescript
import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";

// Load routes
const routesPath = path.join(__dirname, "../all_routes.json");
const routes = JSON.parse(fs.readFileSync(routesPath, "utf-8"));

test.describe("🪸 Great Barrier Reef - Full UI Audit", () => {
  // Login once before all tests (reuse verify global setup usually, but doing explicit here for safety)
  test.beforeEach(async ({ page }) => {
    // Modify this if you rely on storageState in config
    // If using storageState from global setup, you can skip this.
    // Assuming 'storageState: "playwright/.auth/user.json"' is active in config.
  });

  for (const route of routes) {
    test(`Check Route: ${route}`, async ({ page }) => {
      console.log(`🌊 Visiting: ${route}`);

      // 1. Navigate
      // Handle base URL in config usually, ensure route starts with /
      await page.goto(route);

      // 2. Wait for Load
      // Wait for network to settle or specific element
      try {
        await page.waitForLoadState("networkidle", { timeout: 10000 });
      } catch (e) {
        console.warn(
          `⚠️ Network still busy on ${route}, proceeding to check UI...`,
        );
      }

      // 3. Check for White Screen of Death (WSOD)
      // Main content area should be present. Adjust selector to your layout (e.g. 'main', '#root', '.app')
      const mainContent = page.locator("main, #root");
      await expect(mainContent).toBeVisible();

      // Ensure it's not empty height (common WSOD symptom)
      const box = await mainContent.boundingBox();
      expect(box?.height).toBeGreaterThan(50);

      // Check for common error boundaries
      const errorText = page.getByText(
        /Something went wrong|Application Error|Minified React error/i,
      );
      await expect(errorText).not.toBeVisible();

      // 4. Evidence: Screenshot
      // Sanitize filename
      const safeName = route.replace(/\//g, "_").replace(/[:?]/g, "-");
      await page.screenshot({
        path: `test-results/great_barrier_reef/screenshot${safeName}.png`,
        fullPage: true,
      });
    });
  }
});
```

## 3. Execution

Instruct Jules to run the suite.

```bash
cd frontend
# Install generic dependencies if needed
npm install

# Run the Reef Test
npx playwright test tests/great_barrier_reef.spec.ts --project=chromium --reporter=html
```

## 4. Analysis

Instruct Jules to check the report:

1.  **Failures**: Any route that crashed or timed out.
2.  **Screenshots**: Check `test-results/great_barrier_reef/` folder.
    - If many failed, provide a summary list.
    - If successful, show a few key screenshots (Dashboard, Breeding, obscure pages).

---

**Note to Jules**: If 200 tests are too slow, use `--workers=4` or split the json list. But for a "Great Barrier Reef" audit, correctness > speed. Leave no stone unturned.
