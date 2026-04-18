from datetime import datetime, date
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Mentor, MentorSchedule, TreeComment, TreePost, User
from app.db.schemas import (
    AdminMentorCreateRequest,
    AdminMentorItem,
    AdminMentorUpdateRequest,
    AdminScheduleCreateRequest,
    AdminScheduleItem,
    AdminScheduleUpdateRequest,
    AdminStatusUpdateRequest,
    AdminTreeCommentItem,
    AdminTreePostItem,
    AdminXhsAuditItem,
    AdminXhsAuditUpdateRequest,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


TIME_SLOTS = {"8:00-9:30", "10:00-11:30", "14:00-15:30", "16:00-17:30"}


def _datetime_to_text(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _require_admin(current_user: User) -> None:
    if (current_user.role or "user") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.get("/mentors", response_model=List[AdminMentorItem])
def admin_list_mentors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AdminMentorItem]:
    _require_admin(current_user)
    mentors = list(db.execute(select(Mentor).order_by(Mentor.id.asc())).scalars().all())
    return [AdminMentorItem.model_validate(item) for item in mentors]


@router.post("/mentors", response_model=AdminMentorItem)
def admin_create_mentor(
    payload: AdminMentorCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminMentorItem:
    _require_admin(current_user)

    mentor = Mentor(
        name=payload.name.strip(),
        intro=payload.intro.strip(),
        location=payload.location.strip(),
        avatar=payload.avatar.strip(),
        is_active=payload.is_active,
    )
    db.add(mentor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="导师名称已存在")

    db.refresh(mentor)
    return AdminMentorItem.model_validate(mentor)


@router.put("/mentors/{mentor_id}", response_model=AdminMentorItem)
def admin_update_mentor(
    mentor_id: int,
    payload: AdminMentorUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminMentorItem:
    _require_admin(current_user)

    mentor = db.execute(select(Mentor).where(Mentor.id == mentor_id)).scalar_one_or_none()
    if mentor is None:
        raise HTTPException(status_code=404, detail="导师不存在")

    if payload.name is not None:
        mentor.name = payload.name.strip()
    if payload.intro is not None:
        mentor.intro = payload.intro.strip()
    if payload.location is not None:
        mentor.location = payload.location.strip()
    if payload.avatar is not None:
        mentor.avatar = payload.avatar.strip()
    if payload.is_active is not None:
        mentor.is_active = payload.is_active

    db.add(mentor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="导师名称冲突")

    db.refresh(mentor)
    return AdminMentorItem.model_validate(mentor)


@router.delete("/mentors/{mentor_id}")
def admin_delete_mentor(
    mentor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    _require_admin(current_user)

    mentor = db.execute(select(Mentor).where(Mentor.id == mentor_id)).scalar_one_or_none()
    if mentor is None:
        raise HTTPException(status_code=404, detail="导师不存在")

    db.delete(mentor)
    db.commit()
    return {"detail": "删除成功"}


@router.get("/schedules", response_model=List[AdminScheduleItem])
def admin_list_schedules(
    mentor_id: int = 0,
    schedule_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AdminScheduleItem]:
    _require_admin(current_user)

    stmt = select(MentorSchedule, Mentor.name).join(Mentor, Mentor.id == MentorSchedule.mentor_id)
    if mentor_id > 0:
        stmt = stmt.where(MentorSchedule.mentor_id == mentor_id)
    if schedule_date is not None:
        stmt = stmt.where(MentorSchedule.schedule_date == schedule_date)

    rows = db.execute(
        stmt.order_by(MentorSchedule.schedule_date.desc(), MentorSchedule.time_slot.asc(), MentorSchedule.id.desc())
    ).all()

    result: List[AdminScheduleItem] = []
    for schedule, mentor_name in rows:
        result.append(
            AdminScheduleItem(
                id=schedule.id,
                mentor_id=schedule.mentor_id,
                mentor_name=mentor_name,
                schedule_date=schedule.schedule_date,
                time_slot=schedule.time_slot,
                capacity=schedule.capacity,
                is_active=bool(schedule.is_active),
            )
        )
    return result


@router.post("/schedules", response_model=AdminScheduleItem)
def admin_create_schedule(
    payload: AdminScheduleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminScheduleItem:
    _require_admin(current_user)

    mentor = db.execute(select(Mentor).where(Mentor.id == payload.mentor_id)).scalar_one_or_none()
    if mentor is None:
        raise HTTPException(status_code=404, detail="导师不存在")
    if payload.time_slot not in TIME_SLOTS:
        raise HTTPException(status_code=400, detail="非法时段")

    schedule = MentorSchedule(
        mentor_id=payload.mentor_id,
        schedule_date=payload.schedule_date,
        time_slot=payload.time_slot,
        capacity=payload.capacity,
        is_active=payload.is_active,
    )
    db.add(schedule)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该导师该时段排班已存在")

    db.refresh(schedule)
    return AdminScheduleItem(
        id=schedule.id,
        mentor_id=schedule.mentor_id,
        mentor_name=mentor.name,
        schedule_date=schedule.schedule_date,
        time_slot=schedule.time_slot,
        capacity=schedule.capacity,
        is_active=bool(schedule.is_active),
    )


@router.put("/schedules/{schedule_id}", response_model=AdminScheduleItem)
def admin_update_schedule(
    schedule_id: int,
    payload: AdminScheduleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminScheduleItem:
    _require_admin(current_user)

    schedule = db.execute(select(MentorSchedule).where(MentorSchedule.id == schedule_id)).scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=404, detail="排班不存在")

    if payload.mentor_id is not None:
        mentor_exists = db.execute(select(Mentor).where(Mentor.id == payload.mentor_id)).scalar_one_or_none()
        if mentor_exists is None:
            raise HTTPException(status_code=404, detail="导师不存在")
        schedule.mentor_id = payload.mentor_id
    if payload.schedule_date is not None:
        schedule.schedule_date = payload.schedule_date
    if payload.time_slot is not None:
        if payload.time_slot not in TIME_SLOTS:
            raise HTTPException(status_code=400, detail="非法时段")
        schedule.time_slot = payload.time_slot
    if payload.capacity is not None:
        schedule.capacity = payload.capacity
    if payload.is_active is not None:
        schedule.is_active = payload.is_active

    db.add(schedule)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="排班冲突：同导师同日期同时段已存在")

    db.refresh(schedule)
    mentor_name = db.execute(select(Mentor.name).where(Mentor.id == schedule.mentor_id)).scalar_one_or_none() or ""
    return AdminScheduleItem(
        id=schedule.id,
        mentor_id=schedule.mentor_id,
        mentor_name=mentor_name,
        schedule_date=schedule.schedule_date,
        time_slot=schedule.time_slot,
        capacity=schedule.capacity,
        is_active=bool(schedule.is_active),
    )


@router.delete("/schedules/{schedule_id}")
def admin_delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    _require_admin(current_user)

    schedule = db.execute(select(MentorSchedule).where(MentorSchedule.id == schedule_id)).scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=404, detail="排班不存在")

    db.delete(schedule)
    db.commit()
    return {"detail": "删除成功"}


@router.get("/tree/posts", response_model=List[AdminTreePostItem])
def admin_list_tree_posts(
    status: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AdminTreePostItem]:
    _require_admin(current_user)

    stmt = (
        select(TreePost, User.account)
        .outerjoin(User, User.id == TreePost.author_user_id)
        .order_by(desc(TreePost.created_at))
    )
    if status.strip():
        stmt = stmt.where(TreePost.status == status.strip())

    rows = db.execute(stmt).all()
    result: List[AdminTreePostItem] = []
    for post, account in rows:
        result.append(
            AdminTreePostItem(
                id=post.id,
                tree_slug=post.tree_slug,
                content=post.content,
                status=post.status,
                author_account=account,
                created_at=_datetime_to_text(post.created_at),
                updated_at=_datetime_to_text(post.updated_at),
            )
        )
    return result


@router.put("/tree/posts/{post_id}/status", response_model=AdminTreePostItem)
def admin_update_tree_post_status(
    post_id: int,
    payload: AdminStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminTreePostItem:
    _require_admin(current_user)

    post = db.execute(select(TreePost).where(TreePost.id == post_id)).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")

    post.status = payload.status
    db.add(post)
    db.commit()
    db.refresh(post)

    account = db.execute(select(User.account).where(User.id == post.author_user_id)).scalar_one_or_none()
    return AdminTreePostItem(
        id=post.id,
        tree_slug=post.tree_slug,
        content=post.content,
        status=post.status,
        author_account=account,
        created_at=_datetime_to_text(post.created_at),
        updated_at=_datetime_to_text(post.updated_at),
    )


@router.get("/tree/comments", response_model=List[AdminTreeCommentItem])
def admin_list_tree_comments(
    status: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AdminTreeCommentItem]:
    _require_admin(current_user)

    stmt = (
        select(TreeComment, User.account)
        .outerjoin(User, User.id == TreeComment.author_user_id)
        .order_by(desc(TreeComment.created_at))
    )
    if status.strip():
        stmt = stmt.where(TreeComment.status == status.strip())

    rows = db.execute(stmt).all()
    result: List[AdminTreeCommentItem] = []
    for comment, account in rows:
        result.append(
            AdminTreeCommentItem(
                id=comment.id,
                post_id=comment.post_id,
                content=comment.content,
                status=comment.status,
                author_account=account,
                created_at=_datetime_to_text(comment.created_at),
            )
        )
    return result


@router.put("/tree/comments/{comment_id}/status", response_model=AdminTreeCommentItem)
def admin_update_tree_comment_status(
    comment_id: int,
    payload: AdminStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminTreeCommentItem:
    _require_admin(current_user)

    comment = db.execute(select(TreeComment).where(TreeComment.id == comment_id)).scalar_one_or_none()
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")

    comment.status = payload.status
    db.add(comment)
    db.commit()
    db.refresh(comment)

    account = db.execute(select(User.account).where(User.id == comment.author_user_id)).scalar_one_or_none()
    return AdminTreeCommentItem(
        id=comment.id,
        post_id=comment.post_id,
        content=comment.content,
        status=comment.status,
        author_account=account,
        created_at=_datetime_to_text(comment.created_at),
    )


@router.get("/xhs/users", response_model=List[AdminXhsAuditItem])
def admin_list_xhs_users(
    audit_status: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AdminXhsAuditItem]:
    _require_admin(current_user)

    stmt = select(User).where(User.xhs_url.is_not(None), User.xhs_url != "")
    if audit_status.strip() in {"pending", "approved", "rejected"}:
        stmt = stmt.where(User.xhs_audit_status == audit_status.strip())

    users = list(db.execute(stmt.order_by(User.updated_at.desc())).scalars().all())
    return [
        AdminXhsAuditItem(
            user_id=int(item.id),
            account=item.account,
            nickname=item.nickname,
            xhs_url=item.xhs_url or "",
            xhs_audit_status=item.xhs_audit_status or "pending",
            updated_at=_datetime_to_text(item.updated_at),
        )
        for item in users
    ]


@router.put("/xhs/users/{user_id}/audit", response_model=AdminXhsAuditItem)
def admin_audit_xhs_user(
    user_id: int,
    payload: AdminXhsAuditUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminXhsAuditItem:
    _require_admin(current_user)

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not (user.xhs_url or "").strip():
        raise HTTPException(status_code=400, detail="该用户未提交小红书主页URL")

    user.xhs_audit_status = payload.status
    db.add(user)
    db.commit()
    db.refresh(user)

    return AdminXhsAuditItem(
        user_id=int(user.id),
        account=user.account,
        nickname=user.nickname,
        xhs_url=user.xhs_url or "",
        xhs_audit_status=user.xhs_audit_status or "pending",
        updated_at=_datetime_to_text(user.updated_at),
    )
