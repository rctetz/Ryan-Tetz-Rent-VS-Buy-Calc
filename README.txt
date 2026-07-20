HOUSE ALPHA V4

Deploying over the existing Render app:
1. Replace the files in your GitHub repository with the contents of this folder.
2. Commit and push.
3. Render should redeploy automatically at the same public URL.
4. On iPhone, reopen the app and refresh. If the old installed icon or layout remains, remove the old home-screen app and add it again after deployment.

New in v4:
- Expanded Eastern Sierra location list
- Location-specific 1BR rent, HOA, home insurance, tax, and one-car garage/storage defaults
- Current rent automatically equals the location's 1BR default
- HOA and garage/storage toggles
- Mammoth HOA default set to $750/month
- 10% stock-return and 3% inflation defaults
- Purchase-price slider
- Improved break-even range messages
- Wealth chart, insight cards, new visual theme, and House Alpha app icon

Important: Small-market rent, HOA, storage, insurance, and tax values are editable planning benchmarks. Always replace them with property-specific figures when available.


HOUSE ALPHA V5
- Adds Carson City, Gardnerville, Truckee, and Sonora.
- June Lake uses a Mammoth-adjacent planning rent rather than a distorted vacation-rental average.
- Condo mode enables HOA and garage/storage by default; single-family mode disables both.
- Price slider shows green/yellow/red zones and a break-even marker.

HOUSE ALPHA V6
- Fixes current-rent break-even: tested rent and market-rent cap now move together.
- Removes misleading '$20,000/mo rent' result caused by the old cap interaction.
- Adds automatic home-insurance scaling with purchase price.
- Condo insurance scales gently; single-family insurance scales more strongly.
- Adds an insurance auto/manual switch.
- Labels sub-2% mortgage break-even values as below the practical range.

HOUSE ALPHA V7
- Adds estimated PMI for down payments below 20%.
- PMI automatically ends once modeled LTV reaches the selected cancellation threshold.
- Default PMI estimate is 0.50% annually and remains editable.
- Keeps the 100% cash button directly beside the down-payment selector.
- Adds Fresno, California.
- Replaces the round slider thumb with a narrow precision bar.
- Slider snaps to the exact break-even price when moved within $5,000.
- Break-even marker and green/yellow/red price zones are more precise.

HOUSE ALPHA V8
- Adds Rental / Investment Property mode.
- Adds 1, 2, 3, and 4 bedroom rent-collected estimates by location.
- Adds editable vacancy, management, repairs/capex reserve, utilities, and other landlord costs.
- Calculates monthly landlord cash flow.
- Calculates gross-rent cash-flow break-even.
- Calculates long-term wealth break-even rent versus investing the same initial capital and additional contributions.
- Self-management toggle removes management fees.
- Bedroom estimates are anchored to local 1BR benchmarks and remain editable in sparse markets.

HOUSE ALPHA V9
- Replaces the single global break-even search with a segmented crossing scan.
- Selects the closest valid crossing to the user's current price/rate/rent.
- Labels mortgage break-even direction: either the rate needed to catch up or the maximum rate before renting wins.
- Adds property bedrooms for both primary residences and rentals.
- Adds Garage/storage situation: Auto, Included, Rent separately, or Not needed.
- Auto mode charges separate storage for small 1BR condos and assumes included storage for larger condos and single-family homes.
- Garage/storage assumptions are now independent of rental-versus-primary use.

HOUSE ALPHA V10
- Separates renter-paid garage/storage from owner-paid garage/storage.
- Either side can be Auto, Included, Rent separately, or Not needed.
- Adds current-rental bedroom count for renter-storage auto assumptions.
- Renter garage cost is added to the rent side and compounds with inflation.
- Owner garage cost remains part of ownership and rental-property operating costs.
- Break-even current rent is explicitly shown as base rent, with renter garage cost listed separately.
- Rental/investment mode hides the current-renter garage section because it is not part of that comparison.
