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

HOUSE ALPHA V11
- Shows bedrooms only in Rental / Investment Property mode.
- Bedroom selection updates both estimated collected rent and estimated purchase price.
- Adds editable location home-value benchmarks and property-type/bedroom price estimates.
- Price slider dynamically narrows around the local estimated purchase price.
- Removes the black vertical break-even marker; uses a small arrow above the track only.
- Slider snaps precisely near break-even and shows a short snapped-value message.
- Adds a prominent independent renter-paid garage/storage switch and amount.
- Renter garage/storage raises only the renting side of the primary-residence comparison.
- Fixes initial premium to compare owner cost with total renter cost including renter storage.
- Fixes an old initialization reference that could prevent some controls from loading correctly.

HOUSE ALPHA V12
- Separates Primary Residence and Rental / Investment Property into distinct comparisons.
- Investment mode compares the rental-property strategy directly with an S&P 500 index-fund strategy.
- Removes renter, renter-storage, and owner-garage comparisons from investment mode.
- Rental-property storage/garage costs are forced to zero and the garage UI is hidden in investment mode.
- Adds estimated rent by location, property type (condo or single-family), and 1–4 bedrooms.
- Gross collected rent and its market-rent cap can auto-load from the selected property estimate.
- Rental income growth is capped by a market-rent ceiling that rises with inflation.
- Adds a Use Local Rent Estimate button and preserves manual rent overrides.
- Investment results relabel all metrics, milestones, and break-even text around S&P 500 versus rental-property wealth.

V12 FINAL PATCH
- Investment gross-rent break-even now moves the tested market-rent cap with rent.
- Down-payment comparison relabels and recalculates monthly property costs for investment mode.
- Adds clearer no-crossing language when a rental continues to trail the S&P 500.

HOUSE ALPHA V13
- Mortgage-rate searches now begin at a true 0%.
- Replaces raw '0.01' no-crossing output with plain language explaining that even a 0% mortgage would not make buying catch up.
- Renter-paid garage/storage is always off by default, including after location changes.
- Removes Auto from the owner garage/storage dropdown.
- Condo/townhome visibly defaults to Rent separately as owner.
- Single-family home visibly defaults to Included with property.
- The native phone dropdown displays the currently selected option with its normal checkmark.
- Users can still manually select Included, Rent separately, or Not needed.

HOUSE ALPHA V14
- Keeps 10% as the default S&P 500 annual return.
- Adds one-tap 10% Base and 7% Conservative return presets.
- Preset buttons visually show the active assumption.
- The return input remains fully editable for custom assumptions.
- Adds a side-by-side 10% versus 7% sensitivity section to every result.
- Sensitivity values recalculate for both primary-residence and rental-investment modes.

HOUSE ALPHA V15
- Adds a Shared Housing / Income Offsets module to Primary Residence mode.
- Models a renter receiving a roommate contribution.
- Models an owner receiving income from a roommate, existing ADU, owner-occupied duplex unit, or custom space.
- Includes vacancy, management, repairs/capex, utilities, other expenses, and income growth.
- Uses local rent benchmarks for roommate, ADU, and duplex income estimates.
- Calculates effective renter cost after roommate contribution.
- Calculates effective owner cost after net housing income.
- Invests monthly savings on the appropriate side for a fair wealth comparison.
- Adds shared-housing result cards and owner-income break-even analysis.
- Keeps the pure Rental / Investment Property versus S&P 500 calculator separate.
- Fixes a duplicate JavaScript helper declaration present in an earlier package.

HOUSE ALPHA V16
- Investment Property mode now defaults to 0% property management.

HOUSE ALPHA V17
- Replaced 'Custom income space' with 'Build new ADU' in owner-occupied housing options.
