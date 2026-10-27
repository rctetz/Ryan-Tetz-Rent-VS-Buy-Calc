HOUSE ALPHA V43

This release makes House Alpha feel more responsive and alive while keeping the financial model clean, serious, and unchanged.

New in v43:
- Add a restrained Sierra ridgeline signature and one-time alpha-mark sheen without introducing looping decoration.
- Restore visible Save, Share, Copy, load, and error feedback on phone and tablet layouts with a compact action toast; keep an amber dot on the Save button while the scenario has unsaved edits.
- Make the original break-even slider more tactile with drag feedback and one confirmation pulse when it catches the sticky modeled break-even, without changing its range, step, or escape behavior.
- Show the immediate modeled outcome of a Decision Lever test beside the lever cards, with plain-English winner and margin feedback plus the existing Undo action.
- Add short, state-bounded cues when a deal checkpoint or monthly-cash winner actually changes, and a brief entrance when switching calculator sections or opening a disclosure.
- Make saved-property cards easier to browse with housing-type placeholders, focused hover treatment, and a one-time new-card reveal while keeping real thumbnails primary and local-only.
- Expand reduced-motion coverage so every new effect disappears when the device requests less motion.

Financial assumptions and calculation formulas are unchanged from v42.

VERSION HISTORY

HOUSE ALPHA V42

This release makes recurring monthly affordability visible across every strategy and adds a realistic zero-fixed-rent camper-van planning mode.

New in v42:
- Put a Total monthly cash bill panel ahead of long-term wealth, showing the complete month-one cash need for both strategies, the lower-cost option, the dollar difference, and each option's average monthly cash need over the selected holding period.
- Keep monthly cash and ending wealth separate: down payment, closing, setup, and immediate repairs remain upfront cash, while loan payments, taxes, insurance, HOA or site costs, maintenance reserves, storage, housing-income offsets, and commuting are included when applicable.
- Add a Roaming camper van / $0 fixed site rent preset with editable paid parking, relocation mileage, MPG, fuel price, variable tire and road wear, an optional storage unit, road-living services, and annual cost growth.
- Avoid double-counting van ownership in commuting: a roaming van's own-side commute uses fuel plus variable road wear per mile, while its insurance, registration, maintenance reserve, and depreciation remain in the housing strategy.
- Carry the cash-bill comparison and roaming breakdown into saved-property results, shared summaries, and printed decision briefs; saved housing options identify the lowest recurring cash need when comparable results are available.
- Keep legal and practical overnight parking explicitly unverified until the user reviews stay limits, seasonal access, sanitation, insurance, registration or address needs, and permission for recurring locations.
- Keep the manufactured-home, RV, and camper-van purchase-price rail fixed while it is being dragged, use matching $500 price bumps, expand only for an out-of-range exact price or modeled break-even, and let the next deliberate bump leave the sticky break-even point.

Important scope:
- Zero fixed rent does not mean zero housing cost or guaranteed free parking. Replace every starter input with the actual van, travel pattern, paid-night plan, insurance, repair reserve, and legal overnight locations.
- The cash panel is a recurring modeled planning total, not a household budget. Utilities and everyday spending appear only when entered, and upfront acquisition cash is shown separately.

HOUSE ALPHA V41

This release compares the location cost of where you rent or buy with where you work, while keeping route, schedule, storage, and maintenance assumptions visible and editable.

New in v41:
- Add an optional Commute comparison with separate renter-side and owner-side routes, distance, drive time, weekly round trips, weeks per year, and other transportation cost.
- Put modeled driving cost into the correct rent-versus-buy cash flows without treating personal commuting time as money or adding owner commute to a rental property's operating cost.
- Include editable Eastern Sierra town-route planning presets and make the exact annual miles, driving hours, and monthly cost visible before they influence the result.
- Let the renter-side town load its rent and storage benchmarks without changing the town of the property being purchased; storage remains excluded until its separate toggle is turned on.
- Add an optional location-aware maintenance planning reserve for higher-snow or remote-service areas while keeping the percentage editable and clearly separate from immediate repairs and HOA-covered work.
- Carry active commute assumptions into saved scenarios, Property History, shared summaries, and printed decision briefs; older scenarios continue with safe defaults.

