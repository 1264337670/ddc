from datetime import date, datetime
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Mentor, MentorAppointment, MentorSchedule, User
from app.db.schemas import MentorAppointmentCreateRequest, MentorAppointmentPublic, MentorPublic, MentorSlotPublic

router = APIRouter(prefix="/api/mentor", tags=["mentor"])
oauth2_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

TIME_SLOTS = ["8:00-9:30", "10:00-11:30", "14:00-15:30", "16:00-17:30"]
MAX_SLOT_CAPACITY = 5


def _datetime_to_text(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _date_text(value: date) -> str:
    return "{}月{}日".format(value.month, value.day)


def _get_optional_user(db: Session, token: Optional[str]) -> Optional[User]:
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        account = payload.get("sub")
        if not isinstance(account, str) or not account:
            return None
    except JWTError:
        return None

    stmt = select(User).where(User.account == account, User.is_active == True)  # noqa: E712
    return db.execute(stmt).scalar_one_or_none()


def _get_required_user(db: Session, token: Optional[str]) -> User:
    user = _get_optional_user(db, token)
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


@router.get("/slots", response_model=List[MentorSlotPublic])
def list_mentor_slots(
    date_value: Optional[date] = None,
    name: str = "",
    location: str = "",
    token: Optional[str] = Depends(oauth2_optional),
    db: Session = Depends(get_db),
) -> List[MentorSlotPublic]:
    current_user = _get_optional_user(db, token)

    stmt = select(Mentor).where(Mentor.is_active == True)  # noqa: E712
    if name.strip():
        stmt = stmt.where(Mentor.name.like("%{}%".format(name.strip())))
    if location.strip():
        stmt = stmt.where(Mentor.location.like("%{}%".format(location.strip())))

    mentors = list(db.execute(stmt.order_by(Mentor.id.asc())).scalars().all())
    if not mentors:
        return []

    mentor_ids = [item.id for item in mentors]

    schedule_stmt = select(MentorSchedule).where(
        MentorSchedule.mentor_id.in_(mentor_ids),
        MentorSchedule.is_active == True,  # noqa: E712
    )
    if date_value is not None:
        schedule_stmt = schedule_stmt.where(MentorSchedule.schedule_date == date_value)

    schedules = list(
        db.execute(
            schedule_stmt.order_by(MentorSchedule.schedule_date.asc(), MentorSchedule.time_slot.asc(), MentorSchedule.mentor_id.asc())
        ).scalars().all()
    )
    if not schedules:
        return []

    schedule_keys = {(item.mentor_id, item.schedule_date, item.time_slot) for item in schedules}

    appointments = list(
        db.execute(
            select(MentorAppointment).where(
                MentorAppointment.mentor_id.in_(mentor_ids),
                MentorAppointment.status == "booked",
            )
        ).scalars().all()
    )

    count_map: Dict[str, int] = {}
    my_slot_set: Set[str] = set()

    for item in appointments:
        if (item.mentor_id, item.appointment_date, item.time_slot) not in schedule_keys:
            continue
        key = "{}|{}|{}".format(item.mentor_id, item.appointment_date.isoformat(), item.time_slot)
        count_map[key] = count_map.get(key, 0) + 1
        if current_user and item.user_id == current_user.id:
            my_slot_set.add(key)

    mentor_map = {item.id: item for item in mentors}

    result: List[MentorSlotPublic] = []
    for schedule in schedules:
        mentor = mentor_map.get(schedule.mentor_id)
        if mentor is None:
            continue
        key = "{}|{}|{}".format(schedule.mentor_id, schedule.schedule_date.isoformat(), schedule.time_slot)
        result.append(
            MentorSlotPublic(
                slot_id="{}|{}|{}".format(mentor.id, schedule.schedule_date.isoformat(), schedule.time_slot),
                mentor_id=mentor.id,
                teacher=mentor.name,
                date_text=_date_text(schedule.schedule_date),
                date_iso=schedule.schedule_date.isoformat(),
                time=schedule.time_slot,
                location=mentor.location,
                intro=mentor.intro,
                avatar=mentor.avatar,
                booked=count_map.get(key, 0),
                reserved_by_me=key in my_slot_set,
            )
        )

    return result


@router.get("/search", response_model=List[MentorPublic])
def search_mentors(
    name: str = "",
    location: str = "",
    db: Session = Depends(get_db),
) -> List[MentorPublic]:
    stmt = select(Mentor).where(Mentor.is_active == True)  # noqa: E712
    if name.strip():
        stmt = stmt.where(Mentor.name.like("%{}%".format(name.strip())))
    if location.strip():
        stmt = stmt.where(Mentor.location.like("%{}%".format(location.strip())))

    mentors = list(db.execute(stmt.order_by(Mentor.id.asc())).scalars().all())
    return [
        MentorPublic(
            mentor_id=item.id,
            teacher=item.name,
            location=item.location,
            intro=item.intro,
            avatar=item.avatar,
        )
        for item in mentors
    ]


@router.post("/appointments", response_model=MentorAppointmentPublic)
def create_appointment(
    payload: MentorAppointmentCreateRequest,
    token: Optional[str] = Depends(oauth2_optional),
    db: Session = Depends(get_db),
) -> MentorAppointmentPublic:
    user = _get_required_user(db, token)

    if payload.time_slot not in TIME_SLOTS:
        raise HTTPException(status_code=400, detail="非法时段")

    mentor = db.execute(
        select(Mentor).where(Mentor.id == payload.mentor_id, Mentor.is_active == True)  # noqa: E712
    ).scalar_one_or_none()
    if mentor is None:
        raise HTTPException(status_code=404, detail="导师不存在")

    schedule = db.execute(
        select(MentorSchedule).where(
            MentorSchedule.mentor_id == payload.mentor_id,
            MentorSchedule.schedule_date == payload.appointment_date,
            MentorSchedule.time_slot == payload.time_slot,
            MentorSchedule.is_active == True,  # noqa: E712
        )
    ).scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=400, detail="该导师在当天该时段暂无排班")

    exists = db.execute(
        select(MentorAppointment).where(
            MentorAppointment.mentor_id == payload.mentor_id,
            MentorAppointment.user_id == user.id,
            MentorAppointment.appointment_date == payload.appointment_date,
            MentorAppointment.time_slot == payload.time_slot,
            MentorAppointment.status == "booked",
        )
    ).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=400, detail="你已预约该时段")

    booked_count = (
        db.execute(
            select(func.count(MentorAppointment.id)).where(
                MentorAppointment.mentor_id == payload.mentor_id,
                MentorAppointment.appointment_date == payload.appointment_date,
                MentorAppointment.time_slot == payload.time_slot,
                MentorAppointment.status == "booked",
            )
        ).scalar_one()
        or 0
    )
    capacity = schedule.capacity if schedule.capacity and schedule.capacity > 0 else MAX_SLOT_CAPACITY
    if booked_count >= capacity:
        raise HTTPException(status_code=400, detail="该时段已满额")

    appointment = MentorAppointment(
        mentor_id=payload.mentor_id,
        user_id=user.id,
        appointment_date=payload.appointment_date,
        time_slot=payload.time_slot,
        status="booked",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return MentorAppointmentPublic(
        id=appointment.id,
        mentor_id=mentor.id,
        teacher=mentor.name,
        date_text=_date_text(appointment.appointment_date),
        date_iso=appointment.appointment_date.isoformat(),
        time=appointment.time_slot,
        location=mentor.location,
        intro=mentor.intro,
        avatar=mentor.avatar,
        created_at=_datetime_to_text(appointment.created_at),
    )


@router.get("/appointments/me", response_model=List[MentorAppointmentPublic])
def list_my_appointments(
    token: Optional[str] = Depends(oauth2_optional),
    db: Session = Depends(get_db),
) -> List[MentorAppointmentPublic]:
    user = _get_required_user(db, token)

    stmt = (
        select(MentorAppointment, Mentor)
        .join(Mentor, Mentor.id == MentorAppointment.mentor_id)
        .where(
            and_(
                MentorAppointment.user_id == user.id,
                MentorAppointment.status == "booked",
            )
        )
        .order_by(MentorAppointment.appointment_date.desc(), MentorAppointment.time_slot.asc())
    )

    rows = db.execute(stmt).all()
    result: List[MentorAppointmentPublic] = []
    for appointment, mentor in rows:
        result.append(
            MentorAppointmentPublic(
                id=appointment.id,
                mentor_id=mentor.id,
                teacher=mentor.name,
                date_text=_date_text(appointment.appointment_date),
                date_iso=appointment.appointment_date.isoformat(),
                time=appointment.time_slot,
                location=mentor.location,
                intro=mentor.intro,
                avatar=mentor.avatar,
                created_at=_datetime_to_text(appointment.created_at),
            )
        )

    return result


@router.delete("/appointments/{appointment_id}")
def cancel_my_appointment(
    appointment_id: int,
    token: Optional[str] = Depends(oauth2_optional),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    user = _get_required_user(db, token)

    appointment = db.execute(
        select(MentorAppointment).where(
            MentorAppointment.id == appointment_id,
            MentorAppointment.user_id == user.id,
            MentorAppointment.status == "booked",
        )
    ).scalar_one_or_none()
    if appointment is None:
        raise HTTPException(status_code=404, detail="预约不存在或已取消")

    appointment.status = "canceled"
    db.add(appointment)
    db.commit()

    return {"detail": "取消预约成功"}
