const { test } = require("node:test"),
  assert = require("node:assert/strict"),
  R = require("../static/rental-rules.js"),
  cases = require("./rental-contract.json");
test("JavaScript rental rules match the Python contract across calendar, overlap, money and state cases", () => {
  for (const c of cases) {
    let actual;
    try {
      actual = { value: R[c.method](...c.args) };
    } catch (e) {
      actual = {
        error: { message: e.message, code: e.code, status: e.status },
      };
    }
    assert.deepEqual(actual, c.expected, c.name);
  }
});
test("saved rental data rejects conflicting allocations, altered totals and dangling references", () => {
  const base = require("../static/demo-data.json"),
    data = structuredClone(base);
  data.reservations = R.seeded(
    data.cars,
    data.customers,
    require("../static/reservation-seed.json"),
    "2030-01-01",
  );
  assert.equal(R.validateSaved(data), data);
  const changed = structuredClone(data);
  changed.reservations[0].total_cents = 1;
  assert.throws(() => R.validateSaved(changed));
  const conflict = structuredClone(data);
  conflict.reservations.push({
    ...conflict.reservations[0],
    id: 4,
    request_id: "different-request",
  });
  assert.throws(() => R.validateSaved(conflict));
  const missing = structuredClone(data);
  missing.cars = [];
  assert.throws(() => R.validateSaved(missing));
});