Important scope:
- Route distances and drive times are clear-condition planning inputs. Replace them with the real home and job locations, and check Caltrans road and chain conditions for winter travel.
- The mileage rate is a whole-vehicle planning proxy, not a statement that ordinary commuting is tax deductible. Gas-only estimates can materially understate wear, depreciation, tires, and repairs.
- Maintenance percentages and town storage amounts are planning benchmarks, not bids or guaranteed local prices. Use inspection findings, written HOA responsibilities, contractor quotes, and current storage offers when available.

HOUSE ALPHA V40

This release makes manufactured-home, RV, and camper-van resale uncertainty visible instead of implying that one annual rate is accurate.

New in v40:
- Replace the two alternative-housing appreciation shortcuts with three editable resale stress cases: downside, base, and better resale.
- Show the selected ending unit value and all three scenario values at the chosen holding period, before selling costs and with land explicitly excluded.
- Keep the Ski Trails leased-site manufactured-home base at 0% unit resale growth, with -2% and +2% cases instead of applying Mammoth's ordinary-home appreciation rate.
- Use -13% / -10% / -5% for fifth-wheel planning and -12% / -8% / -4% for camper vans; these are stress cases, not forecasts.
- Update the Mammoth Ski Trails site-rent-growth planning input to 7%, reflecting the pace residents reported in 2026; the exact written lease still controls.
- Base alternative-housing maintenance reserves on purchase cost rising with repair inflation, so a depreciating RV or van no longer appears cheaper to maintain merely because its resale value falls.
- Include the projected unit resale value and land-exclusion note in shared summaries and printed decision briefs.

Why the range matters:
- FHFA's manufactured-home appreciation index covers real-property homes that include land and excludes personal-property/chattel homes, so it is not a valid direct proxy for a Ski Trails or Bishop leased-pad unit.
- Local repeat sales are sparse and can be distorted by remodeling, condition, park approval, site-rent changes, and thin marketing periods. House Alpha therefore keeps 0% as the leased-pad manufactured-home base and makes the uncertainty testable.

HOUSE ALPHA V39

This release adds a focused alternative-housing model for living in a manufactured/mobile home, fifth wheel/RV, or camper van without pretending that park rent is HOA or that a vehicle loan is a mortgage.

New in v39:
- Choose Manufactured / mobile home, Fifth wheel / RV, or Camper van from Property type; House Alpha automatically keeps these options in the primary-residence comparison.
- Load editable Mammoth and Bishop planning examples, including a $250,000 Ski Trails manufactured-home case, a Bishop manufactured home, a fifth wheel, and a camper van.
- Model leased-site rent, annual site-rent growth, other required park charges, added mobility costs, registration or personal-property tax, delivery/setup/winterization, repairs, insurance, maintenance, and unit resale appreciation or depreciation.
- Keep site rent separate from HOA and land equity. Leased-site rent creates no equity and continues after the unit loan ends.
- Use custom manufactured-home/chattel, RV, or vehicle-loan APR and term inputs with no mortgage-program fee, Freddie Mac substitution, or PMI.
- Stop unit-loan payments exactly when the entered term ends, while continuing site and ownership costs through the holding period.
- Extend the gray/red/green purchase-price slider and break-even search below $50,000 for lower-cost units.
- Save alternative housing options alongside real properties, including a private thumbnail, site-cost summary, complete inputs, and source link kept only in the local browser.
- Keep shared summaries private while including site cost, resale assumption, setup cost, and the modeled result; printed briefs show the site arrangement separately.
- Hold actual-option deal signals at Preliminary until the user confirms both the unit facts and park/private-site placement review.
- Preserve the existing condo, single-family, repair-planner, property-history, lookup, sharing, and break-even behavior.

Important scope:
- Mammoth Ski Trails examples observed for this release were roughly $1,500-$1,630 per month in listed site charges; the preset uses $1,590, not the older $1,000-$1,200 assumption. Always replace it with the exact written lease for the chosen unit.
- The Bishop RV $650 monthly site figure is an editable planning estimate, not a quoted park rate. Verify monthly availability, legal full-time occupancy, rig limits, utilities, and winter service directly with the park.
- Private-site mode assumes the site is already owned or free to use. It excludes land purchase cost, land value, land property tax, permits, and land equity.

