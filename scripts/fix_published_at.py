#!/usr/bin/env python3
"""
一次性迁移脚本：为所有 published_at 为空的已发布文章补上 published_at = created_at。

用法：
    python scripts/fix_published_at.py

支持 SQLite / MySQL / PostgreSQL，直接读取 .env 中的 DATABASE_URL。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.post import Post

app = create_app()

with app.app_context():
    affected = Post.query.filter(
        Post.status == 'published',
        Post.published_at.is_(None)
    ).all()

    if not affected:
        print('All published posts already have published_at set. Nothing to do.')
        sys.exit(0)

    print(f'Found {len(affected)} published posts with NULL published_at:')
    for p in affected:
        print(f'  [{p.id}] {p.title}  created_at={p.created_at}')
        p.published_at = p.created_at

    db.session.commit()
    print(f'Done. Updated {len(affected)} posts.')
