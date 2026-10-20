"""Akses Sentinel-2 L2A COG publik di AWS (bucket `sentinel-cogs`, tanpa autentikasi). Dibuat tipis agar mudah dibuktikan.

Sumber: https://registry.opendata.aws/sentinel-2-l2a-cogs/ (Element 84; data Copernicus Sentinel, ESA). Periksa syarat
penggunaan Copernicus. Katalog STAC (earth-search) tidak dipakai karena tidak dapat dijangkau dari lingkungan pengembangan;
daftar scene diambil dari listing S3 dan metadata item JSON.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np

BUCKET = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/"
PREFIX = "sentinel-s2-l2a-cogs"
TIMEOUT = 40


@dataclass(frozen=True)
class Scene:
    scene_id: str
    acquired: date
    cloud_cover_pct: float
    base_url: str   # URL folder scene, diakhiri '/'

    def asset(self, band: str) -> str:
        return f"{self.base_url}{band}.tif"


def _list_prefixes(prefix: str) -> list[str]:
    found: list[str] = []
    token = None
    while True:
        url = f"{BUCKET}?list-type=2&delimiter=/&prefix={prefix}" + (f"&continuation-token={urllib.parse.quote(token)}" if token else "")
        body = urllib.request.urlopen(url, timeout=TIMEOUT).read().decode()
        found += re.findall(r"<Prefix>([^<]+)</Prefix>", body)[1:]  # elemen pertama = prefix kueri itu sendiri
        m = re.search(r"<NextContinuationToken>([^<]+)", body)
        token = m.group(1) if m else None
        if not token:
            return found


def parse_tile(tile: str) -> str:
    """'50MMD' atau '50/M/MD' -> '50/M/MD'."""
    t = tile.strip().upper().replace("/", "")
    m = re.fullmatch(r"(\d{1,2})([C-X])([A-Z]{2})", t)
    if not m:
        raise ValueError(f"Kode tile MGRS tidak valid: {tile!r} (contoh: 50MMD)")
    return f"{int(m.group(1))}/{m.group(2)}/{m.group(3)}"


def month_range(start: date, end: date) -> list[tuple[int, int]]:
    if start > end:
        raise ValueError("Tanggal awal harus sebelum tanggal akhir.")
    out, y, mo = [], start.year, start.month
    while (y, mo) <= (end.year, end.month):
        out.append((y, mo))
        y, mo = (y + 1, 1) if mo == 12 else (y, mo + 1)
    return out


def _item(item_prefix: str) -> Scene | None:
    sid = item_prefix.rstrip("/").split("/")[-1]
    try:
        meta: dict[str, Any] = json.load(urllib.request.urlopen(f"{BUCKET}{item_prefix}{sid}.json", timeout=TIMEOUT))
        acquired = date.fromisoformat(meta["properties"]["datetime"][:10])
        return Scene(sid, acquired, float(meta["properties"]["eo:cloud_cover"]), BUCKET + item_prefix)
    except Exception:  # noqa: BLE001 - scene tanpa metadata dilewati, bukan menggagalkan semuanya
        return None


def list_scenes(tile: str, start: date, end: date) -> list[Scene]:
    """Semua scene pada tile dalam rentang tanggal [start, end], terurut tanggal."""
    t = parse_tile(tile)
    prefixes: list[str] = []
    for y, mo in month_range(start, end):
        prefixes += _list_prefixes(f"{PREFIX}/{t}/{y}/{mo}/")
    with ThreadPoolExecutor(max_workers=8) as pool:
        scenes = [s for s in pool.map(_item, prefixes) if s]
    return sorted((s for s in scenes if start <= s.acquired <= end), key=lambda s: (s.acquired, s.scene_id))


def pick_scenes(scenes: list[Scene], n: int, max_cloud: float = 80.0) -> list[Scene]:
    """Pilih n scene berawan paling sedikit (cloud cover tingkat tile) di bawah batas; satu per tanggal akuisisi."""
    best: dict[date, Scene] = {}
    for s in scenes:
        if s.cloud_cover_pct <= max_cloud and (s.acquired not in best or s.cloud_cover_pct < best[s.acquired].cloud_cover_pct):
            best[s.acquired] = s
    return sorted(best.values(), key=lambda s: s.cloud_cover_pct)[:n]


def read_aoi(scene: Scene, bounds_utm: tuple[float, float, float, float], pixel_m: float = 20.0) -> tuple[dict[str, np.ndarray], np.ndarray, Any]:
    """Baca B04, B08, B12, SCL untuk AOI pada grid seragam ``pixel_m``. Kembalikan (band DN, SCL, transform affine)."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.windows import from_bounds

    minx, miny, maxx, maxy = bounds_utm
    width, height = int(round((maxx - minx) / pixel_m)), int(round((maxy - miny) / pixel_m))
    if width < 2 or height < 2:
        raise ValueError("AOI terlalu kecil.")
    transform = from_origin(minx, maxy, pixel_m, pixel_m)
    bands: dict[str, np.ndarray] = {}
    scl = None
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", GDAL_HTTP_MAX_RETRY="3"):
        for name in ("B04", "B08", "B12", "SCL"):
            with rasterio.open(scene.asset(name)) as ds:
                window = from_bounds(minx, miny, maxx, maxy, ds.transform)
                resampling = Resampling.nearest if name == "SCL" else Resampling.average
                data = ds.read(1, window=window, out_shape=(height, width), resampling=resampling, boundless=True, fill_value=0)
            if name == "SCL":
                scl = data.astype("uint8")
            else:
                bands[name] = data.astype("float32")
    return bands, scl, transform