HOUSE ALPHA V38

This release adds a compact repair and renovation planner for underwriting a real property without cluttering the main calculator.

New in v38:
- Keep the repair budget behind one collapsed Repairs & renovation row until it is needed.
- Enter one quick total or build a draft from safety and structural, roof and exterior, systems, interior and appliances, and other project categories.
- Add an adjustable contingency cushion, with a 15% planning default that can be reduced as inspection findings and contractor bids become firm.
- Review the category subtotal, contingency, and total before explicitly applying the draft to the financial model. Draft edits never silently change the result.
- Treat the applied total as acquisition cash and investment opportunity cost, while keeping ongoing maintenance separate and adding no automatic resale value.
- Save and reopen the full repair worksheet with a property, and show an applied repair budget on saved-property cards, shared summaries, and printed decision briefs.
- Preserve v37 saved properties and scenarios; missing repair-planner fields restore to safe defaults.

HOUSE ALPHA V37

This release adds a private, low-clutter Property History for returning to real-property matches and underwriting scenarios without losing the focused calculator workflow.

New in v37:
- Save an actual-property match or the current property scenario to a compact local deal library.
- Browse saved properties with an optional thumbnail, property name or address, asking price, saved date, and match details.
- Reopen a saved property with its full underwriting inputs so a promising deal can be revisited and adjusted.
- Add or remove an optional property photo. The browser resizes the image locally for a lightweight thumbnail.
- Keep Property History, addresses, source links, and thumbnails only in that browser profile on that device. There is no account or cloud sync, so another device or browser will not automatically see the saved properties.
- Keep thumbnails out of Census and RentCast requests and out of shared result text. Only the typed address is sent when the user explicitly runs an online property lookup.
- Delete individual saved properties without affecting the current calculator scenario.
- Keep Property History when Reset is used; Reset clears the working/saved calculator scenario, not the separate local deal library.

Local-data note:
- Property History depends on browser storage. Clearing site data, using private browsing, or removing browser storage can erase it. Keep the original listing or another record for anything important.

HOUSE ALPHA V36

This release strengthens calculation accuracy, saved-scenario comparisons, and private detailed-property access while preserving the v35 review workflow and public Census address matching.

New in v36:
- Treats the entered stock-market return as an effective annual return and converts it to the mathematically equivalent monthly compound rate.
- Detects exact break-even roots at search endpoints, so a threshold equal to the minimum or maximum tested value is no longer missed.
- Saves automatic/manual input flags and the calculation-engine version with each scenario. Comparisons are shown only when the saved and current results use the same calculation version and input state.
- Keeps U.S. Census address normalization public while placing paid RentCast enrichment behind a private access code and signed, time-limited, HTTP-only session cookie.
- Reduces the common purchase-property enrichment to one RentCast active-listing call. Rental and live-in modes add a second call for a rent estimate; a broader property-record call is used only as a fallback when the listing is absent or too sparse.
- Preserves Current vs Found review, selective apply, provenance, undo, manual entry, and the preliminary Deal checkpoint from v35.

Required Render environment variables for detailed property enrichment:
- `PROPERTY_LOOKUP_ACCESS_CODE`: the private code trusted users enter before a paid lookup.
- `PROPERTY_LOOKUP_SESSION_SECRET`: a long random server-side secret used to sign access cookies. Render can generate it; never reuse the access code.
- `RENTCAST_API_KEY`: the private RentCast key. Never put it in index.html or a public repository.
- `HOUSE_ALPHA_ORIGIN`: the exact public HTTPS origin, for example `https://mammoth-rent-vs-buy.onrender.com`.

