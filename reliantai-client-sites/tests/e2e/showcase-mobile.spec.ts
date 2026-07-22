import { test, expect } from "@playwright/test";

test.describe("Showcase mobile layout", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("loads full-width preview without a persistent sidebar", async ({
    page,
  }) => {
    await page.goto("/showcase");
    await expect(page.getByText("Showcase")).toBeVisible();

    // Drawer closed by default — hamburger invites opening templates
    await expect(
      page.getByRole("button", { name: /Show templates/i }),
    ).toBeVisible();
    await expect(page.getByRole("dialog", { name: "Templates" })).toHaveCount(0);

    // Preview content is present in the main pane
    await expect(page.locator("main").getByText(/Comfort Pro HVAC/i).first()).toBeVisible({
      timeout: 15000,
    });
  });

  test("hamburger opens overlay drawer; selecting a template closes it", async ({
    page,
  }) => {
    await page.goto("/showcase");

    await page.getByRole("button", { name: /Show templates/i }).click();
    const dialog = page.getByRole("dialog", { name: "Templates" });
    await expect(dialog).toBeVisible();

    await dialog.getByRole("button", { name: /Select Plumbing template/i }).click();
    await expect(page.getByRole("dialog", { name: "Templates" })).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: /Show templates/i }),
    ).toBeVisible();
    await expect(page.locator("main").getByText(/PipeShield Plumbing/i).first()).toBeVisible({
      timeout: 15000,
    });
  });
});
