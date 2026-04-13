# Backend (FastAPI)

This folder contains the real backend service for the project.

## 1. Directory

- `app/main.py`: FastAPI application entry
- `app/api/routes/auth.py`: register/login APIs
- `app/api/routes/profile.py`: profile read/update APIs
- `app/api/deps.py`: current-user dependency (JWT)
- `app/db/models.py`: SQLAlchemy models
- `app/db/schemas.py`: request/response schemas
- `app/core/config.py`: environment config
- `app/core/security.py`: password hash + JWT utilities

## 2. SQL setup

Run SQL file in project root first:

- `../database_schema.sql`

It creates database `mind_island` and tables:

- `users`
- `tree_posts`
- `tree_comments`
- `tree_post_reactions`
- `mentors`
- `mentor_appointments`
- `mentor_schedules`
- `user_posts`

## 3. Environment

Copy `.env.example` to `.env` and edit values:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Important values:

- `DATABASE_URL`: your MySQL connection string
- `JWT_SECRET_KEY`: change to a secure random string
- `CORS_ORIGINS`: include frontend origin (Vite default is `http://localhost:5173`)

## 4. Install and run

```bash
cd backend
python -m venv .venv
```

Activate venv:

- Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

- macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start service:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 5. API summary

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`

`register` request body example:

```json
{
  "account": "test001",
  "password": "123456",
  "nickname": "Tester",
  "avatar": "data:image/png;base64,...",
  "xhs_url": "https://www.xiaohongshu.com/user/profile/xxx",
  "email": "test@example.com",
  "gender": "女",
  "phone": "13800000000",
  "signature": "Today is a good day"
}
```

`login` request body example:

```json
{
  "account": "test001",
  "password": "123456"
}
```

Both return:

- `access_token`
- `token_type` (`bearer`)
- `user` (full profile fields used by frontend)

### Profile

Use header:

- `Authorization: Bearer <access_token>`

Endpoints:

- `GET /api/profile/me` (read current profile)
- `PUT /api/profile/me` (update profile fields)

`PUT /api/profile/me` body supports:

- `nickname`
- `avatar`
- `xhs_url`
- `email`
- `gender`
- `phone`
- `signature`

### Tree Hole

Public list (supports optional login token to return your reaction state):

- `GET /api/tree/posts?tree_slug=anxu|baitai|nuanguang`

Authenticated actions (need `Authorization: Bearer <access_token>`):

- `POST /api/tree/posts` (create post)
- `POST /api/tree/posts/{post_id}/comments` (create comment)
- `POST /api/tree/posts/{post_id}/reactions/toggle` (toggle hug/sense, click again to cancel)

Create post body:

```json
{
  "tree_slug": "anxu",
  "content": "今天有点焦虑，但我在努力调整。"
}
```

Create comment body:

```json
{
  "content": "抱抱你，你已经很棒了。"
}
```

Toggle reaction body:

```json
{
  "reaction_type": "hug"
}
```

## 6. Frontend integration tips

- Replace current fake login/register logic with HTTP requests to above APIs.
- Save `access_token` after login/register.
- Send token in `Authorization` for profile APIs.
- Keep avatar as URL or Base64 string, backend accepts both.
- Tree-hole feed is returned in descending `created_at` order (latest first).

### Mentor

Query mentor schedule (supports date + search):

- `GET /api/mentor/slots?date_value=2026-04-12&name=林&location=A302`

If you only pass `name/location` without `date_value`, API returns all matching mentors' schedule rows (not restricted by date).

Book mentor slot (need login):

- `POST /api/mentor/appointments`

Request body:

```json
{
  "mentor_id": 1,
  "appointment_date": "2026-04-12",
  "time_slot": "14:00-15:30"
}
```

My appointments (need login):

- `GET /api/mentor/appointments/me`
- `DELETE /api/mentor/appointments/{appointment_id}`

### Analysis

Run model inference using current user's posts in `user_posts` table:

- `POST /api/analysis/run`

Import demo data from `backend/data.csv` into current user:

- `POST /api/analysis/seed-demo`

Required files for model inference:

- project root: `process_red_data_for_mmim.py`
- backend root: `best_full_model.pth`
- project root: `models.py` (imported by `process_red_data_for_mmim.py`)

## 7. Notes

- Password is stored as bcrypt hash (`password_hash`), never plain text.
- This version uses manual SQL execution as requested; no migration tool is required.
