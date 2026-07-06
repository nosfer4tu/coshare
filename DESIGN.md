<!-- SEED: re-run $impeccable document once there's code to capture the actual tokens and components. -->

---
name: CoShare.jp
description: Codeshare flight price-gap detector for Japan-based travelers
---

# Design System: CoShare.jp

## 1. Overview

**Creative North Star: "The Fare Ledger"**

CoShare.jp reads like a precise, trustworthy ledger of fares, not a travel-marketing brochure. The surface stays quiet — restrained neutrals doing most of the work — so that a single teal/cyan accent can carry all the weight of "this is the number that matters." Precision comes from a display + mono type pairing: mono numerals give prices, dates, and fare codes the fixed-width legibility of a boarding pass or a terminal display, while the display face handles headlines and section titles with quiet confidence. Motion is responsive, not decorative — the interface reacts clearly when a search runs or a price updates, but never performs for its own sake.

The system explicitly rejects the generic SaaS/AI template look (cream backgrounds, gradient text, eyebrow labels, identical card grids) and the cluttered legacy travel-site look typified by Expedia/Kayak circa 2015 (banner-ad density, popup upsells, overwhelming comparison tables). References worth holding in mind: Google Flights' price-first results list, Linear's restrained modern precision, and Japanese transit apps' ability to present dense, legible data in Japanese without feeling cramped.

**Key Characteristics:**
- Restrained neutral base; one teal/cyan accent reserved for price emphasis and codeshare-gap callouts
- Display + mono pairing — mono for anything numeric (prices, dates, fare codes)
- Responsive motion only: feedback on load/search/update, no scroll choreography
- Japanese-first legibility: type and spacing chosen to handle CJK text as the primary language, not a cramped afterthought

## 2. Colors

Tinted neutrals carry the surface; a single teal/cyan accent is reserved for what matters — the price, the gap, the call to action.

### Primary
- **Fare Teal** `[to be resolved during implementation — teal/cyan hue family]`: The one accent color in the system. Used for the cheapest-price highlight, codeshare price-gap badges, primary CTA (search button), active states, and links. Reserved to ≤10% of any given screen — see The One Signal Rule below.

### Neutral
- **Ink** `[to be resolved — near-black for headings/high-emphasis text]`: Headings, prices, primary text.
- **Body** `[to be resolved — mid-gray, must clear 4.5:1 against Paper]`: Body copy, secondary labels.
- **Paper** `[to be resolved — true off-white or very light neutral, not a warm cream/sand]`: Base background.
- **Surface** `[to be resolved — one step off Paper]`: Cards, input fields, result rows.
- **Border** `[to be resolved — light neutral, low contrast]`: Dividers, input outlines, table rules.

### Named Rules
**The One Signal Rule.** Fare Teal appears only where the user needs to act or notice a price signal — never as generic decoration. If you're reaching for the accent to make a section "feel branded," don't; let neutrals and typography carry identity instead.

## 3. Typography

**Display Font:** `[to be chosen at implementation — a clean geometric or grotesque display face with full Japanese (CJK) coverage or a paired CJK font]`
**Body Font:** `[to be chosen at implementation — the display family's regular/text weights, or a matching sans]`
**Mono Font:** `[to be chosen at implementation — a legible monospace for numerals: prices, dates, fare codes]`

**Character:** Display carries quiet confidence at low weight; mono gives every number the fixed-width precision of a boarding pass. The pairing should read as "instrument panel," not "brochure."

### Hierarchy
- **Display** (light–medium weight, large clamp): Page-level headings only (e.g. hero search prompt).
- **Headline** (medium weight): Section titles (search results, trend chart, destination guide).
- **Title** (medium weight, mono for any numeric title): Card/result headers — route, date.
- **Body** (regular weight): Descriptive copy, fare rules, supporting text. Cap at 65–75ch.
- **Label** (medium weight, small size): Form labels, filters, badges.
- **Numeral** (mono, tabular figures): All prices, dates, flight numbers, fare codes — anywhere digits need to align and read at a glance.

### Named Rules
**The Tabular Numerals Rule.** Every price and date renders in mono with `font-variant-numeric: tabular-nums` so columns of numbers align without extra layout work — non-negotiable for a fare-comparison table.

## 4. Elevation

Flat by default, per the Restrained motion energy and minimal personality. Depth is conveyed through the Surface/Paper neutral step and thin borders, not shadows. A shadow may appear only as a direct response to interaction (hover on an actionable result row, a focused input, an open dropdown) — never as ambient decoration on static cards.

### Named Rules
**The Flat-At-Rest Rule.** Result cards, search bar, and nav sit flush against Paper with a Border-colored 1px rule, not a shadow. Shadows are reserved for transient, interactive states only.

## 5. Components

No components exist yet in styled form — the frontend (SearchBar, FlightCard, CodeShareCard, PriceTrendChart, Navbar) is currently unstyled Vite scaffolding. Re-run `$impeccable document` in scan mode once these are styled to capture real component specs.

## 6. Do's and Don'ts

### Do:
- **Do** keep the surface restrained: tinted neutrals doing the work, Fare Teal reserved for price signals and CTAs only (≤10% of any screen).
- **Do** use mono/tabular numerals for every price, date, and fare code so results scan and align cleanly.
- **Do** treat Japanese as the primary language in type and spacing decisions, not as a translated afterthought.
- **Do** limit motion to responsive feedback (search loading, result appearance, price updates) — clear, not choreographed.
- **Do** make the cheapest option and any codeshare price gap immediately scannable, per PRODUCT.md's "price is the hero" principle.

### Don't:
- **Don't** use a generic SaaS/AI template look: no cream/sand backgrounds, no gradient text, no tiny uppercase eyebrow labels above every section, no identical repeating card grids, no glassmorphism-as-decoration.
- **Don't** replicate the cluttered legacy travel-site look — no banner-ad density, no popup upsells, no overwhelming comparison tables, no competing CTAs. Specifically: nothing that reads like Expedia or Kayak circa 2015.
- **Don't** pair `border: 1px solid` with a soft wide `box-shadow` on the same card or button — pick one.
- **Don't** round cards or inputs beyond 12–16px; save full-pill radii for tags/badges only.
- **Don't** apply ambient shadows to static, at-rest surfaces — shadows are interaction-only per the Flat-At-Rest Rule.
