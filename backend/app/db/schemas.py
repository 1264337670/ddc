from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import List, Optional


class UserPublic(BaseModel):
    id: int
    account: str
    nickname: str
    role: str = "user"
    avatar: Optional[str] = None
    xhs_url: Optional[str] = None
    xhs_audit_status: str = "pending"
    email: Optional[EmailStr] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    signature: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    account: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=64)
    nickname: str = Field(min_length=1, max_length=64)
    avatar: Optional[str] = None
    xhs_url: Optional[str] = None
    email: Optional[EmailStr] = None
    gender: Optional[str] = Field(default=None, max_length=16)
    phone: Optional[str] = Field(default=None, max_length=32)
    signature: Optional[str] = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    account: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=64)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(default=None, min_length=1, max_length=64)
    avatar: Optional[str] = None
    xhs_url: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    gender: Optional[str] = Field(default=None, max_length=16)
    phone: Optional[str] = Field(default=None, max_length=32)
    signature: Optional[str] = Field(default=None, max_length=255)


class TreeCommentPublic(BaseModel):
    id: int
    post_id: int
    content: str
    created_at: str


class TreePostPublic(BaseModel):
    id: int
    tree_slug: str
    content: str
    created_at: str
    hug_count: int
    sense_count: int
    comment_count: int
    hugged: bool = False
    sensed: bool = False
    comments: List[TreeCommentPublic] = []


class TreePostCreateRequest(BaseModel):
    tree_slug: str = Field(min_length=2, max_length=32)
    content: str = Field(min_length=1, max_length=5000)


class TreeCommentCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class TreeReactionToggleRequest(BaseModel):
    reaction_type: str = Field(pattern='^(hug|sense)$')


class TreeReactionToggleResponse(BaseModel):
    post_id: int
    reaction_type: str
    active: bool
    hug_count: int
    sense_count: int


class MentorSlotPublic(BaseModel):
    slot_id: str
    mentor_id: int
    teacher: str
    date_text: str
    date_iso: str
    time: str
    location: str
    intro: str
    avatar: str
    booked: int
    reserved_by_me: bool


class MentorPublic(BaseModel):
    mentor_id: int
    teacher: str
    location: str
    intro: str
    avatar: str


class MentorAppointmentCreateRequest(BaseModel):
    mentor_id: int
    appointment_date: date
    time_slot: str = Field(min_length=3, max_length=32)


class MentorAppointmentPublic(BaseModel):
    id: int
    mentor_id: int
    teacher: str
    date_text: str
    date_iso: str
    time: str
    location: str
    intro: str
    avatar: str
    created_at: str


class AnalysisPrediction(BaseModel):
    pred_label: int
    pred_name: str
    prob_non_clinical: float
    prob_clinical: float


class AnalysisRunResponse(BaseModel):
    user_id: int
    post_count: int
    health_score: float
    prediction: AnalysisPrediction
    source: str


class ChatMessageItem(BaseModel):
    role: str = Field(pattern='^(system|user|assistant)$')
    content: str = Field(min_length=1, max_length=4000)


class ChatStreamRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: List[ChatMessageItem] = Field(default_factory=list)


class AdminMentorItem(BaseModel):
    id: int
    name: str
    intro: str
    location: str
    avatar: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AdminMentorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    intro: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=64)
    avatar: str = Field(min_length=1, max_length=255)
    is_active: bool = True


class AdminMentorUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    intro: Optional[str] = Field(default=None, min_length=1, max_length=255)
    location: Optional[str] = Field(default=None, min_length=1, max_length=64)
    avatar: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class AdminScheduleItem(BaseModel):
    id: int
    mentor_id: int
    mentor_name: str
    schedule_date: date
    time_slot: str
    capacity: int
    is_active: bool


class AdminScheduleCreateRequest(BaseModel):
    mentor_id: int
    schedule_date: date
    time_slot: str = Field(min_length=3, max_length=32)
    capacity: int = Field(default=5, ge=1, le=200)
    is_active: bool = True


class AdminScheduleUpdateRequest(BaseModel):
    mentor_id: Optional[int] = None
    schedule_date: Optional[date] = None
    time_slot: Optional[str] = Field(default=None, min_length=3, max_length=32)
    capacity: Optional[int] = Field(default=None, ge=1, le=200)
    is_active: Optional[bool] = None


class AdminTreePostItem(BaseModel):
    id: int
    tree_slug: str
    content: str
    status: str
    author_account: Optional[str] = None
    created_at: str
    updated_at: str


class AdminTreeCommentItem(BaseModel):
    id: int
    post_id: int
    content: str
    status: str
    author_account: Optional[str] = None
    created_at: str


class AdminStatusUpdateRequest(BaseModel):
    status: str = Field(pattern='^(approved|blocked)$')


class AdminXhsAuditItem(BaseModel):
    user_id: int
    account: str
    nickname: str
    xhs_url: str
    xhs_audit_status: str
    updated_at: str


class AdminXhsAuditUpdateRequest(BaseModel):
    status: str = Field(pattern='^(approved|rejected)$')
