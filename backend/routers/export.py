"""Ekspor data hasil analisis (CSV) dan laporan ringkas (PDF) dengan filter yang sama seperti peta dan dashboard."""
from __future__ import annotations

import csv
import io
from collections import Counter
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from models.disturbance import ForestDisturbance
from routers.dashboard import filtered_query

router = APIRouter(prefix="/export", tags=["export"])

COLUMNS = ["id", "region", "province", "centroid_lat", "centroid_lon", "area_ha", "detected_date", "period_start", "period_end",
           "category_prediksi_model", "confidence_score", "confidence_level", "verified_category", "is_validated",
           "ndvi_before", "ndvi_after", "ndvi_change", "data_source"]

DISCLAIMER = ("Indikasi perubahan dan prediksi kategori bukan bukti penyebab deforestasi dan belum menggantikan verifikasi "
              "lapangan. Data bersumber 'simulasi' adalah data buatan, bukan citra nyata.")


def _filters(date_from, date_to, categories, provinces, min_confidence, source):
    return dict(date_from=date_from, date_to=date_to, categories=categories, provinces=provinces,
                min_confidence=min_confidence, source=source)


@router.get("/disturbances.csv")
def export_csv(date_from: Optional[datetime] = Query(None), date_to: Optional[datetime] = Query(None),
               categories: Optional[str] = Query(None), provinces: Optional[str] = Query(None),
               min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0), source: Optional[str] = Query(None),
               db: Session = Depends(get_db)):
    rows = filtered_query(db, **_filters(date_from, date_to, categories, provinces, min_confidence, source)).order_by(ForestDisturbance.id).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(COLUMNS)
    for d in rows:
        writer.writerow([d.id, d.region, d.province, d.centroid_lat, d.centroid_lon, d.area_ha,
                         d.detected_date.isoformat() if d.detected_date else "", d.period_start.isoformat() if d.period_start else "",
                         d.period_end.isoformat() if d.period_end else "", d.category, d.confidence_score, d.confidence_level,
                         d.verified_category or "", bool(d.is_validated), d.ndvi_before, d.ndvi_after, d.ndvi_change, d.data_source])
    return Response(buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=forestwatch_indikasi.csv"})


@router.get("/report.pdf")
def export_pdf(date_from: Optional[datetime] = Query(None), date_to: Optional[datetime] = Query(None),
               categories: Optional[str] = Query(None), provinces: Optional[str] = Query(None),
               min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0), source: Optional[str] = Query(None),
               db: Session = Depends(get_db)):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    f = _filters(date_from, date_to, categories, provinces, min_confidence, source)
    rows = filtered_query(db, **f).all()
    st = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Laporan ForestWatch AI")
    flow = [Paragraph("Laporan ForestWatch AI", st["Title"]), Paragraph(DISCLAIMER, st["BodyText"]), Spacer(1, 8),
            Paragraph("Filter aktif", st["Heading2"])]
    active = {k: v for k, v in f.items() if v}
    flow.append(Paragraph(", ".join(f"{k}={v}" for k, v in active.items()) or "tanpa filter (semua data)", st["BodyText"]))
    real = sum(1 for d in rows if (d.data_source or "").startswith("Sentinel-2 L2A COG (citra nyata)"))
    flow += [Paragraph("Ringkasan", st["Heading2"]),
             Paragraph(f"Jumlah indikasi: {len(rows)} (citra nyata: {real}; simulasi: {len(rows) - real}). "
                       f"Total luas: {sum(d.area_ha or 0 for d in rows):,.1f} ha. "
                       f"Diverifikasi operator: {sum(1 for d in rows if d.is_validated)}.", st["BodyText"])]
    counts = Counter(d.category for d in rows)
    table = Table([["Kategori (prediksi model)", "Jumlah"]] + [[k, str(v)] for k, v in counts.most_common()] or [["-", "0"]])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)]))
    flow += [Paragraph("Distribusi kategori", st["Heading2"]), table, Paragraph("Keterbatasan", st["Heading2"])]
    for text in ("Kategori adalah keluaran model yang dilatih pada data SINTETIS; tidak berlaku sebagai bukti penyebab.",
                 "Indikasi dari citra nyata belum diklasifikasi penyebabnya (kategori 'tidak_diketahui').",
                 "Belum ada validasi independen/lapangan skala besar; skor keyakinan bukan probabilitas terkalibrasi."):
        flow.append(Paragraph(f"- {text}", st["BodyText"]))
    doc.build(flow)
    return Response(buf.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=forestwatch_laporan.pdf"})
