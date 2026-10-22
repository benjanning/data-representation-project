/* Read-only reservation search and portable snapshot export. Business rules stay in rental-rules.js. */
(function (root) {
  "use strict";
  function searchRows(rows, query) {
    const words = String(query)
      .trim()
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean);
    return rows.filter((row) => {
      const text = [
        String(row.id).padStart(3, "0"),
        row.vehicle_ref,
        row.vehicle_model,
        row.customer_name,
        row.start_date,
        row.end_date,
        row.status,
      ]
        .join(" ")
        .toLowerCase();
      return words.every((word) => text.includes(word));
    });
  }
  function csv(rows) {
    const fields = [
      ["rental_id", "id"],
      ["status", "status"],
      ["vehicle_reference", "vehicle_ref"],
      ["vehicle_model", "vehicle_model"],
      ["customer_name", "customer_name"],
      ["collection_utc", "start_date"],
      ["return_exclusive_utc", "end_date"],
      ["days", "days"],
      ["daily_rate_cents", "daily_rate_cents"],
      ["saved_total_cents", "total_cents"],
    ];
    function cell(value) {
      let text = String(value);
      if (typeof value === "string" && /^[\s]*[=+@-]/.test(text))
        text = "'" + text;
      return '"' + text.replaceAll('"', '""') + '"';
    }
    return (
      [
        fields.map(([heading]) => cell(heading)).join(","),
        ...rows.map((row) => fields.map(([, key]) => cell(row[key])).join(",")),
      ].join("\r\n") + "\r\n"
    );
  }
  const api = { searchRows, csv };
  if (typeof module !== "undefined") module.exports = api;
  else root.FleetReservationView = api;
})(typeof window !== "undefined" ? window : globalThis);
