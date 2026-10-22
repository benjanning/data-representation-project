# Preview provenance

The preview is an authentic application screenshot or a chart from this project, proportionally cropped/padded for repository presentation. Application records are synthetic. The social-preview.png graphic contains that real image and a project label, not a fabricated application interface.

See the project and the central portfolio assets/PROVENANCE.md for source data and generation details.
## V3 Fleetdesk

assets/dashboard.jpg, inventory.jpg, vehicle-form.jpg, customers.jpg and completed-action.jpg are authentic browser captures of the V3 Flask application, using synthetic data on 20 October 2026. The dashboard and tables calculate summaries from actual demo records. Vehicle glyphs are original SVG illustrations, not photographs. No real availability, bookings or revenue is represented. Historical V2 previews remain historical evidence; the README now uses the current dashboard.

The release workflow independently tests both Flask and browser-storage adapters, captures predictable screenshots into verification/screenshots and exports them with the source commit and hashes. Only a successful run is eligible for the central portfolio sync. The portfolio export identifies which source revision each image represents.

## V4 reservation workflow
The rental quote, reservation list, calculated dashboard and mobile form are genuine captures of the shared Flask/static frontend from tests/reservations.spec.cjs. Fictional names, synthetic vehicles and UTC-relative sample dates are used. Quotes use actual selected rates; confirmed example value is not revenue. CI exports images only after API/domain, Python/JavaScript contract, isolated MySQL and browser checks pass. README images resolve to the verified export branch; its manifest identifies source revision, run and hashes. Original CSS/SVG vehicle glyphs are retained.

## V5 reservation workspace

availability-roster.jpg, reservation-search.jpg, mobile-availability.jpg and mobile-reservation-search.jpg are genuine Chromium captures produced by the passing availability/search/export journeys. Availability and blockers come from actual synthetic records; CSV assertions reconcile the downloaded snapshot. No fabricated statistics or interface images are used.
