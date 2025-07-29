from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "rahasia_super_secret"

# Simpan data sementara (ganti pakai database jika perlu)
users = {}
articles = []

# Context processor untuk mengirim user ke template
@app.context_processor
def inject_user():
    user_email = session.get("user_email")
    user = users.get(user_email)
    return dict(user=user)

@app.route("/")
def index():
    return render_template("index.html", articles=articles)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if email in users:
            error = "Email sudah terdaftar."
        elif len(password) < 8 or not re.search(r"[0-9]", password) or not re.search(r"[A-Za-z]", password):
            error = "Password harus minimal 8 karakter dan mengandung huruf & angka."
        else:
            users[email] = {"name": name, "email": email, "password": password}
            session["user_email"] = email
            return redirect("https://sebelassatu.news/")

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users.get(email)
        if user and user["password"] == password:
            session["user_email"] = email
            return redirect("https://sebelassatu.news/")
        else:
            error = "Email atau password salah."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user_email", None)
    return redirect("https://sebelassatu.news/")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_email" not in session:
        return redirect("https://sebelassatu.news/login")

    user = users.get(session["user_email"])
    user_articles = [a for a in articles if a["author"] == user["name"]]
    message = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_info":
            new_name = request.form.get("name")
            new_email = request.form.get("email")

            if new_email and new_email != user["email"]:
                users[new_email] = users.pop(user["email"])
                user = users[new_email]
                session["user_email"] = new_email
                user["email"] = new_email

            if new_name:
                user["name"] = new_name

            message = "✅ Profil berhasil diperbarui!"

        elif action == "update_password":
            old_password = request.form.get("old_password")
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")

            if old_password != user["password"]:
                message = "❌ Password lama salah."
            elif new_password != confirm_password:
                message = "❌ Password baru dan konfirmasi tidak cocok."
            elif len(new_password) < 8:
                message = "❌ Password harus minimal 8 karakter."
            elif not re.search(r"[0-9]", new_password) or not re.search(r"[A-Za-z]", new_password):
                message = "❌ Password harus mengandung huruf dan angka."
            else:
                user["password"] = new_password
                message = "✅ Password berhasil diperbarui!"
                session.pop("user_email", None)  # logout otomatis
                return redirect("https://sebelassatu.news/login")

    return render_template("profile.html", user=user, articles=user_articles, message=message)

@app.route("/add_article", methods=["POST"])
def add_article():
    if "user_email" not in session:
        return redirect("https://sebelassatu.news/login")

    title = request.form.get("title")
    content = request.form.get("content")

    if title and content:
        slug = title.lower().replace(" ", "-") + "-" + datetime.now().strftime("%H%M%S")
        article = {
            "title": title,
            "content": content,
            "author": users[session["user_email"]]["name"],
            "date": datetime.now().strftime("%d %B %Y %H:%M"),
            "slug": slug
        }
        articles.append(article)

    return redirect("https://sebelassatu.news/")

@app.route("/article/<slug>")
def view_article(slug):
    article = next((a for a in articles if a["slug"] == slug), None)
    if not article:
        return "Artikel tidak ditemukan", 404
    return render_template("article.html", article=article)

@app.route("/edit_article/<slug>", methods=["GET", "POST"])
def edit_article(slug):
    if "user_email" not in session:
        return redirect("https://sebelassatu.news/login")

    user = users.get(session["user_email"])
    article = next((a for a in articles if a["slug"] == slug and a["author"] == user["name"]), None)

    if not article:
        return "Artikel tidak ditemukan atau kamu bukan penulisnya.", 403

    if request.method == "POST":
        new_title = request.form.get("title")
        new_content = request.form.get("content")
        if new_title and new_content:
            article["title"] = new_title
            article["content"] = new_content
            return redirect(f"https://sebelassatu.news/article/{slug}")

    return render_template("edit_article.html", article=article)

@app.route("/delete_article/<slug>")
def delete_article(slug):
    if "user_email" not in session:
        return redirect("https://sebelassatu.news/login")

    user = users.get(session["user_email"])
    article = next((a for a in articles if a["slug"] == slug and a["author"] == user["name"]), None)

    if not article:
        return "Artikel tidak ditemukan atau kamu bukan penulisnya.", 403

    articles.remove(article)
    return redirect("https://sebelassatu.news/profile")

if __name__ == "__main__":
    app.run(debug=True)
