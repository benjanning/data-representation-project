const { test, expect } = require("@playwright/test");
const fs = require("node:fs/promises");
const handover = require("../static/reservation-seed.json").find(
  (row) => row.vehicle_id === 1,
).end_offset;
const day = (n) => {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
};
async function capture(page, name) {
  await fs.mkdir("verification/screenshots", { recursive: true });
  const target = name.includes("availability")
    ? ".availability-heading"
    : ".page-heading";
  await page
    .locator(target)
    .evaluate((el) =>
      el.scrollIntoView({ block: "start", behavior: "instant" }),
    );
  await page.screenshot({
    path: `verification/screenshots/${name}.jpg`,
    type: "jpeg",
    quality: 85,
    fullPage: false,
  });
}
for (const [mode, base] of [
  ["flask", "http://127.0.0.1:5000"],
  ["static", "http://127.0.0.1:8088"],
])
  test(`${mode} vehicle availability, selected quote, snapshot search and exact CSV`, async ({
    page,
  }) => {
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(base);
    await page
      .getByRole("button", { name: "Reset demo data ↺", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Reset sample data", exact: true })
      .click();
    await expect(page.locator("#confirm")).not.toBeVisible();
    await page
      .getByText("See all 8 vehicles for these dates", { exact: true })
      .click();
    await expect(page.locator(".availability-card")).toHaveCount(8);
    const blocked = page.locator('[data-availability-vehicle="1"]');
    await expect(blocked).toContainText("Blocked for part");
    await expect(blocked).toContainText(day(handover));
    await expect(blocked.getByRole("button")).toBeDisabled();
    await expect(page.locator(".availability-state.is-free")).toHaveCount(7);
    if (mode === "static") await capture(page, "availability-roster");
    // Adjacent periods do not overlap: the seed Yaris returns on the chosen UTC start date.
    await page
      .locator('#availability-form input[name="start_date"]')
      .fill(day(handover));
    await page
      .locator('#availability-form input[name="end_date"]')
      .fill(day(handover + 3));
    await page
      .getByRole("button", { name: "Check availability", exact: true })
      .click();
    await page
      .getByText("See all 8 vehicles for these dates", { exact: true })
      .click();
    await expect(blocked.getByRole("button")).toBeEnabled();
    await page
      .getByRole("button", { name: "Reserve DEMO-008", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("#rental-vehicle")).toHaveValue("8");
    await expect(page.locator("#rental-start")).toHaveValue(day(handover));
    await expect(page.locator("#rental-end")).toHaveValue(day(handover + 3));
    await page.getByLabel("Customer", { exact: true }).selectOption("4");
    await page.locator("#quote-rental").click();
    await expect(page.locator("#rental-quote")).toContainText("€204.00");
    await page.locator("#confirm-rental").click();
    await expect(page.locator("#rental-editor")).not.toBeVisible();
    await expect(page.locator(".reservation-card")).toHaveCount(4);
    await expect(page.locator("#main")).toBeFocused();
    await page
      .getByLabel("Find a reservation", { exact: true })
      .fill("Taylor Kia");
    await page
      .getByRole("button", { name: "Search reservations", exact: true })
      .click();
    await expect(page.locator(".reservation-card")).toHaveCount(1);
    await expect(page.locator("#reservation-search")).toBeFocused();
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page
        .getByRole("button", {
          name: "Export shown reservations CSV",
          exact: true,
        })
        .click(),
    ]);
    const csv = await fs.readFile(await download.path(), "utf8");
    if (mode === "static") {
      await fs.mkdir("verification/exports", { recursive: true });
      await fs.writeFile("verification/exports/shown-reservations.csv", csv);
    }
    const lines = csv
      .replace(/^\uFEFF/, "")
      .trim()
      .split("\r\n");
    expect(lines).toHaveLength(2);
    expect(lines[1]).toContain('"Taylor Sample"');
    expect(lines[1]).toContain('"6800","20400"');
    expect(lines[1]).toContain(`"${day(handover)}","${day(handover + 3)}","3"`);
    if (mode === "static") await capture(page, "reservation-search");
    await page.getByRole("button", { name: "History", exact: true }).click();
    await expect(page.locator(".reservation-card")).toHaveCount(0);
    await expect(page.locator("#export-reservations")).toBeDisabled();
    await page
      .getByRole("button", { name: "All reservations", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Cancel reservation", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Cancel allocation", exact: true })
      .click();
    await expect(page.locator("#confirm")).not.toBeVisible();
    await page.getByRole("button", { name: "History", exact: true }).click();
    await expect(page.locator(".reservation-card")).toHaveCount(1);
    await expect(page.locator(".reservation-card")).toContainText("Cancelled");
    await page.setViewportSize({ width: 390, height: 844 });
    await page
      .getByRole("button", { name: "Clear search", exact: true })
      .click();
    await expect(page.locator("#reservation-search")).toBeFocused();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (mode === "static") await capture(page, "mobile-reservation-search");
    await page.locator('nav a[href="#dashboard"]').click();
    await page
      .getByText("See all 8 vehicles for these dates", { exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Reserve DEMO-008", exact: true }),
    ).toBeEnabled();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (mode === "static") await capture(page, "mobile-availability");
    expect(errors).toEqual([]);
  });
