# RISKCAST Input Page — Design Specification v1.0
## "Command Center" — A Future-Forward Enterprise Form Experience

**Product:** RISKCAST VisionOS Edition  
**Page:** Input (Entry Point)  
**Version:** 1.0  
**Date:** January 2026  
**Authors:** Product Design + UX Architecture + Design Systems

---

## Table of Contents

1. [North Star Concept](#1-north-star-concept)
2. [Layout Specifications](#2-layout-specifications)
3. [Information Architecture & Section Flow](#3-information-architecture--section-flow)
4. [Component Library Specification](#4-component-library-specification)
5. [Interaction Model](#5-interaction-model)
6. [Microcopy & Tone Guide](#6-microcopy--tone-guide)
7. [Figma Blueprint](#7-figma-blueprint)
8. [Design Variants (A/B)](#8-design-variants-ab)
9. [Data Ownership & Trust Signals](#9-data-ownership--trust-signals) *(NEW)*
10. [Field Provenance System](#10-field-provenance-system) *(NEW)*
11. [Preview Panel Performance](#11-preview-panel-performance) *(NEW)*

---

## 1. North Star Concept

### Vision Statement

> "The RISKCAST Input experience transforms complex logistics data entry from a tedious checklist into a confident, decision-first command center—where every keystroke builds toward a clear outcome, and the interface anticipates your next move."

### Core Philosophy

**Command Center, Not Data Entry**

This redesign treats the Input page not as a traditional form, but as a **mission briefing interface**—where users are commanders preparing for a logistics operation. Every element serves one purpose: building confidence that the risk analysis will deliver actionable insights.

### Key Design Pillars

| Pillar | Description | Implementation |
|--------|-------------|----------------|
| **Decision-First** | Always answer "What do I need to do next?" and "What will I get?" | Live preview panel, completeness meter, CTA clarity |
| **Progressive Confidence** | Build user confidence incrementally through feedback | Real-time validation, smart defaults, autosave indicators |
| **Low Cognitive Load** | Reduce mental effort through chunking and smart disclosure | Section grouping by decision flow, "Basic/Advanced" modes |
| **Traceability** | Never lose work, always know status | Draft timestamps, case IDs, session recovery |
| **Premium Enterprise** | Communicate trust and sophistication | VisionOS glass aesthetic, refined typography, deliberate motion |

### The Experience In One Sentence

*"Enter your shipment details on the left, watch your analysis preview build on the right, and submit with confidence when the meter hits 100%."*

---

## 2. Layout Specifications

### 2.1 Desktop Layout (≥1280px)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ HEADER (Fixed, 64px)                                                          │
│ [Logo] [Case ID: RC-2026-0142 • Draft saved 2m ago]     [Search] [?] [👤]    │
├────────────┬─────────────────────────────────────────────────────────────────┤
│ SIDEBAR    │ MAIN CONTENT AREA (12-column grid, max-width: 1400px)           │
│ (240px)    │                                                                  │
│ Fixed      │  ┌─────────────────────────────────┬──────────────────────────┐ │
│            │  │ FORM PANEL (8 columns)          │ PREVIEW PANEL (4 cols)   │ │
│ ┌────────┐ │  │                                 │ [Sticky on scroll]       │ │
│ │ Mode   │ │  │  ┌───────────────────────────┐  │                          │ │
│ │ Toggle │ │  │  │ Section: Route & Service │  │  ┌──────────────────────┐ │ │
│ │○ Basic │ │  │  │ [Trade Lane ▾] [Mode ▾]   │  │  │ ROUTE SUMMARY        │ │ │
│ │● Advncd│ │  │  │ [Service Route ▾]         │  │  │ ─────────────────    │ │ │
│ └────────┘ │  │  │ [POL ⌕] ────→ [POD ⌕]     │  │  │ HCM → SHA            │ │ │
│            │  │  └───────────────────────────┘  │  │ Ocean FCL • 12 days  │ │ │
│ NAVIGATION │  │                                 │  │ ONE Alliance         │ │ │
│ ───────────│  │  ┌───────────────────────────┐  │  └──────────────────────┘ │ │
│ ✓ Route    │  │  │ Section: Schedule        │  │                          │ │
│ ○ Schedule │  │  │ [ETD 📅] [Transit] [ETA]  │  │  ┌──────────────────────┐ │ │
│ ○ Cargo    │  │  │ [ETA 📅]                  │  │  │ CARGO SUMMARY        │ │ │
│ ○ Value    │  │  └───────────────────────────┘  │  │ ─────────────────    │ │ │
│ ○ Parties  │  │                                 │  │ Electronics          │ │ │
│ ○ Modules  │  │  ┌───────────────────────────┐  │  │ 20,915 kg • 42 m³    │ │ │
│ ○ Upload   │  │  │ Section: Cargo Details   │  │  │ ⚠ Fragile            │ │ │
│            │  │  │ [Type ▾] [Weight] [Vol]  │  │  └──────────────────────┘ │ │
│            │  │  │ [Sensitivity ● ○ ○ ○]     │  │                          │ │
│            │  │  └───────────────────────────┘  │  ┌──────────────────────┐ │ │
│            │  │                                 │  │ COMPLETENESS         │ │ │
│            │  │  ┌───────────────────────────┐  │  │ ─────────────────    │ │ │
│            │  │  │ Section: Value & Terms   │  │  │ ████████░░░░ 67%     │ │ │
│            │  │  │ [$85,000 USD] [Incoterm] │  │  │ 8 of 12 required     │ │ │
│            │  │  └───────────────────────────┘  │  │                      │ │ │
│            │  │                                 │  │ ✓ Route selected     │ │ │
│            │  │  ┌───────────────────────────┐  │  │ ✓ Cargo complete     │ │ │
│            │  │  │ Section: Parties         │  │  │ ✗ Seller country     │ │ │
│            │  │  │ [Seller] [Buyer] tabs     │  │  └──────────────────────┘ │ │
│            │  │  └───────────────────────────┘  │                          │ │
│            │  │                                 │  ┌──────────────────────┐ │ │
│            │  │  ┌───────────────────────────┐  │  │ WHAT YOU'LL GET      │ │ │
│            │  │  │ Section: Risk Modules    │  │  │ ─────────────────    │ │ │
│            │  │  │ [●ESG ●Weather ●Port...]  │  │  │ • Risk Score 0-10    │ │ │
│            │  │  └───────────────────────────┘  │  │ • Route Analysis     │ │ │
│            │  │                                 │  │ • Recommendations    │ │ │
│            │  │  ┌───────────────────────────┐  │  │ • Insurance Options  │ │ │
│            │  │  │ Section: Upload (opt.)   │  │  └──────────────────────┘ │ │
│            │  │  │ [Drag packing list here] │  │                          │ │
│            │  │  └───────────────────────────┘  │                          │ │
│            │  │                                 │                          │ │
│            │  └─────────────────────────────────┴──────────────────────────┘ │
│            │                                                                  │
│            │  ┌──────────────────────────────────────────────────────────────┐│
│            │  │ STICKY CTA BAR                                               ││
│            │  │ Progress ████████░░░░ 8/12 required    [Save Draft] [Run →] ││
│            │  │ ⌨ Tab to navigate • Enter to submit                          ││
│            │  └──────────────────────────────────────────────────────────────┘│
└────────────┴─────────────────────────────────────────────────────────────────┘
```

### 2.2 Grid Specifications (Desktop)

| Element | Specification |
|---------|---------------|
| **Viewport** | Min 1280px, optimal 1440px |
| **Max Content Width** | 1400px (centered) |
| **Grid** | 12 columns, 24px gutter |
| **Column Width** | ~93px (at 1400px) |
| **Sidebar** | Fixed 240px, collapsible to 64px (icon-only) |
| **Header** | Fixed 64px height |
| **Form Panel** | 8 columns (spans cols 1-8) |
| **Preview Panel** | 4 columns (spans cols 9-12), sticky |
| **CTA Bar** | Full width, sticky bottom, 80px height |

### 2.3 Tablet Layout (768px - 1279px)

```
┌─────────────────────────────────────────────────────┐
│ HEADER (64px)                                        │
│ [☰] [Logo] [Case ID]              [?] [👤]          │
├─────────────────────────────────────────────────────┤
│ MAIN CONTENT (Single column, full width)            │
│                                                      │
│  ┌─────────────────────────────────────────────────┐│
│  │ PREVIEW SUMMARY (Collapsed, expandable)         ││
│  │ [HCM → SHA • $85k • 67% complete] [Expand ▾]   ││
│  └─────────────────────────────────────────────────┘│
│                                                      │
│  ┌─────────────────────────────────────────────────┐│
│  │ Section: Route & Service                        ││
│  │ ┌─────────────────┐ ┌─────────────────┐         ││
│  │ │ [Trade Lane ▾]  │ │ [Mode ▾]        │         ││
│  │ └─────────────────┘ └─────────────────┘         ││
│  └─────────────────────────────────────────────────┘│
│                                                      │
│  [... more sections ...]                            │
│                                                      │
│  ┌─────────────────────────────────────────────────┐│
│  │ STICKY CTA BAR                                  ││
│  │ ████████░░░░ 67%  [Draft] [Run Analysis →]      ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

**Tablet Adaptations:**
- Sidebar: Hidden by default, hamburger menu trigger
- Preview Panel: Collapsed to single-line summary bar, expandable
- Form Grid: 2 columns where possible, 1 column for complex fields
- CTA Bar: Simplified, always visible

### 2.4 Mobile Layout (<768px)

```
┌───────────────────────────────┐
│ HEADER (56px)                  │
│ [☰] [Logo]         [?] [👤]   │
├───────────────────────────────┤
│ PROGRESS BAR (Thin, fixed)    │
│ ████████░░░░░░░░░░ 67%        │
├───────────────────────────────┤
│ MAIN CONTENT (Full width)     │
│                               │
│ ┌───────────────────────────┐ │
│ │ Section: Route & Service  │ │
│ │ ┌─────────────────────┐   │ │
│ │ │ Trade Lane          │   │ │
│ │ │ [Select ▾]          │   │ │
│ │ └─────────────────────┘   │ │
│ │ ┌─────────────────────┐   │ │
│ │ │ Mode                │   │ │
│ │ │ [Select ▾]          │   │ │
│ │ └─────────────────────┘   │ │
│ └───────────────────────────┘ │
│                               │
│ [... more sections ...]       │
│                               │
├───────────────────────────────┤
│ STICKY CTA (64px)             │
│ [Save Draft] [Run Analysis →] │
└───────────────────────────────┘
```

**Mobile Adaptations:**
- Sidebar: Full-screen overlay navigation
- Preview Panel: Hidden, accessible via "Preview" FAB or section completion summary
- Form Grid: 1 column exclusively
- All fields: Full width
- Progress: Thin bar at top instead of meter
- CTA Bar: Two buttons, full width

---

## 3. Information Architecture & Section Flow

### 3.1 Grouping Philosophy: Decision Flow

The form is restructured from 6 arbitrary sections to **7 decision-oriented groups** that mirror how logistics professionals think:

| Old Structure | New Structure | Decision Question |
|---------------|---------------|-------------------|
| Transport Setup (partial) | **A. Route & Service** | "Where is it going and how?" |
| Transport Setup (partial) | **B. Schedule** | "When does it depart and arrive?" |
| Cargo & Packing | **C. Cargo Details** | "What am I shipping?" |
| Cargo & Packing (partial) | **D. Value & Terms** | "What's it worth and who's responsible?" |
| Seller + Buyer | **E. Parties** | "Who's involved?" |
| Risk Modules | **F. Risk Modules** | "What should we analyze?" |
| Upload | **G. Upload** | "Any supporting documents?" |

### 3.2 Section Outline

```
RISKCAST INPUT FORM
│
├── A. ROUTE & SERVICE (Primary, Required)
│   ├── Trade Lane* (dropdown, searchable)
│   ├── Mode of Transport* (dropdown, dependent on trade lane)
│   ├── Shipment Type* (dropdown, dependent on mode)
│   ├── Service Route* (dropdown, searchable, dependent on mode)
│   ├── Carrier (dropdown, dependent on service route)
│   ├── Container Type (dropdown)
│   ├── Priority (pill group: fastest/balanced/cheapest/reliable)
│   ├── Origin Port (POL)* (autosuggest)
│   └── Destination Port (POD)* (autosuggest)
│
├── B. SCHEDULE (Auto-populated, Mostly Readonly)
│   ├── ETD (date picker)
│   ├── Transit Time (readonly, from service route)
│   ├── ETA (readonly, calculated)
│   ├── Schedule Frequency (readonly, from service route)
│   └── Reliability Score (readonly, from service route)
│
├── C. CARGO DETAILS (Required Core + Conditional Advanced)
│   ├── BASIC FIELDS
│   │   ├── Cargo Type* (dropdown)
│   │   ├── HS Code (text, optional)
│   │   ├── Packing Type* (dropdown)
│   │   ├── Gross Weight* (number + unit: kg)
│   │   ├── Net Weight (number + unit: kg)
│   │   ├── Volume (number + unit: m³)
│   │   ├── Number of Packages (number)
│   │   └── Stackability (pill group: yes/no)
│   │
│   ├── ADVANCED FIELDS (collapsed by default)
│   │   ├── Cargo Sensitivity (pill group: standard/fragile/temp/high-value)
│   │   │   └── [IF temperature] Min/Max Temp (number + unit: °C)
│   │   ├── Dangerous Goods (pill group: no/yes)
│   │   │   └── [IF yes] UN Number, DG Class, Packing Group
│   │   ├── Loadability Issues (toggle)
│   │   ├── Cargo Description (textarea)
│   │   └── Special Handling Instructions (textarea)
│
├── D. VALUE & TERMS (Required Insurance + Optional Incoterm)
│   ├── Insurance Value* (number + currency selector: USD)
│   ├── Insurance Coverage (dropdown)
│   ├── Incoterm® 2020 (dropdown)
│   └── Incoterm Location (text)
│
├── E. PARTIES (Tabbed: Seller | Buyer)
│   ├── [SELLER TAB]
│   │   ├── Company Name* (text)
│   │   ├── Country* (dropdown, searchable)
│   │   ├── City (text)
│   │   ├── Address (text)
│   │   ├── Contact Person (text)
│   │   ├── Contact Role (text)
│   │   ├── Email (email)
│   │   ├── Phone (tel)
│   │   ├── Business Type (dropdown)
│   │   └── Tax ID / VAT (text)
│   │
│   └── [BUYER TAB] (same fields as Seller, prefixed "buyer")
│
├── F. RISK MODULES (All Optional, Defaults: All Enabled)
│   ├── ESG Risk (toggle, default: on)
│   ├── Weather & Climate Risk (toggle, default: on)
│   ├── Port Congestion Risk (toggle, default: on)
│   ├── Carrier Performance (toggle, default: on)
│   ├── Market Condition Scanner (toggle, default: on)
│   └── Insurance Optimization (toggle, default: on)
│
└── G. UPLOAD (Optional)
    └── Packing List (file upload: PDF, XLSX, CSV)
        └── [IF uploaded] File preview + "Auto-parse suggestion"

* = Required field
```

### 3.3 Progressive Disclosure Rules

| Mode | Visible Fields | Trigger |
|------|---------------|---------|
| **Basic** (default) | Required fields + most common optional fields (~25 fields) | Default state |
| **Advanced** | All fields (~60 fields) | Toggle in sidebar |
| **Section Advanced** | Per-section "Show more options" | Link within each section |
| **Conditional** | DG fields, Temperature fields | Triggered by sensitivity/DG selection |

**Basic Mode Shows:**
- Route & Service: All fields (core decisions)
- Schedule: All fields (mostly readonly)
- Cargo: Type, Packing, Weights, Volume, Packages, Stackability, Insurance Value
- Value & Terms: Insurance Value, Coverage
- Parties: Company Name, Country only
- Modules: All toggles visible
- Upload: Always visible

**Basic Mode Hides (until "Advanced" or "Show more"):**
- Cargo: Sensitivity, DG, Loadability, Description, Handling
- Value & Terms: Incoterm fields
- Parties: All fields except Company/Country

---

## 4. Component Library Specification

### 4.1 Input Components

#### Text Input

| Property | Specification |
|----------|---------------|
| **Height** | 48px (touch-friendly) |
| **Border** | 1px solid `--color-border-default` |
| **Border Radius** | 12px |
| **Background** | `rgba(255, 255, 255, 0.04)` |
| **Padding** | 0 16px |
| **Font** | `--font-body` (15px/1.5) |
| **Icon** | 20px, left-aligned, `--color-text-muted` |

**States:**

| State | Border | Background | Shadow | Other |
|-------|--------|------------|--------|-------|
| Default | `--color-border-default` | `rgba(255,255,255,0.04)` | none | — |
| Hover | `--color-border-hover` | `rgba(255,255,255,0.06)` | none | — |
| Focus | `--color-primary-neon` | `rgba(255,255,255,0.06)` | `0 0 0 3px rgba(110, 243, 255, 0.15)` | Left accent bar 3px |
| Filled | `--color-border-default` | same | none | Value in `--color-text-strong` |
| Error | `--color-error` | same | `0 0 0 3px rgba(239, 68, 68, 0.15)` | Error message below |
| Disabled | `--color-border-muted` | `rgba(255,255,255,0.02)` | none | Opacity 0.5, cursor not-allowed |
| Readonly | `--color-border-muted` | `--color-bg-tertiary` | none | Lock icon, no cursor change |

**Anatomy:**
```
┌─────────────────────────────────────────────────┐
│ [🔍] [Value text here____________] [Unit/Suffix]│
└─────────────────────────────────────────────────┘
  ↑ Icon   ↑ Input                    ↑ Optional
```

#### Dropdown (Select)

| Property | Specification |
|----------|---------------|
| **Trigger Height** | 48px |
| **Menu Max Height** | 320px |
| **Menu Background** | `--color-bg-glass` + `blur(40px)` |
| **Menu Border** | 1px solid `--color-border-subtle` |
| **Menu Radius** | 16px |
| **Menu Shadow** | `0 16px 48px rgba(0,0,0,0.4)` |
| **Item Height** | 44px |
| **Item Padding** | 12px 16px |
| **Animation** | Fade + scale (200ms ease-out) |

**Searchable Dropdown:**
- Search input pinned at top of menu
- Search input has dedicated focus state
- "No results" empty state with suggestion

**Keyboard Navigation:**
- `↓`/`↑`: Navigate items
- `Enter`: Select item
- `Escape`: Close menu
- `Type`: Jump to matching item

#### Autosuggest (POL/POD)

| Property | Specification |
|----------|---------------|
| **Debounce** | 300ms |
| **Min Characters** | 2 |
| **Max Suggestions** | 8 |
| **Highlight** | `<mark>` with `--color-primary-neon` background |

**States:**
- Typing: Show loading spinner after debounce
- Results: Dropdown menu with highlighted matches
- No Results: "No ports found. Try a different search." message
- Error: "Unable to search. Please try again." with retry

#### Date Input

| Property | Specification |
|----------|---------------|
| **Component** | Custom date picker (not browser default) |
| **Format Display** | DD MMM YYYY (e.g., "15 Jan 2026") |
| **Format Input** | ISO 8601 (YYYY-MM-DD) |
| **Calendar** | Dropdown panel with month/year navigation |
| **Today Highlight** | Ring outline in `--color-primary-neon` |

#### Number Input with Units

| Property | Specification |
|----------|---------------|
| **Layout** | Input + suffix unit label |
| **Suffix Position** | Inside input, right-aligned, non-editable |
| **Suffix Style** | `--color-text-muted`, 13px |
| **Step Buttons** | Hidden (clean interface) |
| **Validation** | Real-time format + range |

**Example:**
```
┌─────────────────────────────────────┐
│ [📦] 20915                       kg │
└─────────────────────────────────────┘
```

#### Pill Group (Radio/Toggle)

| Property | Specification |
|----------|---------------|
| **Container** | Flex wrap, gap 8px |
| **Pill Height** | 40px |
| **Pill Padding** | 0 20px |
| **Pill Radius** | 10px |
| **Pill Border** | 1px solid `--color-border-default` |

**States:**

| State | Background | Border | Text |
|-------|------------|--------|------|
| Default | `rgba(255,255,255,0.04)` | `--color-border-default` | `--color-text-muted` |
| Hover | `rgba(255,255,255,0.08)` | `--color-border-hover` | `--color-text-default` |
| Selected | `linear-gradient(135deg, rgba(110,243,255,0.15), rgba(124,58,237,0.15))` | `--color-primary-neon` | `--color-primary-neon` |

**Keyboard:** Tab to group, Arrow keys to navigate, Space/Enter to select.

#### Toggle Switch

| Property | Specification |
|----------|---------------|
| **Track Width** | 48px |
| **Track Height** | 24px |
| **Track Radius** | 12px |
| **Thumb Size** | 20px |
| **Animation** | 200ms ease-out |

**States:**

| State | Track | Thumb |
|-------|-------|-------|
| Off | `rgba(255,255,255,0.1)` | `--color-text-muted` |
| On | `--color-primary-neon` | `white` |
| Disabled | Opacity 0.4 | — |

#### Textarea

| Property | Specification |
|----------|---------------|
| **Min Height** | 88px (3 lines) |
| **Max Height** | 200px (then scroll) |
| **Resize** | Vertical only |
| **Character Count** | Bottom right, if max-length set |

#### File Upload Zone

| Property | Specification |
|----------|---------------|
| **Min Height** | 160px |
| **Border** | 2px dashed `--color-border-default` |
| **Border Radius** | 16px |
| **Drag Active** | Border solid `--color-primary-neon`, background glow |

**States:**
- Default: Dashed border, icon + "Drag & drop or click to upload"
- Drag Over: Solid neon border, pulsing glow
- Uploading: Progress bar, file name
- Uploaded: File card with preview, remove button
- Error: Error message, retry button

### 4.2 Preview Panel Components

#### Route Summary Card

```
┌─────────────────────────────────────┐
│ ROUTE SUMMARY                       │
│ ─────────────────────────────────── │
│                                     │
│      HCM  ━━━━━━━━━━━━━━━━━━►  SHA  │
│   Ho Chi Minh          Shanghai     │
│                                     │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│ │🚢 Ocean │ │📦 FCL   │ │⏱ 12 days││
│ └─────────┘ └─────────┘ └─────────┘│
│                                     │
│ ONE Alliance • CSCL Saturn          │
│ Reliability: ████████░░ 87%         │
└─────────────────────────────────────┘
```

| Property | Specification |
|----------|---------------|
| **Background** | `--color-bg-card` |
| **Border** | 1px solid `--color-border-subtle` |
| **Radius** | 20px |
| **Padding** | 24px |
| **Port Codes** | `--font-display`, 24px, `--color-text-strong` |
| **Port Names** | `--font-body`, 13px, `--color-text-muted` |
| **Route Line** | SVG with animated dash |

#### Cargo Summary Card

```
┌─────────────────────────────────────┐
│ CARGO SUMMARY                       │
│ ─────────────────────────────────── │
│                                     │
│ 📦 Electronics                      │
│                                     │
│ Weight    Volume     Packages       │
│ 20,915 kg  42.5 m³   120 units     │
│                                     │
│ ┌─────────┐ ┌─────────┐            │
│ │⚠ Fragile│ │🌡 Temp  │            │
│ └─────────┘ └─────────┘            │
│                                     │
│ Insured: $85,000 USD • CIF          │
└─────────────────────────────────────┘
```

#### Completeness Meter

```
┌─────────────────────────────────────┐
│ COMPLETENESS                        │
│ ─────────────────────────────────── │
│                                     │
│ ████████████░░░░░░░░  67%          │
│                                     │
│ 8 of 12 required fields             │
│                                     │
│ ✓ Route selected                    │
│ ✓ Cargo details complete            │
│ ✓ Insurance value set               │
│ ✗ Seller country required           │
│ ✗ Buyer country required            │
│ ✗ POD required                      │
│                                     │
│ [Jump to missing fields]            │
└─────────────────────────────────────┘
```

| Property | Specification |
|----------|---------------|
| **Progress Bar Height** | 8px |
| **Progress Bar Radius** | 4px |
| **Progress Fill** | Gradient from `--color-primary-neon` to `--color-accent-purple` |
| **Checklist Icon ✓** | `--color-success` |
| **Checklist Icon ✗** | `--color-error` |
| **Jump Link** | Text button, underline on hover |

#### "What You'll Get" Card

```
┌─────────────────────────────────────┐
│ WHAT YOU'LL GET                     │
│ ─────────────────────────────────── │
│                                     │
│ After analysis, you'll receive:     │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🎯 Risk Score (0-10)            │ │
│ │    Overall shipment risk rating │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 🗺 Route Analysis               │ │
│ │    Port delays, weather, etc.   │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 💡 Recommendations              │ │
│ │    Actionable risk mitigations  │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 🛡 Insurance Options            │ │
│ │    Optimized coverage plans     │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 4.3 Navigation & Actions

#### Sidebar Navigation

| Property | Specification |
|----------|---------------|
| **Width** | 240px expanded, 64px collapsed |
| **Item Height** | 44px |
| **Item Padding** | 0 16px |
| **Item Radius** | 10px |
| **Active Indicator** | Left border 3px `--color-primary-neon` |

**Section Status Badges:**
- ✓ (green): All required fields complete
- ● (yellow): In progress (partial)
- ○ (default): Not started
- ✗ (red): Has validation errors

#### Sticky CTA Bar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  Progress ████████████░░░░░░░░ 67%     8 of 12 required                     │
│                                                                              │
│  ⌨ Tab to navigate • Enter to submit            [Save Draft] [Run Analysis →]│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Property | Specification |
|----------|---------------|
| **Height** | 80px |
| **Background** | `--color-bg-glass` + `blur(24px)` |
| **Border Top** | 1px solid `--color-border-subtle` |
| **Primary Button** | Gradient, 48px height, disabled until ready |
| **Secondary Button** | Ghost style, 48px height |
| **Progress Bar** | Same as Completeness Meter, inline |

**Primary CTA States:**

| State | Appearance | Behavior |
|-------|------------|----------|
| Disabled | Opacity 0.5, no pointer | Required fields incomplete |
| Enabled | Full opacity, cursor pointer | All required fields complete |
| Hover | Glow effect, slight lift | — |
| Loading | Spinner, "Analyzing..." text | After click, during submission |

---

## 5. Interaction Model

### 5.1 Autosave

| Behavior | Specification |
|----------|---------------|
| **Trigger** | Any field change |
| **Debounce** | 1000ms after last change |
| **Scope** | Entire form state |
| **Storage** | Session (server-side) + localStorage (fallback) |
| **Indicator** | "Draft saved • 2m ago" in sidebar |
| **Recovery** | On page load, prompt "Continue where you left off?" |

**Autosave Flow:**
1. User changes field
2. Debounce timer starts (1s)
3. If no more changes, save triggers
4. Show "Saving..." indicator briefly
5. Update to "Draft saved • just now"
6. Timestamp updates every minute

### 5.2 Validation

#### Validation Timing

| Type | Trigger | Fields |
|------|---------|--------|
| **On Blur** | Field loses focus | All fields |
| **On Change** | Value changes | Required fields, format-sensitive |
| **On Submit** | Form submission | All fields |

#### Validation Rules

| Field Type | Validation |
|------------|------------|
| Required Text | Non-empty after trim |
| Email | Valid email format |
| Phone | Valid phone format (international) |
| Number | Non-negative, within range |
| Date | Valid date, ETD ≥ today |
| Dropdown | Selection made (not default) |
| Autosuggest | Selection from suggestions |

#### Error Display

**Field-Level:**
```
┌─────────────────────────────────────┐
│ [🏢] Company Name *                 │
│ ┌─────────────────────────────────┐ │
│ │ [Empty field with red border]   │ │
│ └─────────────────────────────────┘ │
│ ⚠ Company name is required          │
└─────────────────────────────────────┘
```

**Form-Level (on submit):**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠ Please fix the following before continuing:              │
│                                                             │
│ • Seller country is required                    [Jump →]    │
│ • Buyer country is required                     [Jump →]    │
│ • ETD cannot be in the past                     [Jump →]    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Keyboard Navigation

| Key | Behavior |
|-----|----------|
| `Tab` | Move to next focusable element |
| `Shift + Tab` | Move to previous focusable element |
| `Enter` | Submit form (from CTA focus) or select dropdown item |
| `Escape` | Close dropdown/modal, cancel current action |
| `↓` / `↑` | Navigate dropdown items, pill group options |
| `Space` | Toggle checkbox/switch, select pill option |
| `Ctrl + S` | Save draft (with feedback toast) |

### 5.4 State Flows

#### Empty/Default State

**Smart Defaults Applied:**
- Mode: Ocean
- Priority: Balanced
- Stackability: Yes
- Dangerous Goods: No
- All Risk Modules: Enabled

**Guided Tips (first-time users):**
- Tooltip on Trade Lane: "Start here. Your trade route determines available options."
- Pulsing highlight on first required field

#### Loading States

| Component | Loading Indicator |
|-----------|-------------------|
| Dropdown (dependent) | Skeleton items + spinner |
| Autosuggest | Inline spinner after debounce |
| File Upload | Progress bar with percentage |
| Form Submit | Button spinner + "Analyzing..." + form disabled |

#### Success State (Form Submit)

1. Button shows "Analyzing..." with spinner
2. Form becomes read-only (subtle overlay)
3. Progress message: "Running risk analysis..."
4. On complete: Smooth transition/redirect to Summary page
5. No jarring page refresh—use page transition animation

#### Error State (Server Error)

```
┌─────────────────────────────────────────────────────────────┐
│ ❌ Unable to submit analysis                                │
│                                                             │
│ Something went wrong on our end. Your draft is safe.        │
│                                                             │
│ [Try Again]                          [Contact Support]      │
└─────────────────────────────────────────────────────────────┘
```

- Toast notification appears
- Form remains editable
- Draft preserved
- Retry button available

### 5.5 Warnings & Anomalies

The Preview Panel shows real-time warnings for data anomalies:

| Warning | Condition | Message |
|---------|-----------|---------|
| Past ETD | ETD < today | "⚠ ETD is in the past" |
| Zero Value | Insurance Value = 0 | "⚠ Insurance value is $0" |
| Mode Mismatch | Ocean mode + no container | "⚠ Container type recommended for ocean" |
| High Value Uninsured | Value > $50k, no coverage | "⚠ Consider insurance coverage" |
| Missing Country | Seller/Buyer country empty | "⚠ Country required for compliance" |

---

## 6. Microcopy & Tone Guide

### 6.1 Tone Principles

| Principle | Description | Example |
|-----------|-------------|---------|
| **Professional** | Enterprise-appropriate, no slang | ✓ "Select your trade route" ✗ "Pick your lane" |
| **Concise** | Minimal words, maximum clarity | ✓ "Origin port" ✗ "Please enter the port of loading" |
| **Helpful** | Anticipate confusion, offer guidance | ✓ "e.g., LAX, SGN, SHA" |
| **Confident** | Affirm user actions, no hedging | ✓ "Draft saved" ✗ "Draft might be saved" |
| **Human** | Natural, not robotic | ✓ "Something went wrong" ✗ "Error 500" |

### 6.2 Label Conventions

| Type | Format | Example |
|------|--------|---------|
| **Field Label** | Sentence case, no period | "Trade lane", "Gross weight" |
| **Required Indicator** | Asterisk after label | "Company name *" |
| **Unit Labels** | Parenthetical or suffix | "Gross weight (kg)" or inline "kg" |
| **Placeholder** | Sentence case, action or example | "Select trade lane" or "e.g., Shanghai" |

### 6.3 Helper Text

| Use Case | Format | Example |
|----------|--------|---------|
| **Format Hint** | "Format: X" | "Format: DD MMM YYYY" |
| **Example** | "e.g., X, Y, Z" | "e.g., LAX, SGN, SHA" |
| **Explanation** | Full sentence | "Total weight including packaging" |
| **Tooltip** | Concise definition | "POL: Port of Loading—where cargo is loaded onto vessel" |

### 6.4 Validation Messages

| Type | Format | Example |
|------|--------|---------|
| **Required** | "X is required" | "Trade lane is required" |
| **Format** | "Enter a valid X" | "Enter a valid email address" |
| **Range** | "X must be between Y and Z" | "Volume must be between 0 and 10,000" |
| **Dependency** | "Select X first" | "Select trade lane first" |
| **Past Date** | "X cannot be in the past" | "ETD cannot be in the past" |

### 6.5 Action Microcopy

| Element | Text |
|---------|------|
| **Primary CTA** | "Run Analysis" or "Run Risk Analysis" |
| **Secondary CTA** | "Save Draft" |
| **Cancel** | "Discard Draft" (with confirmation) |
| **Progress** | "8 of 12 required" |
| **Loading** | "Analyzing..." |
| **Success** | "Analysis complete. Redirecting..." |
| **Error** | "Unable to submit. Please try again." |
| **Autosave** | "Draft saved • 2m ago" |
| **Keyboard Hint** | "⌨ Tab to navigate • Enter to submit" |

### 6.6 Empty States

| Location | Message |
|----------|---------|
| **Preview (no route)** | "Select a route to see summary" |
| **Preview (no cargo)** | "Add cargo details to see summary" |
| **Completeness (0%)** | "Start by selecting your trade route" |
| **Upload** | "Drag & drop your packing list or click to browse" |
| **Search No Results** | "No results for 'X'. Try a different search." |

---

## 7. Figma Blueprint

### 7.1 Frame Sizes

| Frame | Dimensions | Grid |
|-------|------------|------|
| **Desktop 1440** | 1440 × 1024 | 12-col, 24px gutter |
| **Desktop 1280** | 1280 × 900 | 12-col, 24px gutter |
| **Tablet 768** | 768 × 1024 | 8-col, 16px gutter |
| **Mobile 375** | 375 × 812 | 4-col, 16px gutter |

### 7.2 Grid System

**Desktop (1440px viewport):**
```
│ 32px │ 12 columns × 93px │ 11 gutters × 24px │ 32px │
│margin│                                       │margin│
```

| Property | Value |
|----------|-------|
| Columns | 12 |
| Column Width | ~93px (at 1440px) |
| Gutter | 24px |
| Margin | 32px |
| Content Width | 1376px max |

### 7.3 Spacing Scale

| Token | Value | Use Case |
|-------|-------|----------|
| `--space-2` | 2px | Hairline gaps |
| `--space-4` | 4px | Tight spacing, icon gaps |
| `--space-8` | 8px | Inline elements, pill gaps |
| `--space-12` | 12px | Small component padding |
| `--space-16` | 16px | Standard component padding |
| `--space-24` | 24px | Card padding, section gaps |
| `--space-32` | 32px | Large gaps, section separators |
| `--space-40` | 40px | Major section spacing |
| `--space-48` | 48px | Page-level spacing |
| `--space-64` | 64px | Hero/major dividers |

### 7.4 Typography Scale

| Token | Size/Line-Height | Weight | Use Case |
|-------|------------------|--------|----------|
| `--font-display-lg` | 32px / 1.15 | 700 | Page title |
| `--font-display-md` | 24px / 1.2 | 700 | Section title |
| `--font-display-sm` | 20px / 1.25 | 600 | Subsection title |
| `--font-body-lg` | 16px / 1.55 | 400 | Body text |
| `--font-body-md` | 15px / 1.5 | 400 | Default body |
| `--font-body-sm` | 14px / 1.45 | 400 | Secondary text |
| `--font-label` | 13px / 1.3 | 600 | Field labels |
| `--font-caption` | 12px / 1.4 | 400 | Helper text, hints |
| `--font-code` | 14px / 1.5 | 400 mono | Code, port codes |

**Font Families:**
- Display: `'Orbitron', 'SF Pro Display', monospace`
- Body: `'Inter', 'SF Pro Text', -apple-system, sans-serif`
- Mono: `'JetBrains Mono', 'SF Mono', monospace`

### 7.5 Color Tokens

#### Background Colors

| Token | Light Mode | Dark Mode | Use |
|-------|------------|-----------|-----|
| `--color-bg-page` | `#f7f9fc` | `#0a0e1a` | Page background |
| `--color-bg-surface` | `#ffffff` | `#111827` | Card background |
| `--color-bg-glass` | `rgba(255,255,255,0.7)` | `rgba(17,24,39,0.6)` | Glass surfaces |
| `--color-bg-input` | `rgba(0,0,0,0.02)` | `rgba(255,255,255,0.04)` | Input background |
| `--color-bg-overlay` | `rgba(0,0,0,0.5)` | `rgba(0,0,0,0.7)` | Modal overlays |

#### Text Colors

| Token | Light Mode | Dark Mode | Use |
|-------|------------|-----------|-----|
| `--color-text-strong` | `#111827` | `#f9fafb` | Headings, important |
| `--color-text-default` | `#374151` | `#e5e7eb` | Body text |
| `--color-text-muted` | `#6b7280` | `#9ca3af` | Secondary text |
| `--color-text-placeholder` | `#9ca3af` | `#6b7280` | Placeholders |

#### Accent Colors

| Token | Value | Use |
|-------|-------|-----|
| `--color-primary-neon` | `#6ef3ff` | Primary actions, focus |
| `--color-accent-purple` | `#8b5cf6` | Secondary accent, gradients |
| `--color-success` | `#10b981` | Success states, checkmarks |
| `--color-warning` | `#f59e0b` | Warnings |
| `--color-error` | `#ef4444` | Errors, required |

#### Border Colors

| Token | Light Mode | Dark Mode | Use |
|-------|------------|-----------|-----|
| `--color-border-default` | `rgba(0,0,0,0.08)` | `rgba(255,255,255,0.08)` | Default borders |
| `--color-border-hover` | `rgba(0,0,0,0.15)` | `rgba(255,255,255,0.15)` | Hover state |
| `--color-border-subtle` | `rgba(0,0,0,0.04)` | `rgba(255,255,255,0.04)` | Subtle dividers |

### 7.6 Effects & Elevation

| Token | Value | Use |
|-------|-------|-----|
| `--blur-glass` | `blur(40px)` | Glass surfaces |
| `--blur-dropdown` | `blur(24px)` | Dropdown menus |
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.1)` | Cards |
| `--shadow-lg` | `0 8px 24px rgba(0,0,0,0.15)` | Dropdowns |
| `--shadow-xl` | `0 16px 48px rgba(0,0,0,0.25)` | Modals |
| `--shadow-glow` | `0 0 24px rgba(110,243,255,0.3)` | CTA glow |

### 7.7 Border Radius

| Token | Value | Use |
|-------|-------|-----|
| `--radius-sm` | 6px | Small elements |
| `--radius-md` | 10px | Buttons, pills |
| `--radius-lg` | 12px | Inputs, small cards |
| `--radius-xl` | 16px | Dropdowns |
| `--radius-2xl` | 20px | Cards |
| `--radius-3xl` | 24px | Large cards, sections |
| `--radius-full` | 9999px | Circular elements |

### 7.8 Animation Tokens

| Token | Value | Use |
|-------|-------|-----|
| `--duration-fast` | 100ms | Micro-interactions |
| `--duration-normal` | 200ms | Standard transitions |
| `--duration-slow` | 300ms | Complex animations |
| `--ease-out` | `cubic-bezier(0.33, 1, 0.68, 1)` | Exit animations |
| `--ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | Smooth transitions |
| `--ease-bounce` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful feedback |

---

## 8. Design Variants (A/B)

### 8.1 Variant A: Split View (Recommended)

**Described throughout this document.**

```
┌────────────┬─────────────────────────────┬──────────────────┐
│  SIDEBAR   │      FORM PANEL (8 col)     │  PREVIEW (4 col) │
│  (240px)   │      Scrollable             │  Sticky          │
│            │                             │                  │
│  Navigation│      Sections               │  Summary Cards   │
│  Mode Toggle│     Fields                  │  Completeness    │
│  Draft Info│                             │  What You'll Get │
└────────────┴─────────────────────────────┴──────────────────┘
                    STICKY CTA BAR
```

**Pros:**
- ✅ Immediate feedback—preview updates as you type
- ✅ All information visible at once
- ✅ Efficient for power users who know what to enter
- ✅ Reduces back-and-forth navigation
- ✅ Clear completion progress always visible

**Cons:**
- ❌ More visual complexity
- ❌ May feel dense for first-time users
- ❌ Preview panel takes space even when not needed

**Best For:**
- Returning users
- Power users entering multiple shipments
- Users who value efficiency over guidance
- Desktop-primary workflows

### 8.2 Variant B: Stepper Wizard

**Multi-step flow with one section per step.**

```
Step 1: Route & Service
────────────────────────────────────────────────

[1] Route ──── [2] Schedule ──── [3] Cargo ──── [4] Value ──── [5] Parties ──── [6] Review
 ●              ○                 ○              ○              ○               ○

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ROUTE & SERVICE                                                           │
│                                                                              │
│   Where is your shipment going?                                             │
│                                                                              │
│   ┌─────────────────────────────┐    ┌─────────────────────────────┐        │
│   │ Trade Lane *                │    │ Mode of Transport *         │        │
│   │ [Select ▾]                  │    │ [Select ▾]                  │        │
│   └─────────────────────────────┘    └─────────────────────────────┘        │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │ Service Route *                                                 │       │
│   │ [Select ▾]                                                      │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   ┌─────────────────────────────┐    ┌─────────────────────────────┐        │
│   │ Origin Port (POL) *         │    │ Destination Port (POD) *    │        │
│   │ [Type to search ⌕]          │    │ [Type to search ⌕]          │        │
│   └─────────────────────────────┘    └─────────────────────────────┘        │
│                                                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

                                        [Back]  [Continue to Schedule →]
```

**Step Structure:**
1. **Route & Service** (Required) — Trade lane, mode, route, POL/POD, carrier
2. **Schedule** (Auto-filled) — ETD, transit, ETA
3. **Cargo Details** (Required) — Type, weight, volume, sensitivity
4. **Value & Terms** (Required) — Insurance, Incoterm
5. **Parties** (Required) — Seller, Buyer
6. **Review & Submit** — Summary of all entries, edit links, submit

**Final Review Step:**
```
Step 6: Review & Submit
────────────────────────────────────────────────

[1] Route ──── [2] Schedule ──── [3] Cargo ──── [4] Value ──── [5] Parties ──── [6] Review
 ✓              ✓                 ✓              ✓              ✓               ●

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   REVIEW YOUR SHIPMENT                                                      │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │ ROUTE SUMMARY                                           [Edit]  │       │
│   │ HCM → SHA • Ocean FCL • ONE Alliance • 12 days transit          │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │ CARGO SUMMARY                                           [Edit]  │       │
│   │ Electronics • 20,915 kg • 42.5 m³ • Fragile                     │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │ VALUE & TERMS                                           [Edit]  │       │
│   │ $85,000 USD insured • CIF Shanghai                              │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │ PARTIES                                                 [Edit]  │       │
│   │ Seller: ACME Corp (Vietnam) → Buyer: TechCo Ltd (China)         │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │ RISK MODULES (6 selected)                               [Edit]  │       │
│   │ ESG, Weather, Port Congestion, Carrier, Market, Insurance       │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   You'll receive: Risk Score • Route Analysis • Recommendations             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

                                        [Back]  [Run Risk Analysis →]
```

**Pros:**
- ✅ Lower cognitive load—one decision at a time
- ✅ Clear progress through numbered steps
- ✅ Better for first-time users or infrequent users
- ✅ Mobile-friendly by default
- ✅ Each step can have focused validation
- ✅ Review step ensures data accuracy

**Cons:**
- ❌ More clicks to complete
- ❌ Harder to jump between sections
- ❌ Less efficient for power users
- ❌ No live preview until final review
- ❌ May feel slower for repetitive data entry

**Best For:**
- First-time users
- Mobile-primary workflows
- Complex conditional flows (DG handling)
- When data accuracy is critical
- Onboarding scenarios

### 8.3 Variant Selection Matrix

| Scenario | Recommended Variant |
|----------|---------------------|
| Desktop power users entering 5+ shipments/day | **Variant A: Split View** |
| Mobile users on the go | **Variant B: Stepper** |
| First-time users (onboarding) | **Variant B: Stepper** |
| Users who value speed | **Variant A: Split View** |
| High-stakes shipments (accuracy critical) | **Variant B: Stepper** |
| Complex conditional fields (DG, temperature) | **Variant B: Stepper** |

### 8.4 Hybrid Approach (Future Consideration)

A future iteration could offer **user preference:**
- Default: Stepper for new users, Split View for returning users
- Toggle: "Switch to [Quick Entry / Guided Mode]"
- Remember preference per user

---

## 9. Data Ownership & Trust Signals

### 9.1 Why This Matters

Enterprise users handling sensitive logistics data need explicit assurance about:
- **Where their data lives** before submission
- **Who can access it** and when
- **Reproducibility** of analysis results
- **Auditability** for compliance requirements

This section defines UI elements that communicate trust without cluttering the interface.

### 9.2 Data Handling Indicator (Sidebar)

**Location:** Bottom of sidebar, above "Discard Draft" button

```
┌─────────────────────────────────────┐
│ 🔒 DATA HANDLING                    │
│ ─────────────────────────────────── │
│                                     │
│ ● Autosaved locally                 │
│   Your browser stores this draft   │
│                                     │
│ ● Not shared until you submit       │
│   Data stays private until "Run"    │
│                                     │
│ ● Editable anytime                  │
│   Modify inputs before analysis     │
│                                     │
│ [Learn more →]                      │
└─────────────────────────────────────┘
```

| Property | Specification |
|----------|---------------|
| **Container** | Subtle card, `--color-bg-input` background |
| **Border** | 1px solid `--color-border-subtle` |
| **Radius** | 12px |
| **Padding** | 16px |
| **Icon** | 🔒 or `Lock` icon from Lucide |
| **Title** | `--font-label`, `--color-text-muted` |
| **Items** | `--font-caption`, `--color-text-muted` |
| **Bullet** | Filled circle, `--color-success` |

**States:**
- Default: Static display (always visible)
- Expanded: "Learn more" opens modal with full privacy policy

### 9.3 Trust Signals (Header Badge)

**Location:** Header, next to Case ID

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Logo] [Case ID: RC-2026-0142 • Draft saved 2m ago] [🔒 Secure] [?] [👤]    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Badge Variants:**

| Badge | Condition | Tooltip |
|-------|-----------|---------|
| `🔒 Secure` | Default (draft mode) | "Your data is stored locally and encrypted" |
| `📤 Submitted` | After submission | "Analysis submitted at [timestamp]" |
| `🔄 Versioned` | If editing previous | "Version 2 of 3 • View history" |

### 9.4 Analysis Reproducibility Card (Preview Panel)

**Location:** Bottom of Preview Panel, after "What You'll Get"

```
┌─────────────────────────────────────┐
│ 🔬 ANALYSIS INTEGRITY               │
│ ─────────────────────────────────── │
│                                     │
│ ✓ Reproducible                      │
│   Same inputs = same results        │
│                                     │
│ ✓ Inputs versioned                  │
│   Full edit history preserved       │
│                                     │
│ ✓ Audit-ready                       │
│   Exportable analysis log           │
│                                     │
│ ─────────────────────────────────── │
│ Analysis ID will be assigned        │
│ upon submission                     │
└─────────────────────────────────────┘
```

| Property | Specification |
|----------|---------------|
| **Visibility** | Show only when completeness ≥ 50% |
| **Style** | Matches other preview cards |
| **Checkmarks** | `--color-success` |
| **Footer Note** | `--font-caption`, `--color-text-muted` |

### 9.5 Post-Submission Confirmation

After successful submission, show brief confirmation before redirect:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                          ✓ Analysis Submitted                               │
│                                                                              │
│                      Analysis ID: RC-2026-0142-A1                           │
│                      Submitted: 15 Jan 2026, 14:32 UTC                      │
│                                                                              │
│                      ┌─────────────────────────────────┐                    │
│                      │ 📋 Input snapshot saved         │                    │
│                      │ 🔄 Results reproducible         │                    │
│                      │ 📧 Confirmation sent to email   │                    │
│                      └─────────────────────────────────┘                    │
│                                                                              │
│                      Redirecting to results in 3s...                        │
│                      [View Results Now →]                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Field Provenance System

### 10.1 Provenance Philosophy

In complex logistics workflows, data comes from multiple sources:
- **User-typed** values
- **Inferred** from other fields (e.g., ETA from ETD + transit time)
- **Parsed** from uploaded documents (packing list)
- **Default** values (system-provided)
- **Fetched** from external APIs (carrier data)

Explicit provenance reduces errors and builds confidence.

### 10.2 Provenance Badges

**Badge Types:**

| Badge | Icon | Label | Color | Use Case |
|-------|------|-------|-------|----------|
| User-provided | `👤` | "You entered" | `--color-text-muted` | Manual user input |
| Inferred | `🧠` | "Calculated" | `--color-accent-purple` | Derived from other fields |
| Parsed | `📄` | "From document" | `--color-primary-neon` | Extracted from upload |
| Default | `⚙️` | "Default" | `--color-text-placeholder` | System default |
| Fetched | `🌐` | "From carrier" | `--color-success` | External API data |

### 10.3 Badge Placement

**Option A: Inline Badge (Recommended for key fields)**

```
┌─────────────────────────────────────────────────────────────┐
│ ETA (Estimated Arrival)                          🧠 Calculated │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 27 Jan 2026                                             │ │
│ └─────────────────────────────────────────────────────────┘ │
│ Calculated from ETD + transit time                          │
└─────────────────────────────────────────────────────────────┘
```

**Option B: Hover Tooltip (For all fields)**

```
┌─────────────────────────────────────────────────────────────┐
│ Gross Weight (kg) *                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 20,915                                            kg [i]│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│   ┌─────────────────────────────────┐                       │
│   │ 📄 Source: Packing list upload  │  ← Tooltip on [i]    │
│   │    Parsed from: packinglist.xlsx│                       │
│   │    Row 47, Column D             │                       │
│   │    [View source →]              │                       │
│   └─────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### 10.4 Provenance in Preview Panel

**Enhanced Route Summary with Provenance:**

```
┌─────────────────────────────────────┐
│ ROUTE SUMMARY                       │
│ ─────────────────────────────────── │
│                                     │
│      HCM  ━━━━━━━━━━━━━━━━━━►  SHA  │
│   👤 You       →        👤 You      │
│                                     │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│ │🚢 Ocean │ │📦 FCL   │ │⏱ 12 days││
│ │  👤     │ │  👤     │ │  🌐     ││
│ └─────────┘ └─────────┘ └─────────┘│
│                                     │
│ ONE Alliance • CSCL Saturn          │
│ 🌐 From carrier database            │
└─────────────────────────────────────┘
```

### 10.5 Provenance Conflict Resolution

When parsed data conflicts with user input:

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠ Conflict Detected                                         │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ Gross Weight                                                │
│                                                             │
│ ┌─────────────────────┐    ┌─────────────────────┐         │
│ │ 📄 From document    │ vs │ 👤 You entered      │         │
│ │    20,915 kg        │    │    21,000 kg        │         │
│ └─────────────────────┘    └─────────────────────┘         │
│                                                             │
│ [Use document value] [Keep my value] [Edit manually]        │
└─────────────────────────────────────────────────────────────┘
```

### 10.6 Provenance Export (Appendix Feature)

For compliance/audit, users can export provenance log:

| Field | Value | Source | Timestamp | User |
|-------|-------|--------|-----------|------|
| Trade Lane | Asia-Europe | User-provided | 2026-01-15 14:22 | john@acme.com |
| Gross Weight | 20,915 kg | Parsed (packinglist.xlsx) | 2026-01-15 14:25 | system |
| ETA | 27 Jan 2026 | Calculated | 2026-01-15 14:23 | system |

**Export Format:** CSV, JSON, or PDF audit report

---

## 11. Preview Panel Performance

### 11.1 Performance Philosophy

The Live Preview Panel must feel instantaneous without causing UI lag. This requires careful optimization at both design and implementation levels.

### 11.2 Update Strategy

| Update Type | Debounce | Approach |
|-------------|----------|----------|
| **Text input** (typing) | 150ms | Debounce, then update |
| **Dropdown selection** | 0ms | Immediate update |
| **Pill selection** | 0ms | Immediate update |
| **Calculation** (ETA, etc.) | 100ms | Debounce after dependency change |
| **Completeness meter** | 200ms | Debounce, batch field checks |

### 11.3 Loading States for Derived Fields

**Skeleton State (while calculating):**

```
┌─────────────────────────────────────┐
│ ROUTE SUMMARY                       │
│ ─────────────────────────────────── │
│                                     │
│      HCM  ━━━━━━━━━━━━━━━━━━►  SHA  │
│   Ho Chi Minh          Shanghai     │
│                                     │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│ │🚢 Ocean │ │📦 FCL   │ │░░░░░░░░ ││  ← Skeleton
│ └─────────┘ └─────────┘ └─────────┘│
│                                     │
│ ░░░░░░░░░░░░░░░░░░░░░░░░           │  ← Skeleton
│ Reliability: ░░░░░░░░░░░            │  ← Skeleton
└─────────────────────────────────────┘
```

**Skeleton Specifications:**

| Property | Value |
|----------|-------|
| Background | `linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%)` |
| Animation | `shimmer 1.5s ease-in-out infinite` |
| Border Radius | Match content (text: 4px, badge: 8px) |
| Min Width | 60px (text), 80px (badge) |

### 11.4 Memoization Strategy

**What to Memoize:**

| Computation | Memoization Key | Cache Duration |
|-------------|-----------------|----------------|
| Route summary string | `${pol}_${pod}_${mode}` | Until input changes |
| Completeness percentage | `fieldValuesHash` | 200ms TTL |
| ETA calculation | `${etd}_${transitDays}` | Until input changes |
| Cargo summary | `${type}_${weight}_${volume}` | Until input changes |
| Validation state | `fieldValuesHash` | 100ms TTL |

**Implementation Pattern:**

```javascript
// Pseudo-code for memoized preview
const routeSummary = useMemo(() => {
  return computeRouteSummary(pol, pod, mode, carrier);
}, [pol, pod, mode, carrier]);

const completeness = useMemo(() => {
  return computeCompleteness(formState);
}, [debouncedFormState]); // Note: debounced input
```

### 11.5 Progressive Enhancement

**Phase 1: Immediate (0ms)**
- Update changed field indicator
- Update section status badge
- Show typing indicator in preview

**Phase 2: Fast (100ms debounce)**
- Update completeness percentage
- Update simple derived values (ETA)
- Validate current field

**Phase 3: Batched (200ms debounce)**
- Full preview card re-render
- Cross-field validation
- Warning/anomaly detection

### 11.6 Visual Feedback for Updates

**Subtle Pulse Animation:**

When a preview value updates, apply brief highlight:

```css
@keyframes preview-update {
  0% { background-color: rgba(110, 243, 255, 0); }
  20% { background-color: rgba(110, 243, 255, 0.1); }
  100% { background-color: rgba(110, 243, 255, 0); }
}

.preview-value-updated {
  animation: preview-update 600ms ease-out;
}
```

| Property | Value |
|----------|-------|
| Duration | 600ms |
| Easing | ease-out |
| Highlight Color | `rgba(110, 243, 255, 0.1)` (neon tint) |
| Trigger | Value change after debounce |

### 11.7 Error Boundary

If preview calculation fails, show graceful fallback:

```
┌─────────────────────────────────────┐
│ ROUTE SUMMARY                       │
│ ─────────────────────────────────── │
│                                     │
│ ⚠️ Preview temporarily unavailable  │
│                                     │
│ Your inputs are saved. Preview will │
│ restore automatically.              │
│                                     │
│ [Refresh Preview]                   │
└─────────────────────────────────────┘
```

### 11.8 Designer Guidelines

> **For Figma/Design Handoff:**
> 
> 1. **Do NOT design preview as "real-time"** — there's always 100-200ms delay
> 2. **Always include skeleton states** for derived fields
> 3. **Design the "stale" state** — preview showing old value while typing
> 4. **Show update animation** in prototypes to set expectations
> 5. **Performance budget:** Preview update should feel < 100ms perceived

---

## Appendix A: Implementation Notes

### A.1 Token Migration Checklist

| Current (input_v20.css) | New (tokens.css) | Status |
|-------------------------|------------------|--------|
| `--rc-neon-primary: #00ffcc` | `--color-primary-neon: #6ef3ff` | ⬜ Migrate |
| `--rc-bg-primary: #0a0e1a` | `--color-bg-page` | ⬜ Migrate |
| `--rc-text-primary: #f9fafb` | `--color-text-strong` | ⬜ Migrate |
| `--rc-spacing-md: 1rem` | `--space-16` | ⬜ Migrate |
| `--rc-font-display` | `--font-display-md` | ⬜ Migrate |
| `--rc-font-body` | `--font-body-md` | ⬜ Migrate |

### A.2 Accessibility Checklist

| Requirement | Status |
|-------------|--------|
| All form fields have associated `<label>` elements | ⬜ |
| Required fields marked with `aria-required="true"` | ⬜ |
| Error messages connected via `aria-describedby` | ⬜ |
| Dropdowns use `aria-expanded`, `aria-haspopup` | ⬜ |
| Focus order follows visual order | ⬜ |
| Focus ring visible (WCAG AA contrast) | ⬜ |
| Color is not the only indicator (icons + text) | ⬜ |
| Touch targets ≥ 44px | ⬜ |
| `aria-live="polite"` for dynamic content | ⬜ |

### A.3 Performance Considerations

| Concern | Mitigation |
|---------|------------|
| Large dropdown datasets | Virtual scrolling for 100+ items |
| Autosuggest API calls | 300ms debounce, cancel inflight |
| Live preview updates | Debounced re-renders (100ms) |
| Form state management | Efficient diffing, memoization |
| Initial load | Lazy load non-critical sections |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **POL** | Port of Loading—where cargo is loaded onto vessel |
| **POD** | Port of Discharge—where cargo is unloaded from vessel |
| **ETD** | Estimated Time of Departure |
| **ETA** | Estimated Time of Arrival |
| **FCL** | Full Container Load |
| **LCL** | Less than Container Load |
| **DG** | Dangerous Goods |
| **HS Code** | Harmonized System Code—international commodity classification |
| **Incoterm** | International Commercial Terms—delivery responsibility |
| **CIF** | Cost, Insurance, Freight (Incoterm) |
| **ESG** | Environmental, Social, Governance (risk factors) |

---

**Document Version:** 1.1  
**Last Updated:** January 2026  
**Changelog:**
- v1.1: Added Data Ownership & Trust Signals, Field Provenance System, Preview Panel Performance
- v1.0: Initial specification

**Next Review:** After A/B testing results

---

*End of Design Specification*
