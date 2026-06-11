import { test, expect } from "@playwright/test";

test.describe("ISR Dynamic Route /[slug]", () => {
  test("home page redirects to showcase", async ({ page }) => {
    const res = await page.goto("/");
    expect(res?.status()).toBe(200);
    await expect(page).toHaveURL(/\/showcase$/);
    await expect(page.locator("body")).toBeVisible();
  });

  test("showcase page renders", async ({ page }) => {
    const res = await page.goto("/showcase");
    expect(res?.status()).toBe(200);
    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("Revalidation endpoint /api/revalidate", () => {
  test("returns 401 without body (auth check runs first)", async ({ request }) => {
    const res = await request.post("/api/revalidate");
    expect(res.status()).toBe(401);
  });

  test("returns 401 with wrong secret", async ({ request }) => {
    const res = await request.post("/api/revalidate", {
      data: { slug: "test-slug" },
      headers: { Authorization: "Bearer wrong-secret" },
    });
    expect(res.status()).toBe(401);
  });

  test("requires authorization header", async ({ request }) => {
    const res = await request.post("/api/revalidate", {
      data: { slug: "test-slug" },
    });
    expect(res.status()).toBe(401);
  });
});

test.describe("Template rendering", () => {
  test("page returns 404 for nonexistent slug", async ({ page }) => {
    const res = await page.goto("/nonexistent-slug-12345");
    expect(res?.status()).toBe(404);
  });
});