Property lookup and billing notes:
- House Alpha requests RentCast's `suppressLogging=true` option and sends only the entered address. Restrict the key to the active-sale-listing, long-term-rent-estimate, and property-record endpoints in the RentCast dashboard.
- A typical uncached primary-residence enrichment uses 1 RentCast call. Rental and live-in enrichment normally use 2 because they also request a rent estimate. A sparse or missing listing can trigger 1 additional property-record fallback call.
- `RENTCAST_PROCESS_CALL_LIMIT` is an optional per-server-process emergency ceiling (default 30). It resets when the server process restarts, so it is not a durable monthly billing cap and does not replace RentCast account quota or billing controls.
- RentCast documents that each successful 200 response with a body counts against the account billing period: https://developers.rentcast.io/reference/billing-and-pricing
- Without an authorized cookie--or without a configured RentCast key--House Alpha still matches U.S. addresses and suggests a supported benchmark market when available.
- Census-only results are address-range normalization/geocoding, not parcel, unit, deliverability, structure, or listing verification.

HOUSE ALPHA V34

This release adds a low-clutter actual-property underwriting layer without removing the existing strategy calculator.

New in v34:
- Attach a property nickname, address or listing title, and optional source link to the current scenario.
- Keep address and listing details local to the device; shared text omits both by default.
- Protect exact deal inputs from benchmark-location, property-type, and bedroom changes while actual-property mode is active.
- Add immediate repairs / work as upfront cash with no automatic resale value, including its opportunity cost in every strategy.
- Show a Deal checkpoint based on exact ending wealth, price-root orientation, and rental cash flow--not the heuristic Alpha score.
- Distinguish Works as modeled, Negotiate, Rework the plan, and Walk-away signal under current assumptions.
- Preserve every purchase-price crossing so nonstandard or multiple roots are never mislabeled as a safe offer.
- Let users test a legitimate lower wealth-parity price and then undo it through the existing decision-lever workflow.
- Save, restore, print, and share actual-property scenarios while keeping the generic calculator available.

HOUSE ALPHA V33.1

This release fixes the price break-even control and makes financing choices genuinely progressive.

New in v33:
- Automatically expands the purchase-price slider so a modeled break-even is reachable instead of pinning it outside the range.
- Keeps the exact break-even amount visible and adds a one-tap Use break-even action.
- Collapses low-down presets behind one neutral row so VA and FHA labels do not linger in unrelated scenarios.
- Shows only the selected loan program until Change loan type is opened.
- Shows only programs compatible with the current down payment inside the chooser.
- Hides all program controls at 20% or more and all financing controls for a cash purchase, while retaining one compact financing-details disclosure when relevant.
- Keeps the Down payments table on the selected loan program below 20% instead of silently swapping in unrelated programs.
- Normalizes each comparison row to that row's program-specific estimated rate.
- Reveals the modeled PMI assumptions for 15% investment-property scenarios instead of applying a hidden cost.

HOUSE ALPHA V32

This release restores the focused interaction of the original calculator while keeping the deeper v31 analysis tools.

New in v32:
- Restores a neutral gray purchase-price slider with a separate green/amber/red decision rail.
- Keeps the modeled break-even label visible at the nearest edge when it falls outside the displayed price range.
- Preserves the original near-break-even snap behavior.
- Moves the duplicate hero price-position graphic behind a compact disclosure.
- Hides unavailable conventional and FHA loan choices as down payment changes; the entire program selector still disappears when it is not relevant.
- Collapses loan-model prose, lender notes, optional shared-housing/ADU income, and secondary growth/transaction inputs without removing any features.
- Automatically reopens an active or invalid disclosure so hidden controls never conceal a modeled assumption or validation error.
- Keeps round 10% stock and 4% home-price defaults, labels both as nominal planning assumptions, and retains the 7%/3% cautious stress presets.

HOUSE ALPHA V31

This release turns House Alpha into a sharper, more visual decision instrument while preserving the transparent local model.

New in v31:
- A redesigned outcome hero makes the winner, modeled wealth advantage, ending wealth, and price break-even immediately legible.
- A responsive, interactive wealth-path chart supports mouse, touch, and keyboard inspection without an external chart library.
- Decision-lever cards let you try the modeled price, rate, or rent break-even and undo the experiment in one click.
- Saved-scenario comparison shows how current edits change ending advantage, month-one economics, and break-even price.
- A focused print layout creates a clean decision brief from the current scenario.
- A bespoke 1200x630 House Alpha preview card sharpens shared links and social unfurls.
- A compact masthead and workspace bar improve hierarchy, density, and mobile usability.
- Expanded numeric guardrails cover ADU loans, costs, rents, sizes, and operating assumptions; rental scenarios require at least 15% down.
- Live-in scoring and break-even copy now respect moves beyond the selected holding period.
- Investment-ADU break-evens are suppressed when construction finishes beyond the holding period.
- Modeled ADU added value now carries corresponding property-tax and maintenance costs after completion.

