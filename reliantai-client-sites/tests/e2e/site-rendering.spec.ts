import { test, expect } from "@playwright/test";

// These tests run against the mock API server (tests/mocks/api-server.mjs)
// wired in via API_BASE_URL in playwright.config.ts, so the full ISR fetch →
// validate → template render path is exercised with real HTTP semantics.

test.describe("Live site rendering from API content", () => {
  test("renders the template for a live slug", async ({ page }) => {
    const res = await page.goto("/test-hvac-austin");
    expect(res?.status()).toBe(200);
    await expect(
      page.getByRole("heading", { name: /Same-Day AC Repair Across Austin/i })
    ).toBeVisible();
    await expect(page.getByText("Comfort Pro HVAC").first()).toBeVisible();
    // Live sites must NOT show the preview banner
    await expect(page.getByText("This is your free preview site")).toHaveCount(0);
  });

  test("emits sanitized JSON-LD that cannot break out of the script tag", async ({
    page,
  }) => {
    await page.goto("/test-hvac-austin");
    const ldScripts = page.locator('script[type="application/ld+json"]');
    // Page emits multiple JSON-LD tags (LocalBusiness, FAQPage, Services, BreadcrumbList, legacy schema_org)
    const count = await ldScripts.count();
    expect(count).toBeGreaterThanOrEqual(1);

    // The legacy schema_org block contains the hostile description from the fixture.
    // It is the last ld+json tag on the page.
    const legacySchema = ldScripts.last();
    const raw = await legacySchema.textContent();
    expect(raw).toBeTruthy();
    // Escaping must prevent a literal closing tag inside the script body...
    expect(raw!).not.toContain("</script");
    // ...while JSON.parse round-trips to the original hostile string intact.
    const parsed = JSON.parse(raw!) as { description?: string; "@type"?: string };
    expect(parsed["@type"]).toBe("HVACBusiness");
    expect(parsed.description).toContain("</script>");
    // And the injected <img onerror> must not exist as a real DOM element.
    await expect(page.locator('img[src="x"]')).toHaveCount(0);
  });

  test("shows the preview banner for preview_live sites", async ({ page }) => {
    const res = await page.goto("/preview-hvac-austin");
    expect(res?.status()).toBe(200);
    await expect(page.getByText("This is your free preview site")).toBeVisible();
    await expect(page.getByText(/Get This Site/)).toBeVisible();
  });

  test("returns 404 when the API responds with an unknown template_id", async ({
    page,
  }) => {
    const res = await page.goto("/bad-template-austin");
    expect(res?.status()).toBe(404);
  });

  test("does not render javascript: website links from API content", async ({
    page,
  }) => {
    const res = await page.goto("/unsafe-url-plumbing");
    expect(res?.status()).toBe(200);
    await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0);
  });

  test("returns 404 when the API has no content for the slug (real API 404)", async ({
    page,
  }) => {
    const res = await page.goto("/no-such-site-xyz");
    expect(res?.status()).toBe(404);
  });

  test("rejects path-traversal style slugs", async ({ page }) => {
    const res = await page.goto("/%2E%2E%2Fadmin");
    expect(res?.status()).toBe(404);
  });
});

test.describe("Security headers", () => {
  test("responses include hardening headers", async ({ page }) => {
    const res = await page.goto("/test-hvac-austin");
    const headers = res?.headers() ?? {};
    expect(headers["x-content-type-options"]).toBe("nosniff");
    expect(headers["x-frame-options"]).toBe("SAMEORIGIN");
    expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
  });
});
