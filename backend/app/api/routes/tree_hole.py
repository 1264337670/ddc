from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import TreeComment, TreePost, TreePostReaction, User
from app.db.schemas import (
    TreeCommentCreateRequest,
    TreeCommentPublic,
    TreePostCreateRequest,
    TreePostPublic,
    TreeReactionToggleRequest,
    TreeReactionToggleResponse,
)

router = APIRouter(prefix="/api/tree", tags=["tree-hole"])
oauth2_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

VALID_TREE_SLUGS = {"anxu", "baitai", "nuanguang"}


def _datetime_to_text(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")


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


def _build_post_public(post: TreePost, comments: List[TreeComment], hugged: bool, sensed: bool) -> TreePostPublic:
    return TreePostPublic(
        id=post.id,
        tree_slug=post.tree_slug,
        content=post.content,
        created_at=_datetime_to_text(post.created_at),
        hug_count=post.hug_count,
        sense_count=post.sense_count,
        comment_count=post.comment_count,
        hugged=hugged,
        sensed=sensed,
        comments=[
            TreeCommentPublic(
                id=item.id,
                post_id=item.post_id,
                content=item.content,
                created_at=_datetime_to_text(item.created_at),
            )
            for item in comments
        ],
    )


@router.get("/posts", response_model=List[TreePostPublic])
def list_posts(
    tree_slug: str,
    token: Optional[str] = Depends(oauth2_optional),
    db: Session = Depends(get_db),
) -> List[TreePostPublic]:
    if tree_slug not in VALID_TREE_SLUGS:
        raise HTTPException(status_code=400, detail="非法树洞分区")

    current_user = _get_optional_user(db, token)

    posts_stmt = (
        select(TreePost)
        .where(TreePost.tree_slug == tree_slug, TreePost.status == "approved")
        .order_by(desc(TreePost.created_at))
    )
    posts = list(db.execute(posts_stmt).scalars().all())
    if not posts:
        return []

    post_ids = [item.id for item in posts]

    comments_stmt = (
        select(TreeComment)
        .where(TreeComment.post_id.in_(post_ids), TreeComment.status == "approved")
        .order_by(TreeComment.created_at.asc())
    )
    all_comments = list(db.execute(comments_stmt).scalars().all())

    comments_map: Dict[int, List[TreeComment]] = {}
    for comment in all_comments:
        comments_map.setdefault(comment.post_id, []).append(comment)

    hugged_ids: Set[int] = set()
    sensed_ids: Set[int] = set()
    if current_user:
        reactions_stmt = select(TreePostReaction).where(
            TreePostReaction.post_id.in_(post_ids),
            TreePostReaction.user_id == current_user.id,
        )
        reactions = list(db.execute(reactions_stmt).scalars().all())
        hugged_ids = {item.post_id for item in reactions if item.reaction_type == "hug"}
        sensed_ids = {item.post_id for item in reactions if item.reaction_type == "sense"}

    return [
        _build_post_public(
            post=post,
            comments=comments_map.get(post.id, []),
            hugged=post.id in hugged_ids,
            sensed=post.id in sensed_ids,
        )
        for post in posts
    ]


@router.post("/posts", response_model=TreePostPublic)
def create_post(
    payload: TreePostCreateRequest,
    token: Optional[str] = Depends(oauth2_optional),
    db: Session = Depends(get_db),
) -> TreePostPublic:
    user = _get_required_user(db, token)

    tree_slug = payload.tree_slug.strip()
    if tree_slug not in VALID_TREE_SLUGS:
        raise HTTPException(status_code=400, detail="非法树洞分区")

    post = TreePost(
        tree_slug=tree_slug,
        author_user_id=user.id,
        content=payload.content.strip(),
        status="approved",
        hug_count=0,
        sense_count=0,
        comment_count=0,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return _build_post_public(post, [], hugged=False, sensed=False)


@router.post("/posts/{post_id}/comments", response_model=TreeCommentPublic)
def create_comment(
    post_id: int,
    payload: TreeCommentCreateRequest,
    token: Optional[str] = Depends(oauth2_optional),
    db: Session = Depends(get_db),
) -> TreeCommentPublic:
    user = _get_required_user(db, token)

    post = db.execute(select(TreePost).where(TreePost.id == post_id, TreePost.status == "approved")).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")

    comment = TreeComment(
        post_id=post_id,
        author_user_id=user.id,
        content=payload.content.strip(),
        status="approved",
    )
    db.add(comment)

    post.comment_count = int(post.comment_count) + 1
    db.add(post)

    db.commit()
    db.refresh(comment)

    return TreeCommentPublic(
        id=comment.id,
        post_id=comment.post_id,
        content=comment.content,
        created_at=_datetime_to_text(comment.created_at),
    )


@router.post("/posts/{post_id}/reactions/toggle", response_model=TreeReactionToggleResponse)
def toggle_reaction(
    post_id: int,
    payload: TreeReactionToggleRequest,
    token: Optional[str] = Depends(oauth2_optional),
    db: Session = Depends(get_db),
) -> TreeReactionToggleResponse:
    user = _get_required_user(db, token)

    post = db.execute(select(TreePost).where(TreePost.id == post_id, TreePost.status == "approved")).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")

    reaction_type = payload.reaction_type

    existing = db.execute(
        select(TreePostReaction).where(
            TreePostReaction.post_id == post_id,
            TreePostReaction.user_id == user.id,
            TreePostReaction.reaction_type == reaction_type,
        )
    ).scalar_one_or_none()

    active = False
    if existing:
        db.execute(delete(TreePostReaction).where(TreePostReaction.id == existing.id))
        if reaction_type == "hug":
            post.hug_count = max(0, int(post.hug_count) - 1)
        else:
            post.sense_count = max(0, int(post.sense_count) - 1)
        active = False
    else:
        db.add(
            TreePostReaction(
                post_id=post_id,
                user_id=user.id,
                reaction_type=reaction_type,
            )
        )
        if reaction_type == "hug":
            post.hug_count = int(post.hug_count) + 1
        else:
            post.sense_count = int(post.sense_count) + 1
        active = True

    db.add(post)
    db.commit()
    db.refresh(post)

    return TreeReactionToggleResponse(
        post_id=post.id,
        reaction_type=reaction_type,
        active=active,
        hug_count=post.hug_count,
        sense_count=post.sense_count,
    )
