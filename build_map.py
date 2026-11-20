#!/usr/bin/env python3
"""
Santiago House Hunter — Interactive Map & Explorer Generator
Reads data/listings.json and builds a self-contained interactive HTML map & property explorer
at output/map.html (works offline and inside sandboxed iframes).
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LISTINGS_PATH = BASE_DIR / "data" / "listings.json"
OUTPUT_HTML_PATH = BASE_DIR / "output" / "map.html"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Santiago House Hunter — La Dehesa &amp; Alto Las Condes</title>
  <style>
    :root {
      --bg: #0c1118;
      --surface: #131a24;
      --surface-hover: #192230;
      --surface-active: #1d2838;
      --border: rgba(226, 232, 240, 0.10);
      --border-strong: rgba(226, 232, 240, 0.18);
      --text: #edf2f7;
      --text-secondary: #a0aec0;
      --text-muted: #8b9bb0;
      --accent: #2563eb;
      --accent-soft: rgba(59, 130, 246, 0.16);
      --accent-text: #7db1ff;
      --pool: #22d3ee;
      --pool-soft: rgba(34, 211, 238, 0.14);
      --shortlist: #f5b942;
      --shortlist-soft: rgba(245, 185, 66, 0.15);
      --visited: #34d399;
      --visited-soft: rgba(52, 211, 153, 0.14);
      --dismissed: #f87171;
      --dismissed-soft: rgba(248, 113, 113, 0.14);
      --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.28);
      --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.36);
      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 12px;
      --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
      color-scheme: dark;
    }

    html.light {
      --bg: #f4f6f8;
      --surface: #ffffff;
      --surface-hover: #f8fafc;
      --surface-active: #eef4ff;
      --border: rgba(15, 23, 42, 0.10);
      --border-strong: rgba(15, 23, 42, 0.18);
      --text: #0f172a;
      --text-secondary: #334155;
      --text-muted: #526075;
      --accent: #2563eb;
      --accent-soft: rgba(37, 99, 235, 0.10);
      --accent-text: #1d4ed8;
      --pool: #0891b2;
      --pool-soft: rgba(8, 145, 178, 0.10);
      --shortlist: #b45309;
      --shortlist-soft: rgba(217, 119, 6, 0.12);
      --visited: #047857;
      --visited-soft: rgba(4, 120, 87, 0.10);
      --dismissed: #be123c;
      --dismissed-soft: rgba(190, 18, 60, 0.10);
      --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
      --shadow-md: 0 8px 24px rgba(15, 23, 42, 0.10);
      color-scheme: light;
    }

    *, *::before, *::after { box-sizing: border-box; }

    ::selection {
      background: var(--accent-soft);
      color: var(--text);
    }

    body {
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
      line-height: 1.45;
      -webkit-font-smoothing: antialiased;
      caret-color: var(--accent);
    }

    a {
      color: var(--accent-text);
      text-underline-offset: 3px;
    }

    button, input, select {
      font: inherit;
      color: inherit;
    }

    button:focus-visible,
    a:focus-visible,
    input:focus-visible,
    select:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }

    .tabular-nums { font-variant-numeric: tabular-nums; }

    /* Custom scrollbars */
    * {
      scrollbar-width: thin;
      scrollbar-color: var(--border-strong) transparent;
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 999px; }

    /* App Shell */
    .app-shell {
      max-width: 1440px;
      margin: 0 auto;
      padding: 16px 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    /* Header */
    .app-header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px 20px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border);
    }

    .brand-group {
      display: flex;
      flex-direction: column;
      gap: 3px;
    }

    .brand-title-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }

    .brand-title {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 650;
      letter-spacing: -0.02em;
      line-height: 1.2;
    }

    .brand-badge {
      font-size: 0.75rem;
      font-weight: 500;
      padding: 2px 9px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-text);
      white-space: nowrap;
    }

    .brand-subtitle {
      margin: 0;
      font-size: 0.8125rem;
      color: var(--text-muted);
    }

    /* KPI Strip (flat inline stats separated by hairlines) */
    .header-actions {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 14px;
    }

    .kpi-strip {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 14px;
      font-size: 0.8125rem;
    }

    .kpi-item {
      display: flex;
      align-items: baseline;
      gap: 6px;
    }

    .kpi-item + .kpi-item {
      padding-left: 14px;
      border-left: 1px solid var(--border);
    }

    .kpi-label { color: var(--text-muted); }
    .kpi-val { font-weight: 600; font-size: 0.9375rem; }
    .kpi-val.pool { color: var(--pool); }
    .kpi-val.shortlist { color: var(--shortlist); }

    .btn-ghost {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 36px;
      padding: 0 12px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-strong);
      background: transparent;
      color: var(--text);
      font-size: 0.8125rem;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 140ms var(--ease-out), border-color 140ms var(--ease-out);
    }
    .btn-ghost:hover {
      background: var(--surface-hover);
      border-color: var(--text-muted);
    }

    /* Filter Toolbar (flat bar, no nested boxes) */
    .filter-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px 10px;
      padding: 10px 0;
      border-bottom: 1px solid var(--border);
    }

    .control-input,
    .control-select {
      min-height: 36px;
      padding: 0 10px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-strong);
      background: var(--surface);
      color: var(--text);
      font-size: 0.8125rem;
      transition: border-color 140ms var(--ease-out);
    }
    .control-input:hover,
    .control-select:hover {
      border-color: var(--text-muted);
    }
    .control-input::placeholder {
      color: var(--text-muted);
    }
    .search-input {
      width: 210px;
      max-width: 100%;
    }

    .range-group {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 36px;
      padding: 0 4px;
      font-size: 0.8125rem;
      color: var(--text-secondary);
    }
    .range-group input[type="range"] {
      width: 96px;
      accent-color: var(--accent);
      cursor: pointer;
    }

    .check-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 36px;
      padding: 0 10px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
      font-size: 0.8125rem;
      color: var(--text-secondary);
      cursor: pointer;
      user-select: none;
      transition: background-color 140ms var(--ease-out), border-color 140ms var(--ease-out);
    }
    .check-pill:hover {
      background: var(--surface-hover);
      border-color: var(--border-strong);
    }
    .check-pill input {
      accent-color: var(--accent);
      cursor: pointer;
    }

    .sort-select {
      margin-left: auto;
    }

    /* Main Workspace Grid */
    .workspace-grid {
      display: grid;
      grid-template-columns: minmax(0, 7fr) minmax(0, 5fr);
      gap: 16px;
      align-items: start;
    }

    @media (max-width: 1024px) {
      .workspace-grid {
        grid-template-columns: 1fr;
      }
      .sort-select {
        margin-left: 0;
      }
    }

    @media (max-width: 640px) {
      .app-shell { padding: 12px 14px 20px; }
      .search-input { width: 100%; }
      .kpi-item + .kpi-item { padding-left: 10px; }
      .kpi-strip { gap: 10px; }
    }

    /* Left Column: Map + Inspector */
    .left-col {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .map-frame {
      position: relative;
      height: 480px;
      border-radius: var(--radius-lg);
      overflow: hidden;
      border: 1px solid var(--border);
      background: var(--surface);
    }

    @media (max-width: 640px) {
      .map-frame { height: 360px; }
    }

    #map-canvas {
      width: 100%;
      height: 100%;
      display: block;
      touch-action: none;
      cursor: grab;
    }
    #map-canvas:active { cursor: grabbing; }

    .map-overlay-top-left {
      position: absolute;
      top: 10px;
      left: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .map-chip {
      min-height: 32px;
      padding: 0 11px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-strong);
      background: rgba(19, 26, 36, 0.88);
      backdrop-filter: blur(8px);
      color: var(--text);
      font-size: 0.75rem;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 140ms var(--ease-out), border-color 140ms var(--ease-out);
    }
    html.light .map-chip {
      background: rgba(255, 255, 255, 0.92);
    }
    .map-chip:hover {
      border-color: var(--accent);
    }
    .map-chip[aria-pressed="true"] {
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff;
    }

    .map-zoom-controls {
      position: absolute;
      top: 10px;
      right: 10px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .zoom-btn {
      width: 36px;
      height: 36px;
      display: grid;
      place-items: center;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-strong);
      background: rgba(19, 26, 36, 0.88);
      backdrop-filter: blur(8px);
      color: var(--text);
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: border-color 140ms var(--ease-out);
    }
    html.light .zoom-btn {
      background: rgba(255, 255, 255, 0.92);
    }
    .zoom-btn:hover { border-color: var(--accent); }

    .map-legend {
      position: absolute;
      bottom: 10px;
      left: 10px;
      padding: 6px 11px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
      background: rgba(19, 26, 36, 0.88);
      backdrop-filter: blur(8px);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px;
      font-size: 0.75rem;
      color: var(--text-secondary);
    }
    html.light .map-legend {
      background: rgba(255, 255, 255, 0.92);
    }

    .legend-item {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .legend-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      display: inline-block;
    }
    .legend-square {
      width: 8px;
      height: 8px;
      border-radius: 2px;
      display: inline-block;
    }

    .map-tooltip {
      position: absolute;
      z-index: 20;
      pointer-events: none;
      max-width: 250px;
      padding: 8px 10px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-strong);
      background: var(--surface);
      box-shadow: var(--shadow-md);
      font-size: 0.75rem;
    }
    .hidden { display: none !important; }

    /* Inspector Panel */
    .inspector-panel {
      padding: 16px;
      border-radius: var(--radius-lg);
      border: 1px solid var(--border);
      background: var(--surface);
    }

    .inspector-empty {
      text-align: center;
      padding: 20px 12px;
      color: var(--text-muted);
      font-size: 0.875rem;
    }

    .inspector-layout {
      display: flex;
      gap: 16px;
      align-items: flex-start;
    }
    @media (max-width: 640px) {
      .inspector-layout { flex-direction: column; }
    }

    .inspector-thumb {
      width: 152px;
      height: 116px;
      object-fit: cover;
      border-radius: var(--radius-md);
      background: var(--surface-hover);
      flex-shrink: 0;
    }
    @media (max-width: 640px) {
      .inspector-thumb { width: 100%; height: 180px; }
    }

    .inspector-body {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .inspector-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }

    .inspector-title {
      margin: 0;
      font-size: 1rem;
      font-weight: 600;
      line-height: 1.3;
    }

    .inspector-meta {
      margin-top: 2px;
      font-size: 0.8125rem;
      color: var(--text-muted);
    }

    .inspector-price {
      text-align: right;
      flex-shrink: 0;
    }
    .inspector-price-clp {
      font-size: 1rem;
      font-weight: 700;
      color: var(--accent-text);
    }
    .inspector-price-uf {
      font-size: 0.75rem;
      color: var(--text-muted);
    }

    .inspector-specs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 16px;
      padding: 8px 0;
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      font-size: 0.8125rem;
      color: var(--text-secondary);
    }
    .inspector-specs strong { color: var(--text); font-weight: 600; }

    .tag-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .tag {
      font-size: 0.75rem;
      font-weight: 500;
      padding: 2px 8px;
      border-radius: 999px;
    }
    .tag-pool { background: var(--pool-soft); color: var(--pool); }
    .tag-quincho { background: rgba(251, 146, 60, 0.14); color: #fb923c; }
    .tag-condo { background: var(--visited-soft); color: var(--visited); }
    .tag-service { background: rgba(192, 132, 252, 0.14); color: #c084fc; }
    .tag-furnished { background: rgba(244, 114, 182, 0.14); color: #f472b6; }
    html.light .tag-quincho { color: #c2410c; }
    html.light .tag-service { color: #7e22ce; }
    html.light .tag-furnished { color: #be185d; }

    .inspector-excerpt {
      margin: 0;
      font-size: 0.8125rem;
      color: var(--text-secondary);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .inspector-actions {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }

    .action-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 36px;
      padding: 0 11px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-strong);
      background: transparent;
      color: var(--text-secondary);
      font-size: 0.8125rem;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 140ms var(--ease-out), border-color 140ms var(--ease-out), color 140ms var(--ease-out);
    }
    .action-btn:hover {
      background: var(--surface-hover);
      color: var(--text);
    }
    .action-btn.is-shortlist {
      background: var(--shortlist-soft);
      border-color: var(--shortlist);
      color: var(--shortlist);
    }
    .action-btn.is-visited {
      background: var(--visited-soft);
      border-color: var(--visited);
      color: var(--visited);
    }
    .action-btn.is-dismissed {
      background: var(--dismissed-soft);
      border-color: var(--dismissed);
      color: var(--dismissed);
    }

    .btn-primary {
      margin-left: auto;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 36px;
      padding: 0 14px;
      border-radius: var(--radius-sm);
      background: var(--accent);
      color: #ffffff;
      font-size: 0.8125rem;
      font-weight: 600;
      text-decoration: none;
      transition: opacity 140ms var(--ease-out);
    }
    .btn-primary:hover { opacity: 0.92; }

    .note-input {
      width: 100%;
      min-height: 36px;
      padding: 0 10px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-size: 0.8125rem;
    }
    .note-input:focus {
      border-color: var(--accent);
      outline: none;
    }

    /* Right Column: Flat List Container with Hairline Dividers (no nested cards) */
    .listings-panel {
      border-radius: var(--radius-lg);
      border: 1px solid var(--border);
      background: var(--surface);
      max-height: 740px;
      overflow-y: auto;
    }

    .listing-row {
      width: 100%;
      text-align: left;
      background: transparent;
      border: none;
      border-bottom: 1px solid var(--border);
      padding: 12px 14px;
      display: flex;
      gap: 12px;
      align-items: flex-start;
      cursor: pointer;
      transition: background-color 140ms var(--ease-out);
    }
    .listing-row:last-child { border-bottom: none; }
    .listing-row:hover { background: var(--surface-hover); }
    .listing-row[aria-pressed="true"] {
      background: var(--surface-active);
      box-shadow: inset 3px 0 0 var(--accent);
    }

    .listing-thumb {
      width: 84px;
      height: 84px;
      object-fit: cover;
      border-radius: var(--radius-sm);
      background: var(--surface-hover);
      flex-shrink: 0;
    }

    .listing-thumb-empty {
      width: 84px;
      height: 84px;
      border-radius: var(--radius-sm);
      background: var(--surface-hover);
      color: var(--text-muted);
      font-size: 0.75rem;
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }

    .listing-info {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .listing-top {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 10px;
    }

    .listing-title {
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .listing-price {
      font-size: 0.875rem;
      font-weight: 700;
      color: var(--accent-text);
      flex-shrink: 0;
    }

    .listing-zone {
      font-size: 0.75rem;
      color: var(--text-muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .listing-specs {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      margin-top: 2px;
      font-size: 0.75rem;
      color: var(--text-secondary);
    }

    .listing-note {
      margin-top: 2px;
      font-size: 0.75rem;
      color: var(--shortlist);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .empty-state {
      padding: 36px 20px;
      text-align: center;
      color: var(--text-muted);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        transition-duration: 0.01ms !important;
      }
    }
  </style>
</head>
<body>
  <div class="app-shell">

    <!-- Header & KPIs -->
    <header class="app-header">
      <div class="brand-group">
        <div class="brand-title-row">
          <h1 class="brand-title">Santiago House Hunter</h1>
          <span class="brand-badge">4–6 Dorm · $3M–$5M CLP</span>
        </div>
        <p class="brand-subtitle" id="meta-subtitle">Loading listings...</p>
      </div>

      <div class="header-actions">
        <div class="kpi-strip" aria-label="Summary metrics">
          <div class="kpi-item">
            <span class="kpi-label">Showing</span>
            <span id="kpi-count" class="kpi-val tabular-nums">0</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-label">Avg Rent</span>
            <span id="kpi-avg" class="kpi-val tabular-nums">-</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-label">With Pool</span>
            <span id="kpi-pool" class="kpi-val pool tabular-nums">0</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-label">Shortlist</span>
            <span id="kpi-shortlist" class="kpi-val shortlist tabular-nums">0</span>
          </div>
        </div>

        <button id="btn-theme" type="button" class="btn-ghost" aria-label="Toggle light or dark theme" title="Toggle light/dark theme">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="4"></circle>
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>
          </svg>
          <span id="theme-label">Light</span>
        </button>

        <button id="btn-export" type="button" class="btn-ghost" title="Export your shortlist &amp; notes as JSON">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Export Tracker
        </button>
      </div>
    </header>

    <!-- Filter Toolbar -->
    <section class="filter-bar" aria-label="Property filters">
      <input id="f-search" type="search" aria-label="Search street, sector, or title"
        placeholder="Search street, sector, title..." class="control-input search-input" />

      <select id="f-zone" aria-label="Filter by zone" class="control-select">
        <option value="all">All Zones</option>
        <option value="la_dehesa">La Dehesa / Lo Barnechea</option>
        <option value="alto_las_condes">Alto Las Condes / Las Condes</option>
      </select>

      <select id="f-beds" aria-label="Filter by bedrooms" class="control-select">
        <option value="all">4–6 Bedrooms</option>
        <option value="4">4 Bedrooms</option>
        <option value="5">5 Bedrooms</option>
        <option value="6">6 Bedrooms</option>
      </select>

      <select id="f-rooms" aria-label="Filter by total rooms" class="control-select">
        <option value="0">Any Total Rooms</option>
        <option value="7">7+ Total Rooms</option>
        <option value="8">8+ Total Rooms</option>
        <option value="9">9+ Total Rooms</option>
      </select>

      <label class="range-group" for="f-max-price">
        <span>Max:</span>
        <input id="f-max-price" type="range" min="3000000" max="5000000" step="100000" value="5000000" />
        <span id="f-max-price-lbl" class="tabular-nums">$5.0M</span>
      </label>

      <label class="check-pill">
        <input id="f-pool" type="checkbox" />
        <span>Pool Only</span>
      </label>

      <label class="check-pill">
        <input id="f-condo" type="checkbox" />
        <span>Condominio</span>
      </label>

      <select id="f-track" aria-label="Filter by tracker status" class="control-select">
        <option value="active">All Active</option>
        <option value="shortlist">Shortlisted Only</option>
        <option value="visited">Visited Only</option>
        <option value="all_inc_dismissed">Include Dismissed</option>
      </select>

      <select id="f-sort" aria-label="Sort listings" class="control-select sort-select">
        <option value="price_asc">Price: Low to High</option>
        <option value="price_desc">Price: High to Low</option>
        <option value="beds_desc">Bedrooms: Most First</option>
        <option value="m2_desc">Size (m²): Largest First</option>
        <option value="rooms_desc">Total Rooms: Most First</option>
      </select>
    </section>

    <!-- Main Grid: Map + Explorer List -->
    <main class="workspace-grid">

      <!-- Left: Interactive Map + Selected Inspector -->
      <div class="left-col">
        <div class="map-frame">
          <canvas id="map-canvas" aria-label="Interactive map of house listings in La Dehesa and Alto Las Condes"></canvas>

          <div class="map-overlay-top-left" role="group" aria-label="Jump to zone">
            <button type="button" data-jump="all" class="map-chip" aria-pressed="true">Both Zones</button>
            <button type="button" data-jump="la_dehesa" class="map-chip" aria-pressed="false">La Dehesa</button>
            <button type="button" data-jump="alto_las_condes" class="map-chip" aria-pressed="false">Alto Las Condes</button>
          </div>

          <div class="map-zoom-controls" role="group" aria-label="Map zoom controls">
            <button id="zoom-in" type="button" class="zoom-btn" aria-label="Zoom in">+</button>
            <button id="zoom-out" type="button" class="zoom-btn" aria-label="Zoom out">−</button>
          </div>

          <div class="map-legend" aria-label="Map legend">
            <span class="legend-item"><span class="legend-dot" style="background: var(--pool);"></span> Pool</span>
            <span class="legend-item"><span class="legend-dot" style="background: #818cf8;"></span> Standard</span>
            <span class="legend-item"><span class="legend-dot" style="background: var(--shortlist);"></span> Shortlisted</span>
            <span class="legend-item"><span class="legend-square" style="background: #fb7185;"></span> Landmark</span>
          </div>

          <div id="map-tooltip" class="map-tooltip hidden" role="status"></div>
        </div>

        <section id="inspector" class="inspector-panel" aria-label="Selected property details">
          <div class="inspector-empty">
            Click any house pin on the map or any listing on the right to inspect full details, amenities, and add notes.
          </div>
        </section>
      </div>

      <!-- Right: Scrollable Property List -->
      <section class="listings-panel" id="listing-cards" aria-label="Matching properties"></section>
    </main>
  </div>

  <script>
    const PAYLOAD = __PAYLOAD_JSON__;
    const LISTINGS = PAYLOAD.listings || [];

    const STORAGE_KEY = "santiago_house_tracker_v1";
    const THEME_KEY = "santiago_house_theme_v1";
    let tracker = {};
    try {
      tracker = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    } catch (e) { tracker = {}; }

    function saveTracker() {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(tracker)); } catch (e) {}
    }

    function getTrack(id) {
      return tracker[id] || { status: "none", note: "" };
    }

    function setTrack(id, patch) {
      tracker[id] = { ...getTrack(id), ...patch, updatedAt: new Date().toISOString() };
      saveTracker();
      renderAll();
    }

    function esc(str) {
      return String(str ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
      }[ch]));
    }

    // Theme initialization & toggle
    const themeBtn = document.getElementById("btn-theme");
    const themeLabel = document.getElementById("theme-label");
    function applyTheme(mode) {
      document.documentElement.classList.toggle("light", mode === "light");
      themeLabel.textContent = mode === "light" ? "Dark" : "Light";
      try { localStorage.setItem(THEME_KEY, mode); } catch (e) {}
      if (typeof drawMap === "function") drawMap();
    }
    try {
      const savedTheme = localStorage.getItem(THEME_KEY);
      if (savedTheme === "light") applyTheme("light");
    } catch (e) {}
    themeBtn.addEventListener("click", () => {
      const next = document.documentElement.classList.contains("light") ? "dark" : "light";
      applyTheme(next);
    });

    // Formatters
    const fmtCLP = (n) => "$" + Math.round(n).toLocaleString("es-CL");
    const fmtShortCLP = (n) => "$" + (n / 1e6).toFixed(2).replace(/\.00$/, "") + "M";

    // Subtitle
    const dt = PAYLOAD.generated_at ? new Date(PAYLOAD.generated_at).toLocaleString() : "Today";
    document.getElementById("meta-subtitle").textContent =
      `Updated ${dt} · UF = ${fmtCLP(PAYLOAD.uf_clp || 41364)} · Sources: TOCTOC & PortalInmobiliario`;

    // Landmarks & Corridors in NE Santiago
    const LANDMARKS = [
      { name: "Alto Las Condes", lat: -33.3905, lon: -70.5465 },
      { name: "Portal La Dehesa", lat: -33.3575, lon: -70.5145 },
      { name: "Mall Sport", lat: -33.3805, lon: -70.5335 },
      { name: "Los Dominicos", lat: -33.4070, lon: -70.5410 },
      { name: "Golf Lomas La Dehesa", lat: -33.3340, lon: -70.5115 },
      { name: "San Carlos Apoquindo", lat: -33.4040, lon: -70.5060 },
      { name: "Los Trapenses", lat: -33.3325, lon: -70.5430 }
    ];

    const ROADS = [
      [[-33.405, -70.595], [-33.396, -70.568], [-33.390, -70.546], [-33.381, -70.533], [-33.371, -70.515], [-33.362, -70.485]],
      [[-33.415, -70.595], [-33.408, -70.565], [-33.407, -70.541], [-33.404, -70.506]],
      [[-33.372, -70.519], [-33.357, -70.514], [-33.342, -70.513], [-33.328, -70.520], [-33.332, -70.543]],
      [[-33.405, -70.595], [-33.386, -70.560], [-33.372, -70.525], [-33.364, -70.495], [-33.358, -70.460]],
      [[-33.425, -70.550], [-33.407, -70.548], [-33.390, -70.546]],
      [[-33.425, -70.570], [-33.404, -70.568], [-33.388, -70.566]]
    ];

    const mapState = {
      centerLat: -33.372,
      centerLon: -70.525,
      zoom: 1.0,
      dragging: false,
      moved: false,
      pointerId: null,
      lastX: 0,
      lastY: 0,
      selectedId: null,
      hoveredId: null
    };

    const canvas = document.getElementById("map-canvas");
    const ctx = canvas.getContext("2d");

    function resizeCanvas() {
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      drawMap();
    }

    function project(lat, lon) {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      const baseScale = Math.min(w, h) * 8.2 * mapState.zoom;
      const cosLat = Math.cos((mapState.centerLat * Math.PI) / 180);
      const x = w / 2 + (lon - mapState.centerLon) * cosLat * baseScale;
      const y = h / 2 - (lat - mapState.centerLat) * baseScale;
      return { x, y };
    }

    function getFilteredListings() {
      const q = document.getElementById("f-search").value.trim().toLowerCase();
      const zone = document.getElementById("f-zone").value;
      const beds = document.getElementById("f-beds").value;
      const minRooms = parseInt(document.getElementById("f-rooms").value, 10) || 0;
      const maxPrice = parseInt(document.getElementById("f-max-price").value, 10);
      const poolOnly = document.getElementById("f-pool").checked;
      const condoOnly = document.getElementById("f-condo").checked;
      const trackMode = document.getElementById("f-track").value;
      const sortMode = document.getElementById("f-sort").value;

      let out = LISTINGS.filter((item) => {
        const tr = getTrack(item.id);
        if (trackMode === "active" && tr.status === "dismissed") return false;
        if (trackMode === "shortlist" && tr.status !== "shortlist") return false;
        if (trackMode === "visited" && tr.status !== "visited") return false;

        if (zone !== "all" && item.zone !== zone) return false;
        if (beds !== "all" && item.bedrooms !== parseInt(beds, 10)) return false;
        if ((item.estimated_rooms || 0) < minRooms) return false;
        if (item.price_clp > maxPrice) return false;
        if (poolOnly && !item.has_pool) return false;
        if (condoOnly && !item.is_condominio) return false;

        if (q) {
          const blob = `${item.title} ${item.address} ${item.comuna} ${item.agency} ${tr.note}`.toLowerCase();
          if (!blob.includes(q)) return false;
        }
        return true;
      });

      out.sort((a, b) => {
        if (sortMode === "price_asc") return a.price_clp - b.price_clp;
        if (sortMode === "price_desc") return b.price_clp - a.price_clp;
        if (sortMode === "beds_desc") return b.bedrooms - a.bedrooms || a.price_clp - b.price_clp;
        if (sortMode === "m2_desc") return (b.built_m2 || 0) - (a.built_m2 || 0);
        if (sortMode === "rooms_desc") return (b.estimated_rooms || 0) - (a.estimated_rooms || 0);
        return 0;
      });
      return out;
    }

    function drawMap() {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (!w || !h) return;

      const isLight = document.documentElement.classList.contains("light");
      const bg = isLight ? "#eef2f6" : "#0b111a";
      const gridColor = isLight ? "rgba(15,23,42,0.06)" : "rgba(148,163,184,0.07)";
      const roadColor = isLight ? "rgba(71,85,105,0.34)" : "rgba(148,163,184,0.22)";
      const textMuted = isLight ? "#475569" : "#9aa8bc";

      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);

      ctx.strokeStyle = gridColor;
      ctx.lineWidth = 1;
      for (let lat = -33.44; lat <= -33.30; lat += 0.02) {
        const p1 = project(lat, -70.62);
        const p2 = project(lat, -70.43);
        ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
      }
      for (let lon = -70.62; lon <= -70.44; lon += 0.02) {
        const p1 = project(-33.44, lon);
        const p2 = project(-33.30, lon);
        ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
      }

      const drawZoneHalo = (lat, lon, label, color) => {
        const p = project(lat, lon);
        const r = 68 * mapState.zoom;
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.fillStyle = textMuted;
        ctx.font = "600 11px IBM Plex Sans, ui-sans-serif, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(label, p.x, p.y - r + 16);
      };
      drawZoneHalo(-33.346, -70.514, "LA DEHESA / LO BARNECHEA", "rgba(56, 189, 248, 0.06)");
      drawZoneHalo(-33.395, -70.542, "ALTO LAS CONDES / LAS CONDES", "rgba(129, 140, 248, 0.06)");

      ctx.strokeStyle = roadColor;
      ctx.lineWidth = Math.max(1.5, 2 * mapState.zoom);
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ROADS.forEach((line) => {
        ctx.beginPath();
        line.forEach(([lat, lon], idx) => {
          const p = project(lat, lon);
          if (idx === 0) ctx.moveTo(p.x, p.y);
          else ctx.lineTo(p.x, p.y);
        });
        ctx.stroke();
      });

      LANDMARKS.forEach((lm) => {
        const p = project(lm.lat, lm.lon);
        ctx.fillStyle = "#fb7185";
        ctx.fillRect(p.x - 3.5, p.y - 3.5, 7, 7);
        ctx.fillStyle = textMuted;
        ctx.font = "500 10px IBM Plex Sans, ui-sans-serif, system-ui, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(lm.name, p.x + 7, p.y + 3);
      });

      const items = getFilteredListings();
      items.forEach((item) => {
        if (!item.lat || !item.lon) return;
        const p = project(item.lat, item.lon);
        const tr = getTrack(item.id);
        const isSel = item.id === mapState.selectedId;
        const isHov = item.id === mapState.hoveredId;

        let color = item.has_pool ? (isLight ? "#0891b2" : "#22d3ee") : "#818cf8";
        if (tr.status === "shortlist") color = isLight ? "#d97706" : "#f5b942";
        if (tr.status === "visited") color = isLight ? "#047857" : "#34d399";
        if (tr.status === "dismissed") color = "#64748b";

        const radius = isSel ? 9 : isHov ? 8 : 6;

        if (isSel || isHov) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, radius + 5, 0, Math.PI * 2);
          ctx.fillStyle = isLight ? "rgba(37, 99, 235, 0.18)" : "rgba(79, 143, 247, 0.28)";
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = isSel ? 2.5 : 1.5;
        ctx.strokeStyle = isLight ? "#ffffff" : "#0c1118";
        ctx.stroke();

        if (mapState.zoom >= 1.5 || isSel) {
          const lbl = fmtShortCLP(item.price_clp);
          ctx.font = "600 10px ui-monospace, monospace";
          const tw = ctx.measureText(lbl).width + 10;
          ctx.fillStyle = isLight ? "rgba(255,255,255,0.95)" : "rgba(19,26,36,0.92)";
          ctx.fillRect(p.x - tw / 2, p.y - radius - 19, tw, 15);
          ctx.fillStyle = isLight ? "#0f172a" : "#edf2f7";
          ctx.textAlign = "center";
          ctx.fillText(lbl, p.x, p.y - radius - 8);
        }
      });
    }

    function findPinAt(mx, my) {
      const items = getFilteredListings();
      let best = null;
      let bestDist = 16;
      for (const item of items) {
        if (!item.lat || !item.lon) continue;
        const p = project(item.lat, item.lon);
        const d = Math.hypot(p.x - mx, p.y - my);
        if (d < bestDist) {
          bestDist = d;
          best = item;
        }
      }
      return best;
    }

    // Unified Pointer Events for mouse + touch pan & tap
    canvas.addEventListener("pointerdown", (e) => {
      mapState.dragging = true;
      mapState.moved = false;
      mapState.pointerId = e.pointerId;
      mapState.lastX = e.clientX;
      mapState.lastY = e.clientY;
      try { canvas.setPointerCapture(e.pointerId); } catch (err) {}
    });

    canvas.addEventListener("pointermove", (e) => {
      if (mapState.dragging && e.pointerId === mapState.pointerId) {
        const dx = e.clientX - mapState.lastX;
        const dy = e.clientY - mapState.lastY;
        if (Math.hypot(dx, dy) > 3) mapState.moved = true;
        mapState.lastX = e.clientX;
        mapState.lastY = e.clientY;
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        const baseScale = Math.min(w, h) * 8.2 * mapState.zoom;
        const cosLat = Math.cos((mapState.centerLat * Math.PI) / 180);
        mapState.centerLon -= dx / (cosLat * baseScale);
        mapState.centerLat += dy / baseScale;
        drawMap();
        return;
      }

      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = findPinAt(mx, my);
      const tt = document.getElementById("map-tooltip");
      if (hit) {
        mapState.hoveredId = hit.id;
        canvas.style.cursor = "pointer";
        tt.classList.remove("hidden");
        tt.style.left = Math.min(mx + 12, rect.width - 255) + "px";
        tt.style.top = Math.max(8, my - 10) + "px";
        tt.innerHTML = `
          <div style="font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${esc(hit.title)}</div>
          <div style="color:var(--text-muted); margin-top:2px;">
            ${fmtCLP(hit.price_clp)} (${esc(hit.price_uf || "-")} UF) · ${hit.bedrooms}D / ${hit.bathrooms}B
            ${hit.has_pool ? " · <span style='color:var(--pool);'>Pool</span>" : ""}
          </div>
        `;
      } else {
        mapState.hoveredId = null;
        canvas.style.cursor = "grab";
        tt.classList.add("hidden");
      }
      drawMap();
    });

    function endDrag(e) {
      if (!mapState.dragging) return;
      const wasMoved = mapState.moved;
      mapState.dragging = false;
      mapState.pointerId = null;
      try { canvas.releasePointerCapture(e.pointerId); } catch (err) {}
      if (!wasMoved && e.type === "pointerup") {
        const rect = canvas.getBoundingClientRect();
        const hit = findPinAt(e.clientX - rect.left, e.clientY - rect.top);
        if (hit) selectProperty(hit.id);
      }
    }
    canvas.addEventListener("pointerup", endDrag);
    canvas.addEventListener("pointercancel", endDrag);
    canvas.addEventListener("lostpointercapture", () => { mapState.dragging = false; });

    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.18 : 0.85;
      mapState.zoom = Math.max(0.6, Math.min(6.0, mapState.zoom * factor));
      drawMap();
    }, { passive: false });

    document.getElementById("zoom-in").addEventListener("click", () => {
      mapState.zoom = Math.min(6.0, mapState.zoom * 1.3);
      drawMap();
    });
    document.getElementById("zoom-out").addEventListener("click", () => {
      mapState.zoom = Math.max(0.6, mapState.zoom / 1.3);
      drawMap();
    });

    const jumpBtns = document.querySelectorAll(".map-chip[data-jump]");
    jumpBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const z = btn.dataset.jump;
        jumpBtns.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
        if (z === "la_dehesa") {
          mapState.centerLat = -33.348; mapState.centerLon = -70.514; mapState.zoom = 1.65;
        } else if (z === "alto_las_condes") {
          mapState.centerLat = -33.395; mapState.centerLon = -70.538; mapState.zoom = 1.65;
        } else {
          mapState.centerLat = -33.372; mapState.centerLon = -70.525; mapState.zoom = 1.0;
        }
        drawMap();
      });
    });

    function selectProperty(id) {
      mapState.selectedId = id;
      const item = LISTINGS.find((x) => x.id === id);
      if (item && item.lat && item.lon) {
        mapState.centerLat = item.lat;
        mapState.centerLon = item.lon;
        if (mapState.zoom < 1.5) mapState.zoom = 1.7;
      }
      renderInspector(item);
      renderList();
      drawMap();
    }

    const SVG_STAR = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;
    const SVG_CHECK = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>`;
    const SVG_EXT = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;

    function renderInspector(item) {
      const box = document.getElementById("inspector");
      if (!item) {
        box.innerHTML = `<div class="inspector-empty">Select a house on the map or list to inspect details.</div>`;
        return;
      }
      const tr = getTrack(item.id);
      const tags = [];
      if (item.has_pool) tags.push(`<span class="tag tag-pool">Pool</span>`);
      if (item.has_quincho) tags.push(`<span class="tag tag-quincho">Quincho</span>`);
      if (item.is_condominio) tags.push(`<span class="tag tag-condo">Condominio</span>`);
      if (item.has_service_room) tags.push(`<span class="tag tag-service">Service Room</span>`);
      if (item.is_furnished) tags.push(`<span class="tag tag-furnished">Furnished</span>`);

      box.innerHTML = `
        <div class="inspector-layout">
          ${item.image ? `<img src="${esc(item.image)}" alt="${esc(item.title)}" class="inspector-thumb" onerror="this.style.display='none'" />` : ""}
          <div class="inspector-body">
            <div class="inspector-head">
              <div>
                <h2 class="inspector-title">${esc(item.title)}</h2>
                <div class="inspector-meta">${esc(item.address)} · ${esc(item.source)} (${esc(item.agency)})</div>
              </div>
              <div class="inspector-price">
                <div class="inspector-price-clp tabular-nums">${fmtCLP(item.price_clp)}</div>
                <div class="inspector-price-uf tabular-nums">${esc(item.price_uf || "-")} UF / mo</div>
              </div>
            </div>

            <div class="inspector-specs tabular-nums">
              <span><strong>${item.bedrooms}</strong> Bedrooms</span>
              <span><strong>${item.bathrooms || "-"}</strong> Baths</span>
              <span><strong>~${item.estimated_rooms}</strong> Total Rooms</span>
              <span><strong>${item.built_m2 ? item.built_m2 + " m²" : "-"}</strong> Built</span>
              ${item.lot_m2 ? `<span><strong>${item.lot_m2} m²</strong> Lot</span>` : ""}
              ${item.parking_spaces ? `<span><strong>${item.parking_spaces}</strong> Parking</span>` : ""}
            </div>

            ${tags.length ? `<div class="tag-row">${tags.join("")}</div>` : ""}
            ${item.description_excerpt ? `<p class="inspector-excerpt">${esc(item.description_excerpt)}</p>` : ""}

            <div class="inspector-actions">
              <button type="button" onclick="setTrack('${esc(item.id)}', {status: '${tr.status === "shortlist" ? "none" : "shortlist"}'})"
                class="action-btn ${tr.status === "shortlist" ? "is-shortlist" : ""}">
                ${SVG_STAR}
                ${tr.status === "shortlist" ? "Shortlisted" : "Shortlist"}
              </button>
              <button type="button" onclick="setTrack('${esc(item.id)}', {status: '${tr.status === "visited" ? "none" : "visited"}'})"
                class="action-btn ${tr.status === "visited" ? "is-visited" : ""}">
                ${SVG_CHECK}
                ${tr.status === "visited" ? "Visited" : "Mark Visited"}
              </button>
              <button type="button" onclick="setTrack('${esc(item.id)}', {status: '${tr.status === "dismissed" ? "none" : "dismissed"}'})"
                class="action-btn ${tr.status === "dismissed" ? "is-dismissed" : ""}">
                ${tr.status === "dismissed" ? "Restore" : "Dismiss"}
              </button>
              <a href="${esc(item.url)}" target="_blank" rel="noopener" class="btn-primary">
                Open Listing ${SVG_EXT}
              </a>
            </div>

            <div>
              <input type="text" aria-label="Personal note for ${esc(item.title)}"
                value="${esc(tr.note || "")}"
                placeholder="Add personal note (e.g., 'Contacted broker, visit Tuesday 10am')..."
                onchange="setTrack('${esc(item.id)}', {note: this.value})"
                class="note-input" />
            </div>
          </div>
        </div>
      `;
    }

    function resetFilters() {
      document.getElementById("f-search").value = "";
      document.getElementById("f-zone").value = "all";
      document.getElementById("f-beds").value = "all";
      document.getElementById("f-rooms").value = "0";
      document.getElementById("f-max-price").value = "5000000";
      document.getElementById("f-max-price-lbl").textContent = "$5.0M";
      document.getElementById("f-pool").checked = false;
      document.getElementById("f-condo").checked = false;
      document.getElementById("f-track").value = "active";
      renderAll();
    }

    function renderList() {
      const items = getFilteredListings();
      const container = document.getElementById("listing-cards");

      document.getElementById("kpi-count").textContent = items.length;
      const avg = items.length ? items.reduce((s, x) => s + x.price_clp, 0) / items.length : 0;
      document.getElementById("kpi-avg").textContent = items.length ? fmtShortCLP(avg) : "-";
      document.getElementById("kpi-pool").textContent = items.filter((x) => x.has_pool).length;
      document.getElementById("kpi-shortlist").textContent = LISTINGS.filter((x) => getTrack(x.id).status === "shortlist").length;

      if (!items.length) {
        container.innerHTML = `
          <div class="empty-state">
            <div>No houses match your current filters.</div>
            <button type="button" class="btn-ghost" onclick="resetFilters()">Reset Filters</button>
          </div>
        `;
        return;
      }

      container.innerHTML = items.map((item) => {
        const tr = getTrack(item.id);
        const isSel = item.id === mapState.selectedId;
        return `
          <button type="button" class="listing-row" aria-pressed="${isSel}" onclick="selectProperty('${esc(item.id)}')">
            ${item.image
              ? `<img src="${esc(item.image)}" alt="" class="listing-thumb" loading="lazy" onerror="this.outerHTML='<div class=\\'listing-thumb-empty\\'>No img</div>'" />`
              : `<div class="listing-thumb-empty">No img</div>`}
            <div class="listing-info">
              <div class="listing-top">
                <div class="listing-title">${esc(item.title)}</div>
                <span class="listing-price tabular-nums">${fmtShortCLP(item.price_clp)}</span>
              </div>
              <div class="listing-zone">${esc(item.zone_label)} · ${esc(item.source)}</div>
              <div class="listing-specs tabular-nums">
                <span>${item.bedrooms}D</span>
                <span>${item.bathrooms || "-"}B</span>
                <span>~${item.estimated_rooms} rooms</span>
                ${item.built_m2 ? `<span>${item.built_m2} m²</span>` : ""}
                ${item.has_pool ? `<span class="tag tag-pool">Pool</span>` : ""}
                ${tr.status === "shortlist" ? `<span style="color:var(--shortlist); display:inline-flex; align-items:center;" title="Shortlisted">${SVG_STAR}</span>` : ""}
                ${tr.status === "visited" ? `<span style="color:var(--visited); display:inline-flex; align-items:center;" title="Visited">${SVG_CHECK}</span>` : ""}
              </div>
              ${tr.note ? `<div class="listing-note">Note: ${esc(tr.note)}</div>` : ""}
            </div>
          </button>
        `;
      }).join("");
    }

    function renderAll() {
      renderList();
      drawMap();
      if (mapState.selectedId) {
        const cur = LISTINGS.find((x) => x.id === mapState.selectedId);
        renderInspector(cur);
      }
    }

    ["f-search", "f-zone", "f-beds", "f-rooms", "f-pool", "f-condo", "f-track", "f-sort"].forEach((id) => {
      document.getElementById(id).addEventListener("input", renderAll);
      document.getElementById(id).addEventListener("change", renderAll);
    });
    document.getElementById("f-max-price").addEventListener("input", (e) => {
      document.getElementById("f-max-price-lbl").textContent = fmtShortCLP(parseInt(e.target.value, 10));
      renderAll();
    });

    document.getElementById("btn-export").addEventListener("click", () => {
      const blob = new Blob([JSON.stringify({ exportedAt: new Date().toISOString(), tracker }, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "santiago_house_tracker.json";
      a.click();
      URL.revokeObjectURL(url);
    });

    window.addEventListener("resize", resizeCanvas);
    window.addEventListener("themechange", drawMap);
    resizeCanvas();
    renderAll();
    if (LISTINGS.length) {
      selectProperty(LISTINGS[0].id);
    }
  </script>
</body>
</html>
"""


def build_html(listings_path: Path = LISTINGS_PATH, out_path: Path = OUTPUT_HTML_PATH) -> str:
    with open(listings_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</script>", "<\\/script>")
    html = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", payload_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[DONE] Built interactive map ({payload.get('count', 0)} listings) -> {out_path}")
    return html


if __name__ == "__main__":
    build_html()
