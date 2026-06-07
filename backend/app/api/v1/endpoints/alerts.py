from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import Alert
from app.schemas.responses import AlertSchema

router = APIRouter()


@router.get("/active", response_model=list[AlertSchema])
async def active_alerts(db: Session = Depends(get_db)):
    rows = (
        db.query(Alert)
        .filter(Alert.dismissed == False)  # noqa: E712
        .order_by(Alert.created_at.desc())
        .all()
    )
    return [AlertSchema.model_validate(a) for a in rows]


@router.post("/{alert_id}/dismiss")
async def dismiss_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.dismissed = True
    db.commit()
    return {"dismissed": True}
