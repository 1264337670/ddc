-- Database schema for Mind Island backend (MySQL 8+)
-- Run this file in your database before starting the FastAPI service.

CREATE DATABASE IF NOT EXISTS mind_island DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mind_island;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  account VARCHAR(64) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  nickname VARCHAR(64) NOT NULL,
  avatar TEXT NULL,
  xhs_url VARCHAR(255) NULL,
  email VARCHAR(120) NULL,
  gender VARCHAR(16) NULL,
  phone VARCHAR(32) NULL,
  signature VARCHAR(255) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_account (account),
  UNIQUE KEY uk_users_email (email),
  UNIQUE KEY uk_users_phone (phone),
  KEY idx_users_nickname (nickname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tree_posts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  tree_slug VARCHAR(32) NOT NULL,
  author_user_id BIGINT UNSIGNED NULL,
  content TEXT NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'approved',
  hug_count INT NOT NULL DEFAULT 0,
  sense_count INT NOT NULL DEFAULT 0,
  comment_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_tree_posts_slug_created_at (tree_slug, created_at),
  KEY idx_tree_posts_status_created_at (status, created_at),
  CONSTRAINT fk_tree_posts_author_user
    FOREIGN KEY (author_user_id) REFERENCES users(id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tree_comments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  post_id BIGINT UNSIGNED NOT NULL,
  author_user_id BIGINT UNSIGNED NULL,
  content VARCHAR(500) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'approved',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_tree_comments_post_created_at (post_id, created_at),
  CONSTRAINT fk_tree_comments_post
    FOREIGN KEY (post_id) REFERENCES tree_posts(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_tree_comments_author_user
    FOREIGN KEY (author_user_id) REFERENCES users(id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tree_post_reactions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  post_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  reaction_type VARCHAR(16) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_tree_post_reactions_unique (post_id, user_id, reaction_type),
  KEY idx_tree_post_reactions_post (post_id),
  CONSTRAINT fk_tree_post_reactions_post
    FOREIGN KEY (post_id) REFERENCES tree_posts(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_tree_post_reactions_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mentors (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL,
  intro VARCHAR(255) NOT NULL,
  location VARCHAR(64) NOT NULL,
  avatar VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_mentors_name (name),
  KEY idx_mentors_location (location)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mentor_appointments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  mentor_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  appointment_date DATE NOT NULL,
  time_slot VARCHAR(32) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'booked',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_mentor_appointment_unique (mentor_id, user_id, appointment_date, time_slot, status),
  KEY idx_mentor_appointments_date (appointment_date),
  KEY idx_mentor_appointments_user (user_id),
  KEY idx_mentor_appointments_mentor_slot (mentor_id, appointment_date, time_slot, status),
  CONSTRAINT fk_mentor_appointments_mentor
    FOREIGN KEY (mentor_id) REFERENCES mentors(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_mentor_appointments_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mentor_schedules (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  mentor_id BIGINT UNSIGNED NOT NULL,
  schedule_date DATE NOT NULL,
  time_slot VARCHAR(32) NOT NULL,
  capacity INT NOT NULL DEFAULT 5,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_mentor_schedule_unique (mentor_id, schedule_date, time_slot),
  KEY idx_mentor_schedule_date (schedule_date),
  CONSTRAINT fk_mentor_schedules_mentor
    FOREIGN KEY (mentor_id) REFERENCES mentors(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_posts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  post_uid VARCHAR(64) NOT NULL,
  title VARCHAR(255) NOT NULL,
  author VARCHAR(64) NOT NULL,
  posted_at DATETIME NOT NULL,
  content TEXT NOT NULL,
  image_path VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_posts_uid (user_id, post_uid),
  KEY idx_user_posts_time (user_id, posted_at),
  CONSTRAINT fk_user_posts_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO mentors (name, intro, location, avatar, is_active)
VALUES
  ('林溪导师', '温和倾听，擅长焦虑减压与情绪稳定。', 'A302 咨询室', '/assets/doctor1.png', 1),
  ('顾南导师', '聚焦关系沟通与家庭冲突修复。', 'B105 心理室', '/assets/doctor2.png', 1),
  ('程乔导师', '帮助成长规划与学习节奏重建。', 'C201 安静室', '/assets/doctor3.png', 1),
  ('沈禾导师', '善于压力管理与自我接纳训练。', '线上视频室', '/assets/doctor4.png', 1),
  ('白言导师', '关注青少年支持与考试焦虑辅导。', 'D101 团辅室', '/assets/doctor1.png', 1),
  ('周棠导师', '擅长睡眠困扰和日常作息调节。', 'A302 咨询室', '/assets/doctor2.png', 1)
ON DUPLICATE KEY UPDATE
  intro = VALUES(intro),
  location = VALUES(location),
  avatar = VALUES(avatar),
  is_active = VALUES(is_active);

USE mind_island;

DELETE FROM mentor_schedules 
WHERE schedule_date >= '2026-04-01' 
AND schedule_date < '2026-05-01';

INSERT INTO mentor_schedules (mentor_id, schedule_date, time_slot, capacity, is_active)
SELECT
  ((DAY(t.schedule_date) + s.slot_idx - 2) % 6) + 1 AS mentor_id,
  t.schedule_date,
  s.time_slot,
  5 AS capacity,
  1 AS is_active
FROM (
  SELECT DATE_ADD('2026-04-01', INTERVAL n DAY) AS schedule_date
  FROM (
    SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
    UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9
    UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12 UNION ALL SELECT 13 UNION ALL SELECT 14
    UNION ALL SELECT 15 UNION ALL SELECT 16 UNION ALL SELECT 17 UNION ALL SELECT 18 UNION ALL SELECT 19
    UNION ALL SELECT 20 UNION ALL SELECT 21 UNION ALL SELECT 22 UNION ALL SELECT 23 UNION ALL SELECT 24
    UNION ALL SELECT 25 UNION ALL SELECT 26 UNION ALL SELECT 27 UNION ALL SELECT 28 UNION ALL SELECT 29
  ) AS numbers
) AS t
CROSS JOIN (
  SELECT 1 AS slot_idx, '8:00-9:30' AS time_slot UNION ALL
  SELECT 2, '10:00-11:30' UNION ALL
  SELECT 3, '14:00-15:30' UNION ALL
  SELECT 4, '16:00-17:30'
) AS s;