HOUSE ALPHA V30

This release polishes the existing House Alpha model without changing its core financial assumptions.

New in v30:
- Save one complete scenario on the current device and restore it after reopening the app.
- Share a concise, mode-aware result summary through the phone share sheet or clipboard.
- Reset saved edits with confirmation.
- Adds a compact result summary near the top, with a direct jump to full details.
- Refreshes market benchmarks without erasing manual scenario edits.
- Adds clearer loading, validation, keyboard, focus, tab, and switch behavior.
- Improves phone layouts, touch targets, tables, safe-area spacing, and the install prompt.
- Removes the false $50,000 break-even marker when no modeled crossing exists.
- Validates unsafe values such as zero-year mortgage terms and negative holding periods.
- Fixes live-in move dates that fall beyond the modeled holding period.
- Defers the expensive down-payment comparison until that tab is opened.
- Strengthens offline data caching so an installed app can reopen with its last known location data.
- Parallelizes live mortgage, rent, and home-value checks and reports saved fallbacks honestly when parsing fails.

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
- Adds estimated rent by location, property type (condo or single-family), and 1-4 bedrooms.
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

HOUSE ALPHA V19
- Simplifies Shared Housing / Income Offsets.
- Removes duplicated disabled local-estimate fields; estimate buttons now fill the main rent fields.
- Renames growth controls to Annual rent increase.
- Replaces separate utilities and miscellaneous inputs with one Utilities / other monthly field.
- Adds an owner-side Professional Management toggle, off by default.
- Arrangement-specific controls now hide irrelevant fields.
- Build New ADU now includes construction cost, completion time, cash or loan funding, loan rate, and loan term.
- New ADU rent begins only after the selected construction period.
- Cash-funded ADU construction is compared against investing the same capital in the S&P 500.
- Loan-funded ADU construction includes loan payments and remaining loan balance.

HOUSE ALPHA V20
- Renames the 10% S&P 500 preset from Base to Average.
- Keeps the 7% Conservative preset.
- Adds an optional Investment Property ADU module.
- Investment ADU inputs include construction cost, estimated value added, construction delay, cash/loan funding, loan rate and term.
- Adds ADU rent, vacancy, repairs/capex, Utilities / other, annual rent increase, and optional professional management.
- Investment-property and ADU professional management are off by default.
- Cash-funded ADUs are compared with investing the same cash in the S&P 500.
- Loan-funded ADUs include payments and remaining loan balance.
- ADU rent starts only after construction is complete.
- Adds ADU rent and construction-cost break-even results.
- Corrects cash-funded owner-occupied ADU opportunity-cost handling to avoid double-counting the construction cash.

HOUSE ALPHA V21
- Adds 4% Average and 3% Conservative home-appreciation presets.
- Home appreciation now defaults to 4%.
- The appreciation field remains editable for custom scenarios.
- Investment-property professional management remains off by default.
- Turning professional management on automatically suggests an 8% fee when the current fee is blank or zero.
- Users may still edit the management rate after enabling it.

HOUSE ALPHA V22
- Adds ADU value-added assumptions to both owner-occupied and investment-property Build New ADU paths.
- Defaults to 75% of construction cost (Conservative).
- Adds 100% of cost (Cost basis), Local market proxy, and Custom / appraisal options.
- Local proxy uses ADU finished square feet x editable local listing $/sq ft x 75%.
- Adds location-specific city, county, or nearby price-per-square-foot planning benchmarks and source links.
- Sparse markets are explicitly identified as county or nearby fallbacks.
- Local market proxies are labeled as planning estimates, not appraisals.
- Root and break-even calculations now derive ADU value from the selected method rather than a stale fixed field.

