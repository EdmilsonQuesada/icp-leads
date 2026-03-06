import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook
from app.db.session import get_db
from app.models.lead import Lead

router = APIRouter(prefix="/export", tags=["export"])

EXPORT_FIELDS = [
    "id", "username", "platform", "display_name", "profile_url",
    "score", "category", "status", "city", "country",
    "age", "birthdate", "birthdate_source",
    "followers", "bio", "created_at", "last_monitored_at", "contacted_at",
]

def _lead_to_row(lead: Lead) -> list:
    return [
        lead.id, lead.username,
        lead.platform.value if lead.platform else "",
        lead.display_name or "", lead.profile_url or "",
        lead.score, lead.category.value if lead.category else "",
        lead.status.value if lead.status else "",
        lead.city or "", lead.country or "",
        lead.age, str(lead.birthdate) if lead.birthdate else "",
        lead.birthdate_source or "",
        lead.followers, lead.bio or "",
        str(lead.created_at) if lead.created_at else "",
        str(lead.last_monitored_at) if lead.last_monitored_at else "",
        str(lead.contacted_at) if lead.contacted_at else "",
    ]

@router.get("/csv")
def export_csv(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.score.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(EXPORT_FIELDS)
    for lead in leads:
        writer.writerow(_lead_to_row(lead))
    output.seek(0)
    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@router.get("/excel")
def export_excel(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.score.desc()).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"
    ws.append(EXPORT_FIELDS)
    for lead in leads:
        ws.append(_lead_to_row(lead))
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
