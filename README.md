# Flask + SQLAlchemy + Render PostgreSQL レシピ投稿ミニアプリ

Render の無料プランで動作する最小構成のレシピ投稿アプリです。

機能:

- レシピ一覧表示
- レシピ新規投稿
- PostgreSQL保存
- Flask + SQLAlchemy 2系
- 単一ファイル構成（app.py）

---

# プロジェクト構成

```text
recipe-mini-app/
├─ app.py
├─ requirements.txt
├─ .gitignore
└─ README.md
```

---

# データモデル

テーブル名: recipes

| カラム | 型 |
|----------|----------|
| id | Integer PK |
| title | String(200) |
| minutes | Integer |
| description | Text |
| created_at | DateTime |

---

# ローカル実行

## 1. 仮想環境作成

macOS / Linux

```bash
python -m venv env
source env/bin/activate
```

Windows

```powershell
python -m venv env
env\Scripts\activate
```

---

## 2. 依存関係インストール

```bash
pip install -r requirements.txt
```

---

## 3. .env 作成

例:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
DEBUG=true
```

### RenderのExternal Database URLを使う場合

SSLが必要な場合があります。

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
```

---

## 4. 起動

```bash
python app.py
```

ブラウザでアクセス

```text
http://localhost:8000
```

---

# 使い方

1. タイトルを入力
2. 所要分数を入力
3. 説明を入力（任意）
4. 投稿する

投稿後は一覧の先頭に表示されます。

---

# 入力ルール

## タイトル

必須

最大200文字

---

## 所要分数

必須

整数のみ

1以上

例:

```text
5
15
30
60
```

---

## 説明

任意

未入力可

---

# Render デプロイ手順

## 1. GitHubへプッシュ

以下をコミットしてGitHubへPush

```text
app.py
requirements.txt
.gitignore
README.md
```

---

## 2. PostgreSQL作成

Render Dashboard

```text
New
↓
PostgreSQL
↓
Free
```

作成後

```text
Dashboard
↓
対象DB
↓
Internal Database URL
```

をコピー

---

## 3. Web Service作成

```text
New
↓
Web Service
↓
GitHub Repository選択
```

設定:

### Runtime

```text
Python
```

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
python app.py
```

### Environment Variables

DATABASE_URL

```text
Internal Database URL
```

必要に応じて

```text
postgres://
↓
postgresql+psycopg2://
```

へ置換

DEBUG

```text
false
```

---

### Auto Deploy

```text
ON（推奨）
```

---

## 4. 動作確認

デプロイ完了後

```text
https://xxxxx.onrender.com
```

へアクセス

確認項目:

- 一覧が表示される
- レシピ登録できる
- リロード後もデータが残る

---

# DATABASE_URL の注意

Renderが以下形式を返す場合

```text
postgres://...
```

SQLAlchemy 2系ではそのまま利用できません。

アプリ内で自動変換しています。

```python
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1
    )
```

---

# よくあるエラー

## sqlalchemy.exc.NoSuchModuleError

```text
Can't load plugin:
sqlalchemy.dialects:postgres
```

原因:

```text
postgres://
```

を

```text
postgresql+psycopg2://
```

へ変換していない

対策:

DATABASE_URLを確認

---

## ModuleNotFoundError

原因:

- requirements.txtの記載漏れ
- GitHubへコミット漏れ

対策:

```bash
pip install -r requirements.txt
```

再実行

---

## ページが開かない

原因:

```python
host="127.0.0.1"
```

になっている

または

```python
PORT
```

未対応

対策:

```python
app.run(
    host="0.0.0.0",
    port=port
)
```

を確認

---

## DB接続エラー

確認ポイント:

- DATABASE_URL が正しいか
- Internal Database URL を使っているか
- 外部接続なら sslmode=require が必要か

---

# 今後の拡張案

本課題の範囲外ですが、次の機能を追加できます。

- 編集
- 削除
- 検索
- ページネーション
- ログイン認証
- Blueprint分割
- Jinjaテンプレート分離
- Flask-Migrate導入
- Docker対応
- Gunicorn本番運用