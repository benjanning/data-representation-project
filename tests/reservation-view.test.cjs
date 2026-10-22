const { test } = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const V = require("../static/reservation-view.js");
const rows = [
  {
    id: 1,
    status: "confirmed",
    vehicle_ref: "DEMO-001",
    vehicle_model: "Toyota Yaris",
    customer_name: "Alex Sample",
    start_date: "2026-11-01",
    end_date: "2026-11-04",
    days: 3,
    daily_rate_cents: 3900,
    total_cents: 11700,
  },
  {
    id: 2,
    status: "cancelled",
    vehicle_ref: "DEMO-008",
    vehicle_model: "Kia Sportage",
    customer_name: "Taylor Sample",
    start_date: "2026-11-02",
    end_date: "2026-11-05",
    days: 3,
    daily_rate_cents: 6800,
    total_cents: 20400,
  },
];
function parse(text) {
  const p = spawnSync(
    "python",
    [
      "-c",
      "import csv,io,json,sys; print(json.dumps(list(csv.DictReader(io.StringIO(sys.stdin.buffer.read().decode('utf-8-sig'))))))",
    ],
    { input: text, encoding: "utf8" },
  );
  assert.equal(p.status, 0, p.stderr);
  return JSON.parse(p.stdout);
}
test("searches stored snapshots using all words, without changing order or data", () => {
  const before = JSON.stringify(rows);
  assert.deepEqual(V.searchRows(rows, "  ALEX  yaris "), [rows[0]]);
  assert.deepEqual(V.searchRows(rows, "DEMO-008"), [rows[1]]);
  assert.deepEqual(V.searchRows(rows, "2026-11-05 Taylor"), [rows[1]]);
  assert.deepEqual(V.searchRows(rows, "   "), rows);
  assert.deepEqual(V.searchRows(rows, "missing"), []);
  assert.equal(JSON.stringify(rows), before);
});
test("CSV independently round-trips the selected records, saved cents and exclusive dates", () => {
  const selected = V.searchRows(rows, "Kia");
  const result = parse(V.csv(selected));
  assert.equal(result.length, 1);
  assert.equal(result[0].rental_id, "2");
  assert.equal(result[0].saved_total_cents, "20400");
  assert.equal(result[0].daily_rate_cents, "6800");
  assert.equal(result[0].return_exclusive_utc, "2026-11-05");
  assert.equal(result[0].status, "cancelled");
  assert.equal(Object.keys(result[0]).length, 10);
});
test("CSV retains punctuation, Unicode and line breaks and protects formula-like text", () => {
  const source = {
    ...rows[0],
    customer_name: 'Zoë, "Sample"\nSecond line',
    vehicle_ref: "  =SUM(1,2)",
    vehicle_model: "@example",
  };
  const result = parse(V.csv([source]))[0];
  assert.equal(result.customer_name, source.customer_name);
  assert.equal(result.vehicle_reference, "'" + source.vehicle_ref);
  assert.equal(result.vehicle_model, "'@example");
  assert.equal(result.saved_total_cents, "11700");
  assert.equal(parse(V.csv([])).length, 0);
});
