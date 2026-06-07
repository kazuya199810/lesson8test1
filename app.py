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

load_dotenv()

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL が設定されていません。.env または Render の Environment Variables を確認してください。"
    )

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1,
    )

engine = create_engine(
    database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine)


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


Base.metadata.create_all(engine)

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
}
.card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}
.error {
    background: #ffe5e5;
    color: #b00020;
    padding: 12px;
}
input, textarea {
    width: 100%;
    box-sizing: border-box;
    padding: 8px;
}
.recipe-title {
    font-weight: bold;
}
.meta {
    color: #666;
}
</style>
</head>
<body>

<h1>🍳 レシピ投稿ミニアプリ</h1>

{% if error_message %}
<div class="error">{{ error_message }}</div>
{% endif %}

<div class="card">
<h2>新規レシピ投稿</h2>

<form method="post">

<label>タイトル</label>
<input
    type="text"
    name="title"
    maxlength="200"
    value="{{ form_title }}"
    required
>

<label>所要分数</label>
<input
    type="number"
    name="minutes"
    min="1"
    value="{{ form_minutes }}"
    required
>

<label>説明</label>
<textarea
    name="description"
    rows="4"
>{{ form_description }}</textarea>

<button type="submit">
投稿する
</button>

</form>
</div>

<h2>レシピ一覧</h2>

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
投稿日: {{ recipe.created_at }}
</div>

<div style="margin-top:10px;">

<a href="{{ url_for('edit_recipe', recipe_id=recipe.id) }}">
編集
</a>

<form
    method="post"
    action="{{ url_for('delete_recipe', recipe_id=recipe.id) }}"
    style="display:inline;"
    onsubmit="return confirm('削除しますか？');"
>
<button type="submit">
削除
</button>
</form>

</div>

</div>
{% endfor %}

</body>
</html>
"""

EDIT_TEMPLATE = """
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>レシピ編集</title>
</head>
<body>

<h1>レシピ編集</h1>

{% if error_message %}
<p style="color:red;">
{{ error_message }}
</p>
{% endif %}

<form method="post">

<label>タイトル</label><br>
<input
    type="text"
    name="title"
    maxlength="200"
    value="{{ recipe.title }}"
    required
>

<br><br>

<label>所要分数</label><br>
<input
    type="number"
    name="minutes"
    min="1"
    value="{{ recipe.minutes }}"
    required
>

<br><br>

<label>説明</label><br>
<textarea
    name="description"
    rows="5"
>{{ recipe.description or "" }}</textarea>

<br><br>

<button type="submit">
更新する
</button>

</form>

<p>
<a href="{{ url_for('index') }}">
一覧へ戻る
</a>
</p>

</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    error_message = ""

    form_title = ""
    form_minutes = ""
    form_description = ""

    if request.method == "POST":
        form_title = request.form.get("title", "").strip()
        form_minutes = request.form.get("minutes", "").strip()
        form_description = request.form.get("description", "").strip()

        try:
            if not form_title:
                raise ValueError("タイトルは必須です。")

            if len(form_title) > 200:
                raise ValueError("タイトルは200文字以内です。")

            try:
                minutes_value = int(form_minutes)
            except ValueError:
                raise ValueError("所要分数は整数です。")

            if minutes_value < 1:
                raise ValueError("所要分数は1以上です。")

            with SessionLocal() as session:
                recipe = Recipe(
                    title=form_title,
                    minutes=minutes_value,
                    description=form_description or None,
                )

                session.add(recipe)
                session.commit()

            return redirect(url_for("index"))

        except Exception as e:
            error_message = f"入力エラー: {e}"

    try:
        with SessionLocal() as session:
            recipes = session.scalars(
                select(Recipe).order_by(
                    Recipe.created_at.desc()
                )
            ).all()
    except Exception as e:
        recipes = []
        error_message = f"DBエラー: {e}"

    return render_template_string(
        PAGE_TEMPLATE,
        recipes=recipes,
        error_message=error_message,
        form_title=form_title,
        form_minutes=form_minutes,
        form_description=form_description,
    )


@app.route("/edit/<int:recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):

    error_message = ""

    with SessionLocal() as session:

        recipe = session.get(
            Recipe,
            recipe_id,
        )

        if recipe is None:
            return "レシピが見つかりません", 404

        if request.method == "POST":

            try:
                title = request.form.get(
                    "title",
                    "",
                ).strip()

                minutes_text = request.form.get(
                    "minutes",
                    "",
                ).strip()

                description = request.form.get(
                    "description",
                    "",
                ).strip()

                if not title:
                    raise ValueError(
                        "タイトルは必須です。"
                    )

                if len(title) > 200:
                    raise ValueError(
                        "タイトルは200文字以内です。"
                    )

                try:
                    minutes = int(minutes_text)
                except ValueError:
                    raise ValueError(
                        "所要分数は整数です。"
                    )

                if minutes < 1:
                    raise ValueError(
                        "所要分数は1以上です。"
                    )

                recipe.title = title
                recipe.minutes = minutes
                recipe.description = (
                    description or None
                )

                session.commit()

                return redirect(
                    url_for("index")
                )

            except Exception as e:
                error_message = str(e)

        return render_template_string(
            EDIT_TEMPLATE,
            recipe=recipe,
            error_message=error_message,
        )


@app.route(
    "/delete/<int:recipe_id>",
    methods=["POST"],
)
def delete_recipe(recipe_id):

    with SessionLocal() as session:

        recipe = session.get(
            Recipe,
            recipe_id,
        )

        if recipe is None:
            return (
                "レシピが見つかりません",
                404,
            )

        session.delete(recipe)
        session.commit()

    return redirect(
        url_for("index")
    )


if __name__ == "__main__":
    port = int(
        os.environ.get(
            "PORT",
            8000,
        )
    )

    debug = (
        os.environ.get(
            "DEBUG",
            "false",
        ).lower()
        in (
            "1",
            "true",
            "yes",
            "on",
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
    )
