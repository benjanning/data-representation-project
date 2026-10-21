const { test, expect } = require("@playwright/test"),
  fs = require("node:fs/promises");
const day = (n) => {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
};
async function reset(page) {
  await page
    .getByRole("button", { name: "Reset demo data ↺", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Reset sample data", exact: true })
    .click();
  await expect(page.locator("#confirm")).not.toBeVisible();
}
async function choose(page) {
  await page
    .getByRole("button", { name: "＋ New reservation", exact: true })
    .click();
  await page.getByLabel("Customer", { exact: true }).selectOption("4");
  await page.getByLabel("Vehicle", { exact: true }).selectOption("8");
  await page.locator("#rental-start").fill(day(10));
  await page.locator("#rental-end").fill(day(13));
  await page.locator("#quote-rental").click();
  await expect(page.locator("#rental-quote")).toContainText("€204.00");
}
async function capture(page, name, fullPage = true) {
  await fs.mkdir("verification/screenshots", { recursive: true });
  if (name === "rental-dashboard")
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.screenshot({
    path: `verification/screenshots/${name}.jpg`,
    type: "jpeg",
    quality: 85,
    fullPage,
  });
}
for (const [mode, base] of [
  ["flask", "http://127.0.0.1:5000"],
  ["static", "http://127.0.0.1:8088"],
]) {
  test(
    mode +
      " reservations: quote, allocation, conflicts, history, reset and mobile",
    async ({ page }) => {
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      await page.goto(base);
      await reset(page);
      await expect(page.locator("#available-total")).toContainText("7 / 8");
      if (mode === "static") await capture(page, "rental-dashboard", false);
      await page.locator('nav a[href="#reservations"]').click();
      await choose(page);
      if (mode === "static") await capture(page, "rental-quote", false);
      await page.locator("#confirm-rental").dblclick();
      await expect(page.locator("#rental-editor")).not.toBeVisible();
      await expect(page.locator(".reservation-card")).toHaveCount(4);
      await expect(
        page.locator(".reservation-card").filter({ hasText: "Kia Sportage" }),
      ).toContainText("€204.00");
      await page.reload();
      await expect(page.locator(".reservation-card")).toHaveCount(4);
      if (mode === "static") await capture(page, "reservations");
      await page
        .getByRole("button", { name: "＋ New reservation", exact: true })
        .click();
      await page.getByLabel("Customer", { exact: true }).selectOption("5");
      await page.getByLabel("Vehicle", { exact: true }).selectOption("8");
      await page.locator("#rental-start").fill(day(11));
      await page.locator("#rental-end").fill(day(14));
      await page.locator("#quote-rental").click();
      await expect(page.locator("#rental-error")).toContainText(
        "already reserved",
      );
      await page
        .getByRole("button", { name: "Keep browsing", exact: true })
        .click();
      const selected = page
        .locator(".reservation-card")
        .filter({ hasText: "Kia Sportage" });
      await selected
        .getByRole("button", { name: "Cancel reservation", exact: true })
        .click();
      await page
        .getByRole("button", { name: "Cancel allocation", exact: true })
        .click();
      await expect(page.locator("#confirm")).not.toBeVisible();
      await expect(selected).toContainText("Cancelled");
      await page.getByRole("button", { name: "History", exact: true }).click();
      await expect(page.locator(".reservation-card")).toHaveCount(1);
      await page
        .getByRole("button", { name: "Return due", exact: true })
        .click();
      await page
        .getByRole("button", { name: "Mark completed", exact: true })
        .click();
      await page
        .getByRole("button", { name: "Complete rental", exact: true })
        .click();
      await expect(page.locator("#confirm")).not.toBeVisible();
      await expect(
        page.getByText("No reservations in this view.", { exact: true }),
      ).toBeVisible();
      await page
        .getByRole("button", { name: "All reservations", exact: true })
        .click();
      await choose(page);
      await page.setViewportSize({ width: 390, height: 844 });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      if (mode === "static") await capture(page, "mobile-rental-quote", false);
      await page
        .getByRole("button", { name: "Keep browsing", exact: true })
        .click();
      await reset(page);
      await expect(page.locator(".reservation-card")).toHaveCount(3);
      expect(errors).toEqual([]);
    },
  );
}
test("static simultaneous tabs have one allocation winner", async ({
  context,
  page,
}) => {
  await page.goto("http://127.0.0.1:8088/#reservations");
  await reset(page);
  await choose(page);
  const other = await context.newPage();
  await other.goto("http://127.0.0.1:8088/#reservations");
  await choose(other);
  await Promise.all([
    page.locator("#confirm-rental").click(),
    other.locator("#confirm-rental").click(),
  ]);
  await expect
    .poll(
      async () =>
        Number(await page.locator("#rental-editor").isVisible()) +
        Number(await other.locator("#rental-editor").isVisible()),
    )
    .toBe(1);
  const loser = (await page.locator("#rental-editor").isVisible())
    ? page
    : other;
  await expect(loser.locator("#rental-error")).toContainText(
    "already reserved",
  );
  await page.reload();
  await expect(page.locator(".reservation-card")).toHaveCount(4);
  await other.close();
});
test("server retry after a lost create response does not allocate twice", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:5000/#reservations");
  await reset(page);
  await choose(page);
  let first = true;
  await page.route("**/api/reservations", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    const response = await route.fetch();
    if (first) {
      first = false;
      return route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          error: "Temporary response failure. Try again.",
        }),
      });
    }
    return route.fulfill({ response });
  });
  await page.locator("#confirm-rental").click();
  await expect(page.locator("#rental-error")).toContainText(
    "Temporary response failure",
  );
  await expect(page.getByLabel("Customer", { exact: true })).toHaveValue("4");
  await page.locator("#confirm-rental").click();
  await expect(page.locator("#rental-editor")).not.toBeVisible();
  await expect(page.locator(".reservation-card")).toHaveCount(4);
});
