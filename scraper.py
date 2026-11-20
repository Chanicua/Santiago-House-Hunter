#!/usr/bin/env python3
"""
Santiago House Hunter — Daily Scraper
Fetches 4-6 bedroom houses for rent (3M-5M CLP) in La Dehesa & Alto Las Condes / Las Condes
from TOCTOC and PortalInmobiliario, converts UF to CLP, geocodes addresses, and tracks history.
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = BASE_DIR / "config.json"
GEOCODE_CACHE_PATH = DATA_DIR / "geocode_cache.json"
HISTORY_PATH = DATA_DIR / "history.json"
LISTINGS_PATH = DATA_DIR / "listings.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Accurate sector centroids in Northeast Santiago for fallback geocoding
SECTOR_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "alto las condes": (-33.3905, -70.5465),
    "las tranqueras": (-33.3935, -70.5485),
    "estoril": (-33.3865, -70.5415),
    "san damián": (-33.3870, -70.5265),
    "san damian": (-33.3870, -70.5265),
    "mall sport": (-33.3805, -70.5335),
    "los dominicos": (-33.4055, -70.5385),
    "dominicos": (-33.4055, -70.5385),
    "san carlos de apoquindo": (-33.4040, -70.5060),
    "quinchamalí": (-33.3775, -70.5110),
    "quinchamali": (-33.3775, -70.5110),
    "el remanso": (-33.4135, -70.5220),
    "cerro apoquindo": (-33.4080, -70.5280),
    "vital apoquindo": (-33.4140, -70.5350),
    "kennedy": (-33.3945, -70.5560),
    "manquehue": (-33.4045, -70.5680),
    "hernando de magallanes": (-33.4090, -70.5580),
    "escuela militar": (-33.4140, -70.5830),
    "el golf": (-33.4150, -70.5940),
    "la dehesa": (-33.3480, -70.5140),
    "los trapenses": (-33.3325, -70.5430),
    "huinganal": (-33.3395, -70.4910),
    "lomas de la dehesa": (-33.3340, -70.5115),
    "golf lomas": (-33.3340, -70.5115),
    "valle la dehesa": (-33.3565, -70.5220),
    "los nogales": (-33.3440, -70.5060),
    "parque del sol": (-33.3375, -70.5015),
    "la ciénaga": (-33.3535, -70.5090),
    "la cienaga": (-33.3535, -70.5090),
    "valle escondido": (-33.3210, -70.5080),
    "pie andino": (-33.3360, -70.5310),
    "camino turístico": (-33.3520, -70.4940),
    "camino turistico": (-33.3520, -70.4940),
    "el arrayán": (-33.3580, -70.4670),
    "el arrayan": (-33.3580, -70.4670),
    "lo barnechea": (-33.3510, -70.5090),
    "las condes": (-33.4020, -70.5480),
}


def fetch_url(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def get_uf_value(fallback: float) -> float:
    try:
        raw = fetch_url("https://mindicador.cl/api/uf", timeout=8)
        data = json.loads(raw)
        serie = data.get("serie", [])
        if serie and "valor" in serie[0]:
            return float(serie[0]["valor"])
    except Exception as e:
        print(f"[WARN] Could not fetch live UF from mindicador.cl: {e}. Using fallback {fallback}")
    return fallback


def load_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def parse_number(text: str) -> Optional[float]:
    if not text:
        return None
    s = str(text).strip()
    # Handle Chilean number formatting: 3.500.000 or 183,50
    s = re.sub(r"[^\d,\.]", "", s)
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def extract_features(title: str, desc: str, bedrooms: int) -> Dict[str, Any]:
    blob = f"{title} {desc}".lower()

    has_pool = bool(re.search(r"\b(piscina|pileta|alberca)\b", blob))
    has_quincho = bool(re.search(r"\b(quincho|parrilla|barbacoa)\b", blob))
    has_service = bool(re.search(r"\b(servicio|servicios|pieza de servicio|dormitorio de servicio|logia)\b", blob))
    is_condominio = bool(re.search(r"\b(condominio|seguridad 24|port[oó]n|conserjer[ií]a)\b", blob))
    is_furnished = bool(re.search(r"\b(amoblad[oa]|full service|equipada)\b", blob))
    has_garden = bool(re.search(r"\b(jard[ií]n|patio|terraza)\b", blob))
    has_sala_estar = bool(re.search(r"\b(sala de estar|estar|playroom|family room)\b", blob))
    has_escritorio = bool(re.search(r"\b(escritorio|home office|oficina|estudio)\b", blob))

    # Estimate total rooms: bedrooms + living/dining (2) + estar + escritorio + servicio
    extra_rooms = 2  # living + comedor baseline
    if has_sala_estar:
        extra_rooms += 1
    if has_escritorio:
        extra_rooms += 1
    if has_service:
        extra_rooms += 1
    estimated_rooms = bedrooms + extra_rooms

    # Parking spaces
    parking = None
    m_est = re.search(r"(\d+)\s*(?:estac(?:ionamientos?)?|autos?|cocheras?)", blob)
    if m_est:
        parking = int(m_est.group(1))

    # Lot size m2
    lot_m2 = None
    m_lot = re.search(r"(\d[\d\.]*)\s*m2?\s*(?:de\s*)?(?:terreno|totales|parcela)", blob)
    if m_lot:
        lot_m2 = parse_number(m_lot.group(1))

    return {
        "has_pool": has_pool,
        "has_quincho": has_quincho,
        "has_service_room": has_service,
        "is_condominio": is_condominio,
        "is_furnished": is_furnished,
        "has_garden": has_garden,
        "has_sala_estar": has_sala_estar,
        "has_escritorio": has_escritorio,
        "estimated_rooms": estimated_rooms,
        "parking_spaces": parking,
        "lot_m2": lot_m2,
    }


def classify_zone(
    lat: Optional[float],
    lon: Optional[float],
    text_blob: str,
    default_zone: str,
    zones_cfg: Dict[str, Any],
) -> str:
    low = text_blob.lower()
    # Keyword match first for explicit neighborhood names
    for z_key, z_val in zones_cfg.items():
        for kw in z_val.get("keywords", []):
            if kw in low:
                return z_key
    # Bounding box check
    if lat is not None and lon is not None:
        for z_key, z_val in zones_cfg.items():
            bb = z_val["bbox"]
            if bb["lat_min"] <= lat <= bb["lat_max"] and bb["lon_min"] <= lon <= bb["lon_max"]:
                return z_key
    return default_zone


def geocode_address(
    address: str,
    zone_key: str,
    cache: Dict[str, List[float]],
    zones_cfg: Dict[str, Any],
    allow_nominatim: bool = True,
) -> Tuple[float, float, str]:
    """Returns (lat, lon, precision: 'exact' | 'geocoded' | 'sector')."""
    clean_addr = clean_text(address)
    # Remove noisy scientific-notation zip artifacts from PI addresses
    clean_addr = re.sub(r"\b\d+(?:\.\d+)?e\+\d+\s*-\s*\d+(?:\.\d+)?e\+\d+\b", "", clean_addr)
    clean_addr = re.sub(r"\s+", " ", clean_addr).strip(" ,")

    cache_key = clean_addr.lower()
    if cache_key in cache:
        lat, lon = cache[cache_key]
        return lat, lon, "geocoded"

    # Try Nominatim if address looks like a real street
    if allow_nominatim and clean_addr and len(clean_addr) > 8:
        try:
            q = f"{clean_addr}, Santiago, Chile"
            url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
                {"q": q, "format": "json", "limit": 1}
            )
            req = urllib.request.Request(url, headers={"User-Agent": "SantiagoHouseHunter/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                hits = json.loads(resp.read().decode("utf-8"))
                if hits:
                    lat = float(hits[0]["lat"])
                    lon = float(hits[0]["lon"])
                    # Sanity check: must be in Santiago metro area
                    if -33.65 <= lat <= -33.25 and -70.80 <= lon <= -70.35:
                        cache[cache_key] = [lat, lon]
                        time.sleep(0.35)
                        return lat, lon, "geocoded"
        except Exception:
            pass

    # Sector centroid fallback with deterministic micro-jitter so pins don't stack identically
    low = clean_addr.lower()
    for sector, (slat, slon) in SECTOR_CENTROIDS.items():
        if sector in low:
            h = abs(hash(clean_addr)) % 1000
            jlat = ((h % 31) - 15) * 0.00022
            jlon = (((h // 31) % 31) - 15) * 0.00025
            return round(slat + jlat, 6), round(slon + jlon, 6), "sector"

    center = zones_cfg[zone_key]["center"]
    h = abs(hash(clean_addr or zone_key)) % 1000
    jlat = ((h % 31) - 15) * 0.00035
    jlon = (((h // 31) % 31) - 15) * 0.00040
    return round(center[0] + jlat, 6), round(center[1] + jlon, 6), "sector"


def scrape_toctoc(source_cfg: Dict[str, Any], uf_clp: float, zones_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    base_url = source_cfg["url"]
    default_zone = source_cfg["default_zone"]
    max_pages = source_cfg.get("max_pages", 2)

    for page in range(1, max_pages + 1):
        url = base_url if page == 1 else f"{base_url}?pagina={page}"
        try:
            html = fetch_url(url)
        except Exception as e:
            print(f"[WARN] TOCTOC fetch failed ({url}): {e}")
            break

        m = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
        if not m:
            break
        try:
            data = json.loads(m.group(1))
            items = data["props"]["pageProps"]["propiedades"]["results"]
        except Exception as e:
            print(f"[WARN] TOCTOC JSON parse failed ({url}): {e}")
            break

        if not items:
            break

        for item in items:
            try:
                beds_list = item.get("dormitorios") or []
                baths_list = item.get("bannos") or []
                surf_list = item.get("superficie") or []
                beds = int(parse_number(beds_list[0]) or 0) if beds_list else 0
                baths = int(parse_number(baths_list[0]) or 0) if baths_list else 0
                built_m2 = parse_number(surf_list[0]) if surf_list else None
                if built_m2 is not None and built_m2 < 20:
                    built_m2 = None  # ignore malformed data like "2,16 m2"

                price_clp = None
                price_uf = None
                for p in item.get("precios", []):
                    prefix = (p.get("prefix") or "").strip()
                    val = parse_number(p.get("value"))
                    if val is None:
                        continue
                    if prefix == "UF":
                        price_uf = val
                    elif prefix == "$":
                        price_clp = val

                if price_clp is None and price_uf is not None:
                    price_clp = round(price_uf * uf_clp)
                if price_uf is None and price_clp is not None:
                    price_uf = round(price_clp / uf_clp, 1)

                if price_clp is None:
                    continue

                title = clean_text(item.get("titulo", ""))
                desc = clean_text(item.get("description", ""))
                comuna = clean_text(item.get("comuna", ""))
                lat = item.get("latitud")
                lon = item.get("longitud")
                lat = float(lat) if lat is not None else None
                lon = float(lon) if lon is not None else None

                zone = classify_zone(lat, lon, f"{title} {desc} {comuna}", default_zone, zones_cfg)
                feats = extract_features(title, desc, beds)

                horas = item.get("horasPublicado")
                published_ago = None
                if isinstance(horas, (int, float)):
                    if horas < 24:
                        published_ago = f"Hace {int(horas)}h"
                    else:
                        published_ago = f"Hace {int(horas // 24)}d"

                agency = (item.get("imagenInmobiliaria") or {}).get("alt") or "Corredora"
                img = (item.get("imagenPrincipal") or {}).get("src") or ""
                prop_url = item.get("urlFicha") or ""
                pid = f"toctoc_{item.get('hashId') or item.get('idProperty')}"

                results.append(
                    {
                        "id": pid,
                        "source": "TOCTOC",
                        "title": title,
                        "url": prop_url,
                        "image": img,
                        "agency": agency,
                        "comuna": comuna,
                        "address": f"{comuna}, Santiago",
                        "zone": zone,
                        "zone_label": zones_cfg[zone]["label"],
                        "price_clp": int(round(price_clp)),
                        "price_uf": round(float(price_uf), 1) if price_uf else None,
                        "bedrooms": beds,
                        "bathrooms": baths,
                        "built_m2": built_m2,
                        "lat": lat,
                        "lon": lon,
                        "coord_precision": "exact" if (lat and lon) else "sector",
                        "published_ago": published_ago,
                        "description_excerpt": desc[:320] + ("..." if len(desc) > 320 else ""),
                        **feats,
                    }
                )
            except Exception:
                continue

        print(f"[INFO] TOCTOC {url} -> {len(items)} raw items")
    return results


def _collect_polycards(node: Any, out: List[Dict[str, Any]]) -> None:
    if isinstance(node, dict):
        if "polycard" in node and isinstance(node["polycard"], dict):
            out.append(node["polycard"])
        else:
            for v in node.values():
                if isinstance(v, (dict, list)):
                    _collect_polycards(v, out)
    elif isinstance(node, list):
        for item in node:
            if isinstance(item, (dict, list)):
                _collect_polycards(item, out)


def _extract_polycards(html: str) -> List[Dict[str, Any]]:
    decoder = json.JSONDecoder()
    polycards: List[Dict[str, Any]] = []
    for pat in (r"_n\.ctx\.r\s*=\s*(\{)", r"__PRELOADED_STATE__\s*=\s*(\{)"):
        for m in re.finditer(pat, html):
            try:
                obj, _ = decoder.raw_decode(html[m.start(1):])
                _collect_polycards(obj, polycards)
            except Exception:
                continue
        if polycards:
            return polycards
    return polycards


def scrape_portalinmobiliario(
    source_cfg: Dict[str, Any],
    uf_clp: float,
    zones_cfg: Dict[str, Any],
    geo_cache: Dict[str, List[float]],
    source_name: str = "PortalInmobiliario",
    id_prefix: str = "pi",
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    base_url = source_cfg["url"]
    default_zone = source_cfg["default_zone"]
    max_pages = source_cfg.get("max_pages", 2)

    for page in range(1, max_pages + 1):
        if page == 1:
            url = base_url
        else:
            offset = (page - 1) * 48 + 1
            url = f"{base_url}/_Desde_{offset}_NoIndex_True"

        try:
            html = fetch_url(url)
        except Exception as e:
            print(f"[WARN] {source_name} fetch failed ({url}): {e}")
            break

        polycards = _extract_polycards(html)
        if not polycards:
            t_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
            page_title = clean_text(t_m.group(1)) if t_m else "unknown"
            print(f"[WARN] {source_name} no polycards found ({url}) [len={len(html)}, title={page_title!r}]")
            break

        print(f"[INFO] {source_name} {url} -> {len(polycards)} raw items")

        for pc in polycards:
            try:
                meta = pc.get("metadata", {})
                comps = {c.get("id"): c for c in pc.get("components", []) if c.get("id")}

                title = clean_text(((comps.get("title") or {}).get("title") or {}).get("text", ""))
                loc_text = clean_text(((comps.get("location") or {}).get("location") or {}).get("text", ""))

                price_obj = ((comps.get("price") or {}).get("price") or {}).get("current_price") or {}
                pval = price_obj.get("value")
                pcurr = price_obj.get("currency", "CLP")
                if pval is None:
                    continue

                if pcurr == "CLF":
                    price_uf = float(pval)
                    price_clp = round(price_uf * uf_clp)
                else:
                    price_clp = float(pval)
                    price_uf = round(price_clp / uf_clp, 1)

                attrs = ((comps.get("attributes_list") or {}).get("attributes_list") or {}).get("texts") or []
                beds = 0
                baths = 0
                built_m2 = None
                for a in attrs:
                    al = a.lower()
                    if "dormitorio" in al:
                        beds = int(parse_number(al) or 0)
                    elif "baño" in al:
                        baths = int(parse_number(al) or 0)
                    elif "m²" in al or "m2" in al:
                        built_m2 = parse_number(al)

                zone = classify_zone(None, None, f"{title} {loc_text}", default_zone, zones_cfg)
                clean_addr = re.sub(r"\b\d+(?:\.\d+)?e\+\d+\s*-\s*\d+(?:\.\d+)?e\+\d+\b", "", loc_text).strip()
                lat, lon, precision = geocode_address(clean_addr or title, zone, geo_cache, zones_cfg, allow_nominatim=True)
                feats = extract_features(title, loc_text, beds)

                pics = (pc.get("pictures") or {}).get("pictures") or []
                img = f"https://http2.mlstatic.com/D_NQ_NP_2X_{pics[0]['id']}-N.webp" if pics else ""
                raw_url = meta.get("url", "")
                prop_url = f"https://{raw_url}" if raw_url and not raw_url.startswith("http") else raw_url
                pid = f"{id_prefix}_{meta.get('id', abs(hash(title + loc_text)))}"

                comuna = "Lo Barnechea" if zone == "la_dehesa" else "Las Condes"

                results.append(
                    {
                        "id": pid,
                        "source": source_name,
                        "title": title,
                        "url": prop_url,
                        "image": img,
                        "agency": source_name,
                        "comuna": comuna,
                        "address": clean_addr,
                        "zone": zone,
                        "zone_label": zones_cfg[zone]["label"],
                        "price_clp": int(round(price_clp)),
                        "price_uf": round(float(price_uf), 1),
                        "bedrooms": beds,
                        "bathrooms": baths,
                        "built_m2": built_m2,
                        "lat": lat,
                        "lon": lon,
                        "coord_precision": precision,
                        "published_ago": None,
                        "description_excerpt": loc_text,
                        **feats,
                    }
                )
            except Exception:
                continue

        print(f"[INFO] PortalInmobiliario {url} -> {len(polycards)} raw items")
    return results


def filter_and_dedupe(listings: List[Dict[str, Any]], search_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    min_b = search_cfg["min_bedrooms"]
    max_b = search_cfg["max_bedrooms"]
    min_p = search_cfg["min_price_clp"]
    max_p = search_cfg["max_price_clp"]

    filtered: List[Dict[str, Any]] = []
    seen_keys = set()

    # Prefer TOCTOC first (has exact coords + full description)
    ordered = sorted(listings, key=lambda x: (0 if x["source"] == "TOCTOC" else 1, x["price_clp"]))

    for item in ordered:
        beds = item.get("bedrooms", 0)
        price = item.get("price_clp", 0)
        if not (min_b <= beds <= max_b):
            continue
        if not (min_p <= price <= max_p):
            continue
        # Exclude commercial-only properties
        if re.search(r"\b(comercial|oficina|jard[ií]n infantil|educaci[oó]n)\b", item["title"].lower()):
            continue

        # Deduplicate by normalized title + bedrooms + rounded price (within 50k)
        norm_title = re.sub(r"[^a-z0-9]", "", item["title"].lower())[:28]
        dedupe_key = (norm_title, beds, round(price / 50000))
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        filtered.append(item)

    return filtered


def update_history(listings: List[Dict[str, Any]], history: Dict[str, Any], today_str: str) -> List[Dict[str, Any]]:
    active_ids = set()
    enriched: List[Dict[str, Any]] = []

    for item in listings:
        lid = item["id"]
        active_ids.add(lid)
        price = item["price_clp"]

        if lid not in history:
            history[lid] = {
                "first_seen": today_str,
                "last_seen": today_str,
                "price_history": [{"date": today_str, "price_clp": price}],
                "title": item["title"],
                "url": item["url"],
            }
            status = "new"
            price_delta = 0
        else:
            rec = history[lid]
            rec["last_seen"] = today_str
            prev_price = rec["price_history"][-1]["price_clp"]
            price_delta = price - prev_price
            if price != prev_price:
                rec["price_history"].append({"date": today_str, "price_clp": price})
                status = "price_drop" if price < prev_price else "price_up"
            else:
                status = "new" if rec["first_seen"] == today_str else "active"

        item["first_seen"] = history[lid]["first_seen"]
        item["last_seen"] = today_str
        item["status"] = status
        item["price_delta"] = price_delta
        enriched.append(item)

    return enriched


def main() -> None:
    cfg = load_json(CONFIG_PATH, {})
    search_cfg = cfg["search"]
    zones_cfg = cfg["zones"]
    sources_cfg = cfg["sources"]

    uf_clp = get_uf_value(search_cfg["fallback_uf_clp"])
    print(f"[INFO] Live UF rate: ${uf_clp:,.2f} CLP")

    geo_cache = load_json(GEOCODE_CACHE_PATH, {})
    history = load_json(HISTORY_PATH, {})
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    raw_listings: List[Dict[str, Any]] = []
    for src in sources_cfg.get("toctoc", []):
        raw_listings.extend(scrape_toctoc(src, uf_clp, zones_cfg))
    for src in sources_cfg.get("portalinmobiliario", []):
        raw_listings.extend(scrape_portalinmobiliario(src, uf_clp, zones_cfg, geo_cache, "PortalInmobiliario", "pi"))
    for src in sources_cfg.get("mercadolibre", []):
        raw_listings.extend(scrape_portalinmobiliario(src, uf_clp, zones_cfg, geo_cache, "MercadoLibre", "ml"))

    save_json(GEOCODE_CACHE_PATH, geo_cache)

    filtered = filter_and_dedupe(raw_listings, search_cfg)
    enriched = update_history(filtered, history, today_str)
    save_json(HISTORY_PATH, history)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "uf_clp": uf_clp,
        "criteria": search_cfg,
        "count": len(enriched),
        "listings": enriched,
    }
    save_json(LISTINGS_PATH, payload)
    print(f"[DONE] Saved {len(enriched)} matching houses to {LISTINGS_PATH}")


if __name__ == "__main__":
    main()
