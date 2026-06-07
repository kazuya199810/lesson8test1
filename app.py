import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, render_template_string, request, redirect, url_for
from sqlalchemy import (
    create_engine,
    Integer,
    String,
    Text,
    DateTime,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)

# .env を読み込む（存在しなくてもOK）
load_dotenv()

app = Flask(__name__)

# =========================
# 環境変数からDB接続URL取得
# =========================
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL が設定されていません。.env または Render の Environment Variables を確認してください。"
    )

# Render の postgres:// を SQLAlchemy 用に変換
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1,
    )

# DBエンジン作成
engine = create_engine(
    database_url,
    pool_pre_ping=True,
)

# Session作成
SessionLocal = sessionmaker(bind=engine)


# =========================
# SQLAlchemy モデル定義
# =========================
class Base(DeclarativeBase):
    pass


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# テーブル自動作成
Base.metadata.create_all(engine)

# =========================
# HTMLテンプレート
# =========================
PAGE_TEMPLATE = """
<!doctype html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <title>レシピ投稿ミニアプリ</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 16px;
            line-height: 1.6;
        }

        h1 {
            margin-bottom: 24px;
        }

        .card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }

        label {
            display: block;
            margin-top: 12px;
            font-weight: bold;
        }

        input[type="text"],
        input[type="number"],
        textarea {
            width: 100%;
            box-sizing: border-box;
            padding: 8px;
            margin-top: 4px;
        }

        button {
            margin-top: 16px;
            padding: 10px 16px;
            cursor: pointer;
        }

        .error {
            background: #ffe5e5;
            color: #b00020;
            border: 1px solid #ffb3b3;
            padding: 12px;
            margin-bottom: 16px;
            border-radius: 6px;
        }

        .recipe-title {
            font-size: 1.1rem;
            font-weight: bold;
        }

        .meta {
            color: #666;
            font-size: 0.9rem;
        }

        .empty {
            color: #666;
        }
    </style>
</head>
<body>

<h1>🍳 レシピ投稿ミニアプリ</h1>

{% if error_message %}
<div class="error">
    {{ error_message }}
</div>
{% endif %}

<div class="card">
    <h2>新規レシピ投稿</h2>

    <form method="post" accept-charset="utf-8">
        <label for="title">タイトル（必須）</label>
        <input
            type="text"
            id="title"
            name="title"
            maxlength="200"
            value="{{ form_title }}"
            required
        >

        <label for="minutes">所要分数（整数・1以上）</label>
        <input
            type="number"
            id="minutes"
            name="minutes"
            min="1"
            step="1"
            value="{{ form_minutes }}"
            required
        >

        <label for="description">説明（任意）</label>
        <textarea
            id="description"
            name="description"
            rows="4"
        >{{ form_description }}</textarea>

        <button type="submit">投稿する</button>
    </form>
</div>

<h2>レシピ一覧</h2>

{% if recipes %}
    {% for recipe in recipes %}
    <div class="card">
        <div class="recipe-title">
            {{ recipe.title }}
        </div>

        <div class="meta">
            所要時間: {{ recipe.minutes }} 分
        </div>

        {% if recipe.description %}
        <p>{{ recipe.description }}</p>
        {% endif %}

        <div class="meta">
            投稿日時: {{ recipe.created_at }}
        </div>
    </div>
    {% endfor %}
{% else %}
    <p class="empty">まだレシピがありません。</p>
{% endif %}

</body>
</html>
"""


# =========================
# 一覧表示 + 新規登録
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    error_message = ""

    form_title = ""
    form_minutes = ""
    form_description = ""

    if request.method == "POST":
        # フォーム値取得
        form_title = request.form.get("title", "").strip()
        form_minutes = request.form.get("minutes", "").strip()
        form_description = request.form.get("description", "").strip()

        try:
            # タイトル必須
            if not form_title:
                raise ValueError("タイトルは必須です。")

            if len(form_title) > 200:
                raise ValueError("タイトルは200文字以内で入力してください。")

            # 所要分数チェック
            try:
                minutes_value = int(form_minutes)
            except ValueError:
                raise ValueError("所要分数は整数で入力してください。")

            if minutes_value < 1:
                raise ValueError("所要分数は1以上で入力してください。")

            # DB保存
            with SessionLocal() as session:
                recipe = Recipe(
                    title=form_title,
                    minutes=minutes_value,
                    description=form_description or None,
                )

                session.add(recipe)
                session.commit()

            # PRGパターン
            return redirect(url_for("index"))

        except Exception as e:
            error_message = f"入力エラー: {e}"

    # 新しい順で取得
    try:
        with SessionLocal() as session:
            recipes = session.scalars(
                select(Recipe).order_by(Recipe.created_at.desc())
            ).all()

    except Exception as e:
        recipes = []
        error_message = f"データベースエラー: {e}"

    response = render_template_string(
        PAGE_TEMPLATE,
        recipes=recipes,
        error_message=error_message,
        form_title=form_title,
        form_minutes=form_minutes,
        form_description=form_description,
    )

    return response, 200, {
        "Content-Type": "text/html; charset=utf-8"
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    debug = (
        os.environ.get("DEBUG", "false").lower()
        in ("1", "true", "yes", "on")
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
    )