HOUSE ALPHA V23
- Removes the universal $250,000 ADU construction default.
- Adds location-adjusted planning build cost per square foot.
- ADU size defaults by bedroom count: 600, 800, 1,000, or 1,200 square feet.
- Total construction cost is automatically calculated from size x regional build-cost assumption.
- Both owner-occupied and investment-property ADUs include a Use Local Build Estimate button.
- Size, cost per square foot, and total cost remain editable; manual total costs are preserved.
- Regional estimates are labeled as planning assumptions, not contractor bids.
- Investment-property price slider now reads PROPERTY WINS versus S&P 500 WINS.
- Primary-residence slider reads BUYING WINS versus RENTING WINS.
- Replaces the word Snapped with Break-even at the modeled threshold.

HOUSE ALPHA V24
- Hides the investment-property management percentage when professional management is off.
- Moves the management-rate field directly beneath the professional-management switch.
- Turning professional management on reveals the field and suggests 8%.
- Professional management remains off by default.
- Users can edit the suggested 8% after enabling management.

HOUSE ALPHA V25
- Owner garage/storage now displays $0 when Included with purchased property is selected.
- Owner garage/storage now displays $0 when Not needed after buying is selected.
- Rent separately as an owner restores the selected location's garage/storage market estimate.
- PMI controls are hidden whenever the down payment is 20% or greater.
- Below 20% down, the PMI rate and cancellation fields appear only when Estimate PMI is enabled.

HOUSE ALPHA V26
- Adds primary-residence down-payment presets: 0%, 3%, 3.5% FHA, 5%, 10%, 15%, 20%, and Cash.
- Keeps 20% as the primary-residence default.
- Adds rental-property presets: 15%, 20%, 25%, and Cash.
- Adds Conventional, FHA, VA, and USDA Guaranteed loan-program planning models.
- Conventional remains selected by default.
- Low-down-payment selections reveal program choices and eligibility disclaimers.
- The app now refreshes the live Freddie Mac PMMS benchmark on initial load and location refresh.
- Estimated rates update from the live benchmark using transparent planning adjustments.
- A manual rate can still be entered and preserved; Use Current Estimate restores automatic pricing.
- FHA models 1.75% financed upfront MIP and current typical annual MIP assumptions.
- VA models current first-use/subsequent-use funding-fee tiers and an exemption toggle.
- USDA Guaranteed models a 1% financed upfront fee and 0.35% annual fee.
- Conventional PMI remains editable and is shown only below 20% down.
- Cash purchases hide mortgage-program, rate, term, and mortgage-insurance controls.

HOUSE ALPHA V27
- Adds a USDA Guaranteed income-limit information box when USDA is selected.
- Limits update with the selected House Alpha location and its USDA county/HUD area.
- Displays separate individual, couple, 3-4 person, and 5-8 person cards.
- Clarifies that USDA officially uses the same limit for all 1-4 person households.
- Adds a household-size selector and highlights the applicable limit.
- Uses USDA FY 2026 adjusted income limits effective July 13, 2026.
- Clarifies that limits apply to adjusted annual household income, not only borrower income.
- Links to USDA's official limit table and exact property/income eligibility checker.
- Notes that address eligibility must still be checked separately.

HOUSE ALPHA V28
- Shortens the USDA eligibility link label to "Check exact address."

HOUSE ALPHA V29
- Adds a dedicated Live-In Rental / Owner in ADU strategy mode.
- Models an owner living in the main home before moving into an ADU, or living elsewhere while the property begins as a full rental.
- Supports an existing ADU or construction of a new ADU with cash/loan funding, completion delay, and value-added assumptions.
- Models renting the main home after the owner moves into the ADU.
- Optionally models renting the ADU before owner move-in when an available ADU precedes the move date.
- Compares the strategy against renting a comparable ADU/apartment elsewhere and investing the same initial cash and monthly differences in the S&P 500.
- Adds live-in strategy result labels, timeline metrics, milestones, break-even main-home rent, comparable-rent crossing, price/rate thresholds, sensitivity results, and down-payment comparisons.
- Keeps owner-occupied loan-program planning controls available, with a clear delayed-occupancy financing warning.
