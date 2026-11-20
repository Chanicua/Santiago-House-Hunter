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
  <title>Santiago House Hunter — La Dehesa & Alto Las Condes</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; padding: 0; font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; }
    .tabular-nums { font-variant-numeric: tabular-nums; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: rgba(128,128,128,0.35); border-radius: 3px; }
    canvas { touch-action: none; }
  </style>
</head>
<body class="bg-[var(--background,#0f172a)] text-[var(--foreground,#f8fafc)] antialiased">
  <div class="max-w-[1440px] mx-auto p-3 md:p-4 space-y-3">

    <!-- Header & KPIs -->
    <div class="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[var(--border,#334155)]">
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-base md:text-lg font-semibold tracking-tight">Santiago House Hunter</h1>
          <span class="text-xs px-2 py-0.5 rounded-full bg-[var(--primary,#3b82f6)]/15 text-[var(--primary,#60a5fa)] font-medium">
            4–6 Dorm · $3M–$5M CLP
          </span>
        </div>
        <p class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-0.5" id="meta-subtitle">
          Loading listings...
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2 text-xs">
        <div class="px-2.5 py-1.5 rounded-lg bg-[var(--card,#1e293b)] border border-[var(--border,#334155)]">
          <span class="text-[var(--muted-foreground,#94a3b8)]">Showing</span>
          <span id="kpi-count" class="ml-1 font-semibold tabular-nums">0</span>
        </div>
        <div class="px-2.5 py-1.5 rounded-lg bg-[var(--card,#1e293b)] border border-[var(--border,#334155)]">
          <span class="text-[var(--muted-foreground,#94a3b8)]">Avg Rent</span>
          <span id="kpi-avg" class="ml-1 font-semibold tabular-nums">-</span>
        </div>
        <div class="px-2.5 py-1.5 rounded-lg bg-[var(--card,#1e293b)] border border-[var(--border,#334155)]">
          <span class="text-[var(--muted-foreground,#94a3b8)]">With Pool</span>
          <span id="kpi-pool" class="ml-1 font-semibold tabular-nums text-cyan-400">0</span>
        </div>
        <div class="px-2.5 py-1.5 rounded-lg bg-[var(--card,#1e293b)] border border-[var(--border,#334155)]">
          <span class="text-[var(--muted-foreground,#94a3b8)]">Shortlist</span>
          <span id="kpi-shortlist" class="ml-1 font-semibold tabular-nums text-amber-400">0</span>
        </div>
        <button id="btn-export" class="px-2.5 py-1.5 rounded-lg bg-[var(--card,#1e293b)] hover:opacity-80 border border-[var(--border,#334155)] font-medium cursor-pointer" title="Export your shortlist & notes as JSON">
          Export Tracker
        </button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="p-2.5 rounded-xl bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] flex flex-wrap items-center gap-2.5 text-xs">
      <input id="f-search" type="text" placeholder="Search street, sector, title..."
        class="px-2.5 py-1.5 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-xs w-48 focus:outline-none focus:border-[var(--primary,#3b82f6)]" />

      <select id="f-zone" class="px-2 py-1.5 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-xs">
        <option value="all">All Zones</option>
        <option value="la_dehesa">La Dehesa / Lo Barnechea</option>
        <option value="alto_las_condes">Alto Las Condes / Las Condes</option>
      </select>

      <select id="f-beds" class="px-2 py-1.5 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-xs">
        <option value="all">4–6 Bedrooms</option>
        <option value="4">4 Bedrooms</option>
        <option value="5">5 Bedrooms</option>
        <option value="6">6 Bedrooms</option>
      </select>

      <select id="f-rooms" class="px-2 py-1.5 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-xs">
        <option value="0">Any Total Rooms</option>
        <option value="7">7+ Total Rooms</option>
        <option value="8">8+ Total Rooms</option>
        <option value="9">9+ Total Rooms</option>
      </select>

      <div class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)]">
        <span class="text-[var(--muted-foreground,#94a3b8)]">Max:</span>
        <input id="f-max-price" type="range" min="3000000" max="5000000" step="100000" value="5000000" class="w-24 accent-[var(--primary,#3b82f6)]" />
        <span id="f-max-price-lbl" class="font-mono tabular-nums">$5.0M</span>
      </div>

      <label class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] cursor-pointer select-none">
        <input id="f-pool" type="checkbox" class="accent-cyan-400" />
        <span>Pool Only</span>
      </label>

      <label class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] cursor-pointer select-none">
        <input id="f-condo" type="checkbox" class="accent-[var(--primary,#3b82f6)]" />
        <span>Condominio</span>
      </label>

      <select id="f-track" class="px-2 py-1.5 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-xs">
        <option value="active">All Active</option>
        <option value="shortlist">Shortlisted Only</option>
        <option value="visited">Visited Only</option>
        <option value="all_inc_dismissed">Include Dismissed</option>
      </select>

      <select id="f-sort" class="px-2 py-1.5 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-xs ml-auto">
        <option value="price_asc">Price: Low to High</option>
        <option value="price_desc">Price: High to Low</option>
        <option value="beds_desc">Bedrooms: Most First</option>
        <option value="m2_desc">Size (m²): Largest First</option>
        <option value="rooms_desc">Total Rooms: Most First</option>
      </select>
    </div>

    <!-- Main Grid: Map + Explorer List -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-3">

      <!-- Left: Interactive Map (7 cols) -->
      <div class="lg:col-span-7 flex flex-col gap-3">
        <div class="relative rounded-xl overflow-hidden border border-[var(--border,#334155)] bg-[var(--card,#1e293b)]" style="height: 480px;">
          <canvas id="map-canvas" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>

          <!-- Map Controls Top-Left -->
          <div class="absolute top-2.5 left-2.5 flex flex-wrap gap-1.5 text-xs">
            <button data-jump="all" class="jump-btn px-2.5 py-1 rounded-md bg-[var(--card,#1e293b)]/90 backdrop-blur border border-[var(--border,#334155)] hover:opacity-80 cursor-pointer font-medium">
              Both Zones
            </button>
            <button data-jump="la_dehesa" class="jump-btn px-2.5 py-1 rounded-md bg-[var(--card,#1e293b)]/90 backdrop-blur border border-[var(--border,#334155)] hover:opacity-80 cursor-pointer">
              La Dehesa
            </button>
            <button data-jump="alto_las_condes" class="jump-btn px-2.5 py-1 rounded-md bg-[var(--card,#1e293b)]/90 backdrop-blur border border-[var(--border,#334155)] hover:opacity-80 cursor-pointer">
              Alto Las Condes
            </button>
          </div>

          <!-- Zoom Controls Top-Right -->
          <div class="absolute top-2.5 right-2.5 flex flex-col gap-1 text-xs">
            <button id="zoom-in" class="w-7 h-7 rounded-md bg-[var(--card,#1e293b)]/90 border border-[var(--border,#334155)] hover:opacity-80 cursor-pointer font-bold">+</button>
            <button id="zoom-out" class="w-7 h-7 rounded-md bg-[var(--card,#1e293b)]/90 border border-[var(--border,#334155)] hover:opacity-80 cursor-pointer font-bold">−</button>
          </div>

          <!-- Legend Bottom-Left -->
          <div class="absolute bottom-2.5 left-2.5 px-2.5 py-1.5 rounded-lg bg-[var(--card,#1e293b)]/90 backdrop-blur border border-[var(--border,#334155)] flex flex-wrap items-center gap-3 text-xs">
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block"></span> Pool</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-indigo-400 inline-block"></span> Standard</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block"></span> Shortlisted</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-rose-400 inline-block"></span> Landmark</span>
          </div>

          <!-- Hover Tooltip -->
          <div id="map-tooltip" class="hidden pointer-events-none absolute z-20 px-2.5 py-1.5 rounded-lg bg-[var(--background,#0f172a)]/95 border border-[var(--border,#334155)] shadow-lg text-xs max-w-[240px]"></div>
        </div>

        <!-- Selected Property Inspector -->
        <div id="inspector" class="p-3.5 rounded-xl bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] text-xs">
          <div class="text-[var(--muted-foreground,#94a3b8)] text-center py-4">
            Click any house pin on the map or any card on the right to inspect full details, amenities, and add notes.
          </div>
        </div>
      </div>

      <!-- Right: Scrollable Property List (5 cols) -->
      <div class="lg:col-span-5 flex flex-col gap-2" style="max-height: 700px; overflow-y: auto;" id="listing-cards">
      </div>
    </div>
  </div>

  <script>
    const PAYLOAD = __PAYLOAD_JSON__;
    const LISTINGS = PAYLOAD.listings || [];

    // Tracker state persisted in localStorage
    const STORAGE_KEY = "santiago_house_tracker_v1";
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
      // Av. Kennedy -> Av. Las Condes -> Camino Farellones
      [[-33.405, -70.595], [-33.396, -70.568], [-33.390, -70.546], [-33.381, -70.533], [-33.371, -70.515], [-33.362, -70.485]],
      // Av. Apoquindo -> Camino El Alba
      [[-33.415, -70.595], [-33.408, -70.565], [-33.407, -70.541], [-33.404, -70.506]],
      // Av. La Dehesa -> Camino Los Trapenses
      [[-33.372, -70.519], [-33.357, -70.514], [-33.342, -70.513], [-33.328, -70.520], [-33.332, -70.543]],
      // Costanera Norte / Río Mapocho
      [[-33.405, -70.595], [-33.386, -70.560], [-33.372, -70.525], [-33.364, -70.495], [-33.358, -70.460]],
      // Av. Padre Hurtado / Manquehue
      [[-33.425, -70.550], [-33.407, -70.548], [-33.390, -70.546]],
      [[-33.425, -70.570], [-33.404, -70.568], [-33.388, -70.566]]
    ];

    // Map viewport state
    const mapState = {
      centerLat: -33.372,
      centerLon: -70.525,
      zoom: 1.0, // 1.0 fits [-33.425..-33.315]
      dragging: false,
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

      const styles = getComputedStyle(document.documentElement);
      const isLight = document.documentElement.classList.contains("light");
      const bg = isLight ? "#f1f5f9" : "#0b1220";
      const gridColor = isLight ? "rgba(15,23,42,0.06)" : "rgba(148,163,184,0.08)";
      const roadColor = isLight ? "rgba(100,116,139,0.35)" : "rgba(148,163,184,0.22)";
      const textMuted = isLight ? "#475569" : "#94a3b8";

      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);

      // Subtle lat/lon grid
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

      // Zone soft halos
      const drawZoneHalo = (lat, lon, label, color) => {
        const p = project(lat, lon);
        const r = 68 * mapState.zoom;
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.fillStyle = textMuted;
        ctx.font = "600 11px ui-sans-serif, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(label, p.x, p.y - r + 16);
      };
      drawZoneHalo(-33.346, -70.514, "LA DEHESA / LO BARNECHEA", "rgba(56, 189, 248, 0.05)");
      drawZoneHalo(-33.395, -70.542, "ALTO LAS CONDES / LAS CONDES", "rgba(129, 140, 248, 0.05)");

      // Roads
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

      // Landmarks
      LANDMARKS.forEach((lm) => {
        const p = project(lm.lat, lm.lon);
        ctx.fillStyle = "#fb7185";
        ctx.fillRect(p.x - 3.5, p.y - 3.5, 7, 7);
        ctx.fillStyle = textMuted;
        ctx.font = "500 10px ui-sans-serif, system-ui, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(lm.name, p.x + 6, p.y + 3);
      });

      // Property Pins
      const items = getFilteredListings();
      items.forEach((item) => {
        if (!item.lat || !item.lon) return;
        const p = project(item.lat, item.lon);
        const tr = getTrack(item.id);
        const isSel = item.id === mapState.selectedId;
        const isHov = item.id === mapState.hoveredId;

        let color = item.has_pool ? "#22d3ee" : "#818cf8";
        if (tr.status === "shortlist") color = "#fbbf24";
        if (tr.status === "visited") color = "#34d399";
        if (tr.status === "dismissed") color = "#64748b";

        const radius = isSel ? 9 : isHov ? 8 : 6;

        if (isSel || isHov) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, radius + 5, 0, Math.PI * 2);
          ctx.fillStyle = color + "40";
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = isSel ? 2.5 : 1.5;
        ctx.strokeStyle = isLight ? "#ffffff" : "#0f172a";
        ctx.stroke();

        // Show price pill when zoomed in or selected
        if (mapState.zoom >= 1.5 || isSel) {
          const lbl = fmtShortCLP(item.price_clp);
          ctx.font = "600 10px ui-monospace, monospace";
          const tw = ctx.measureText(lbl).width + 8;
          ctx.fillStyle = isLight ? "rgba(255,255,255,0.92)" : "rgba(15,23,42,0.9)";
          ctx.fillRect(p.x - tw / 2, p.y - radius - 18, tw, 14);
          ctx.fillStyle = isLight ? "#0f172a" : "#f8fafc";
          ctx.textAlign = "center";
          ctx.fillText(lbl, p.x, p.y - radius - 8);
        }
      });
    }

    function findPinAt(mx, my) {
      const items = getFilteredListings();
      let best = null;
      let bestDist = 14;
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

    // Canvas mouse/wheel interactions
    canvas.addEventListener("mousedown", (e) => {
      mapState.dragging = true;
      mapState.lastX = e.clientX;
      mapState.lastY = e.clientY;
    });
    window.addEventListener("mouseup", () => { mapState.dragging = false; });
    window.addEventListener("mousemove", (e) => {
      if (mapState.dragging) {
        const dx = e.clientX - mapState.lastX;
        const dy = e.clientY - mapState.lastY;
        mapState.lastX = e.clientX;
        mapState.lastY = e.clientY;
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        const baseScale = Math.min(w, h) * 8.2 * mapState.zoom;
        const cosLat = Math.cos((mapState.centerLat * Math.PI) / 180);
        mapState.centerLon -= dx / (cosLat * baseScale);
        mapState.centerLat += dy / baseScale;
        drawMap();
      }
    });

    canvas.addEventListener("mousemove", (e) => {
      if (mapState.dragging) return;
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = findPinAt(mx, my);
      const tt = document.getElementById("map-tooltip");
      if (hit) {
        mapState.hoveredId = hit.id;
        canvas.style.cursor = "pointer";
        tt.classList.remove("hidden");
        tt.style.left = Math.min(mx + 12, rect.width - 245) + "px";
        tt.style.top = Math.max(8, my - 10) + "px";
        tt.innerHTML = `
          <div class="font-semibold truncate">${hit.title}</div>
          <div class="text-[var(--muted-foreground,#94a3b8)] mt-0.5">
            ${fmtCLP(hit.price_clp)} (${hit.price_uf || "-"} UF) · ${hit.bedrooms}D / ${hit.bathrooms}B
            ${hit.has_pool ? " · <span class='text-cyan-400'>Pool</span>" : ""}
          </div>
        `;
      } else {
        mapState.hoveredId = null;
        canvas.style.cursor = "grab";
        tt.classList.add("hidden");
      }
      drawMap();
    });

    canvas.addEventListener("click", (e) => {
      const rect = canvas.getBoundingClientRect();
      const hit = findPinAt(e.clientX - rect.left, e.clientY - rect.top);
      if (hit) {
        selectProperty(hit.id);
      }
    });

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

    document.querySelectorAll(".jump-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const z = btn.dataset.jump;
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

    function renderInspector(item) {
      const box = document.getElementById("inspector");
      if (!item) {
        box.innerHTML = `<div class="text-[var(--muted-foreground,#94a3b8)] text-center py-4">Select a house on the map or list to inspect details.</div>`;
        return;
      }
      const tr = getTrack(item.id);
      const tags = [];
      if (item.has_pool) tags.push(`<span class="px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-400">Pool</span>`);
      if (item.has_quincho) tags.push(`<span class="px-2 py-0.5 rounded bg-orange-500/15 text-orange-400">Quincho</span>`);
      if (item.is_condominio) tags.push(`<span class="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400">Condominio</span>`);
      if (item.has_service_room) tags.push(`<span class="px-2 py-0.5 rounded bg-purple-500/15 text-purple-400">Service Room</span>`);
      if (item.is_furnished) tags.push(`<span class="px-2 py-0.5 rounded bg-pink-500/15 text-pink-400">Furnished</span>`);

      box.innerHTML = `
        <div class="flex flex-col sm:flex-row gap-3">
          ${item.image ? `<img src="${item.image}" alt="" class="w-full sm:w-36 h-28 object-cover rounded-lg bg-slate-800 shrink-0" />` : ""}
          <div class="flex-1 min-w-0 space-y-1.5">
            <div class="flex items-start justify-between gap-2">
              <div>
                <h2 class="text-sm font-semibold leading-snug">${item.title}</h2>
                <div class="text-[var(--muted-foreground,#94a3b8)]">${item.address} · ${item.source} (${item.agency})</div>
              </div>
              <div class="text-right shrink-0">
                <div class="text-sm font-bold tabular-nums text-[var(--primary,#60a5fa)]">${fmtCLP(item.price_clp)}</div>
                <div class="text-[var(--muted-foreground,#94a3b8)] tabular-nums">${item.price_uf || "-"} UF / mo</div>
              </div>
            </div>

            <div class="flex flex-wrap gap-3 py-1 border-y border-[var(--border,#334155)] tabular-nums">
              <span><strong>${item.bedrooms}</strong> Bedrooms</span>
              <span><strong>${item.bathrooms || "-"}</strong> Baths</span>
              <span><strong>~${item.estimated_rooms}</strong> Total Rooms</span>
              <span><strong>${item.built_m2 ? item.built_m2 + " m²" : "-"}</strong> Built</span>
              ${item.lot_m2 ? `<span><strong>${item.lot_m2} m²</strong> Lot</span>` : ""}
              ${item.parking_spaces ? `<span><strong>${item.parking_spaces}</strong> Parking</span>` : ""}
            </div>

            <div class="flex flex-wrap gap-1.5">${tags.join("")}</div>
            ${item.description_excerpt ? `<p class="text-[var(--muted-foreground,#94a3b8)] line-clamp-2">${item.description_excerpt}</p>` : ""}

            <div class="flex flex-wrap items-center gap-2 pt-1">
              <button onclick="setTrack('${item.id}', {status: '${tr.status === "shortlist" ? "none" : "shortlist"}'})"
                class="px-2.5 py-1 rounded-md border cursor-pointer ${tr.status === "shortlist" ? "bg-amber-500/20 border-amber-400 text-amber-300" : "border-[var(--border,#334155)] hover:opacity-80"}">
                ${tr.status === "shortlist" ? "★ Shortlisted" : "☆ Shortlist"}
              </button>
              <button onclick="setTrack('${item.id}', {status: '${tr.status === "visited" ? "none" : "visited"}'})"
                class="px-2.5 py-1 rounded-md border cursor-pointer ${tr.status === "visited" ? "bg-emerald-500/20 border-emerald-400 text-emerald-300" : "border-[var(--border,#334155)] hover:opacity-80"}">
                ${tr.status === "visited" ? "✓ Visited" : "Mark Visited"}
              </button>
              <button onclick="setTrack('${item.id}', {status: '${tr.status === "dismissed" ? "none" : "dismissed"}'})"
                class="px-2.5 py-1 rounded-md border cursor-pointer ${tr.status === "dismissed" ? "bg-rose-500/20 border-rose-400 text-rose-300" : "border-[var(--border,#334155)] hover:opacity-80"}">
                ${tr.status === "dismissed" ? "Restored" : "Dismiss"}
              </button>
              <a href="${item.url}" target="_blank" rel="noopener"
                class="ml-auto px-3 py-1 rounded-md bg-[var(--primary,#3b82f6)] text-white font-medium hover:opacity-90">
                Open Listing ↗
              </a>
            </div>

            <div class="pt-1">
              <input type="text" value="${(tr.note || "").replace(/"/g, "&quot;")}"
                placeholder="Add personal note (e.g., 'Contacted broker, visit Tuesday 10am')..."
                onchange="setTrack('${item.id}', {note: this.value})"
                class="w-full px-2.5 py-1.5 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-xs focus:outline-none focus:border-[var(--primary,#3b82f6)]" />
            </div>
          </div>
        </div>
      `;
    }

    function renderList() {
      const items = getFilteredListings();
      const container = document.getElementById("listing-cards");

      // KPIs
      document.getElementById("kpi-count").textContent = items.length;
      const avg = items.length ? items.reduce((s, x) => s + x.price_clp, 0) / items.length : 0;
      document.getElementById("kpi-avg").textContent = items.length ? fmtShortCLP(avg) : "-";
      document.getElementById("kpi-pool").textContent = items.filter((x) => x.has_pool).length;
      document.getElementById("kpi-shortlist").textContent = LISTINGS.filter((x) => getTrack(x.id).status === "shortlist").length;

      if (!items.length) {
        container.innerHTML = `<div class="p-6 text-center text-xs text-[var(--muted-foreground,#94a3b8)] rounded-xl bg-[var(--card,#1e293b)] border border-[var(--border,#334155)]">No houses match your current filters.</div>`;
        return;
      }

      container.innerHTML = items.map((item) => {
        const tr = getTrack(item.id);
        const isSel = item.id === mapState.selectedId;
        const borderCls = isSel
          ? "border-[var(--primary,#3b82f6)] ring-1 ring-[var(--primary,#3b82f6)]"
          : tr.status === "shortlist"
          ? "border-amber-500/60"
          : "border-[var(--border,#334155)]";

        return `
          <div onclick="selectProperty('${item.id}')"
            class="p-2.5 rounded-xl bg-[var(--card,#1e293b)] border ${borderCls} hover:opacity-95 cursor-pointer flex gap-2.5 text-xs transition">
            ${item.image ? `<img src="${item.image}" alt="" class="w-20 h-20 object-cover rounded-lg bg-slate-800 shrink-0" />` : `<div class="w-20 h-20 rounded-lg bg-slate-800 shrink-0 flex items-center justify-center text-[var(--muted-foreground,#94a3b8)]">No img</div>`}
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <div class="font-semibold truncate">${item.title}</div>
                <span class="font-bold tabular-nums shrink-0 text-[var(--primary,#60a5fa)]">${fmtShortCLP(item.price_clp)}</span>
              </div>
              <div class="text-[var(--muted-foreground,#94a3b8)] truncate mt-0.5">${item.zone_label} · ${item.source}</div>
              <div class="flex flex-wrap items-center gap-2 mt-1.5 tabular-nums">
                <span>${item.bedrooms}D</span>
                <span>${item.bathrooms || "-"}B</span>
                <span>~${item.estimated_rooms} rooms</span>
                ${item.built_m2 ? `<span>${item.built_m2} m²</span>` : ""}
                ${item.has_pool ? `<span class="px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-400">Pool</span>` : ""}
                ${tr.status === "shortlist" ? `<span class="text-amber-400">★</span>` : ""}
                ${tr.status === "visited" ? `<span class="text-emerald-400">✓</span>` : ""}
              </div>
              ${tr.note ? `<div class="mt-1 text-amber-300/90 truncate">Note: ${tr.note}</div>` : ""}
            </div>
          </div>
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

    // Wire filters
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
