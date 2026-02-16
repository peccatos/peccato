import json
import os
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "store.db"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))
    app.config["ADMIN_USERNAME"] = os.getenv("ADMIN_USERNAME", "admin")

    admin_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if not admin_hash:
        admin_hash = generate_password_hash("change-me-please")
    app.config["ADMIN_PASSWORD_HASH"] = admin_hash

    with app.app_context():
        init_db()

    @app.before_request
    def load_cart_count() -> None:
        session.setdefault("cart", {})
        g.cart_count = sum(session["cart"].values())

    @app.context_processor
    def inject_globals() -> dict:
        return {
            "cart_count": g.get("cart_count", 0),
            "year": datetime.utcnow().year,
        }

    @app.get("/")
    def index():
        products = fetch_products()
        featured = products[:3]
        return render_template("index.html", products=products, featured=featured)

    @app.get("/product/<int:product_id>")
    def product_details(product_id: int):
        product = fetch_product(product_id)
        if not product:
            flash("Товар не найден", "error")
            return redirect(url_for("index"))
        return render_template("product.html", product=product)

    @app.post("/cart/add/<int:product_id>")
    def add_to_cart(product_id: int):
        if not fetch_product(product_id):
            return jsonify({"ok": False, "message": "Товар не найден"}), 404
        cart = session.setdefault("cart", {})
        key = str(product_id)
        cart[key] = cart.get(key, 0) + 1
        session.modified = True
        return jsonify({"ok": True, "cart_count": sum(cart.values())})

    @app.post("/cart/remove/<int:product_id>")
    def remove_from_cart(product_id: int):
        cart = session.setdefault("cart", {})
        key = str(product_id)
        if key in cart:
            if cart[key] <= 1:
                del cart[key]
            else:
                cart[key] -= 1
            session.modified = True
        return redirect(url_for("cart"))

    @app.get("/cart")
    def cart():
        cart_items = build_cart_items(session.get("cart", {}))
        subtotal = sum(item["sum"] for item in cart_items)
        return render_template("cart.html", cart_items=cart_items, subtotal=subtotal)

    @app.post("/checkout")
    def checkout():
        cart_items = build_cart_items(session.get("cart", {}))
        if not cart_items:
            flash("Корзина пуста", "error")
            return redirect(url_for("cart"))

        customer_name = request.form.get("customer_name", "").strip()
        customer_phone = request.form.get("customer_phone", "").strip()
        note = request.form.get("note", "").strip()

        if not customer_name or not customer_phone:
            flash("Укажите имя и телефон", "error")
            return redirect(url_for("cart"))

        subtotal = sum(item["sum"] for item in cart_items)
        order_id = create_order(cart_items, subtotal, customer_name, customer_phone, note)
        payment_link = create_payment_stub(order_id, subtotal)
        session["cart"] = {}
        flash("Заказ создан. Переходите к оплате.", "success")
        return render_template(
            "checkout_success.html",
            order_id=order_id,
            payment_link=payment_link,
            subtotal=subtotal,
        )

    @app.post("/webhook/yookassa")
    def yookassa_webhook():
        # Реальная интеграция требует проверки подписи от YooKassa.
        payload = request.get_json(silent=True) or {}
        event = payload.get("event", "unknown")
        metadata = payload.get("object", {}).get("metadata", {})
        order_id = metadata.get("order_id")

        if event == "payment.succeeded" and order_id:
            mark_order_paid(order_id)

        return "", 204

    def admin_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("admin_authorized"):
                return redirect(url_for("admin_login"))
            return view(*args, **kwargs)

        return wrapped

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            valid = username == app.config["ADMIN_USERNAME"] and check_password_hash(
                app.config["ADMIN_PASSWORD_HASH"], password
            )
            if valid:
                session["admin_authorized"] = True
                return redirect(url_for("admin_dashboard"))
            flash("Неверные данные", "error")
        return render_template("admin_login.html")

    @app.post("/admin/logout")
    def admin_logout():
        session.pop("admin_authorized", None)
        return redirect(url_for("admin_login"))

    @app.get("/admin")
    @admin_required
    def admin_dashboard():
        products = fetch_products()
        orders = fetch_orders()
        return render_template("admin.html", products=products, orders=orders)

    @app.post("/admin/product/create")
    @admin_required
    def admin_product_create():
        create_product(
            title=request.form.get("title", ""),
            price=int(request.form.get("price", 0)),
            image=request.form.get("image", ""),
            description=request.form.get("description", ""),
        )
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/product/update/<int:product_id>")
    @admin_required
    def admin_product_update(product_id: int):
        update_product(
            product_id=product_id,
            title=request.form.get("title", ""),
            price=int(request.form.get("price", 0)),
            image=request.form.get("image", ""),
            description=request.form.get("description", ""),
        )
        return redirect(url_for("admin_dashboard"))

    return app


def get_db() -> sqlite3.Connection:
    conn = getattr(g, "_db", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g._db = conn
    return conn


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price INTEGER NOT NULL,
            image TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            items_json TEXT NOT NULL,
            total INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL
        );
        """
    )

    count = conn.execute("SELECT COUNT(*) as c FROM products").fetchone()["c"]
    if count == 0:
        conn.executemany(
            "INSERT INTO products(title, price, image, description) VALUES (?, ?, ?, ?)",
            [
                (
                    "Prod. 92099",
                    8000,
                    "https://images.unsplash.com/photo-1617137968427-85924c800a22?auto=format&fit=crop&w=900&q=80",
                    "Минималистичный образ для городской среды.",
                ),
                (
                    "Prod. 81011",
                    21000,
                    "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80",
                    "Светлый комплект для контраста с коллекцией black-core.",
                ),
                (
                    "Prod. 2198",
                    30000,
                    "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=900&q=80",
                    "Утеплённый сет с архитектурным силуэтом.",
                ),
            ],
        )

    conn.commit()
    conn.close()


def fetch_products():
    return get_db().execute("SELECT * FROM products ORDER BY id DESC").fetchall()


def fetch_product(product_id: int):
    return get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()


def create_product(title: str, price: int, image: str, description: str) -> None:
    get_db().execute(
        "INSERT INTO products(title, price, image, description) VALUES(?, ?, ?, ?)",
        (title, price, image, description),
    )
    get_db().commit()


def update_product(product_id: int, title: str, price: int, image: str, description: str) -> None:
    get_db().execute(
        """
        UPDATE products
        SET title = ?, price = ?, image = ?, description = ?
        WHERE id = ?
        """,
        (title, price, image, description, product_id),
    )
    get_db().commit()


def build_cart_items(raw_cart: dict):
    items = []
    for product_id, qty in raw_cart.items():
        product = fetch_product(int(product_id))
        if not product:
            continue
        items.append(
            {
                "product": product,
                "qty": qty,
                "sum": product["price"] * qty,
            }
        )
    return items


def create_order(cart_items, total, customer_name, customer_phone, note):
    cursor = get_db().execute(
        """
        INSERT INTO orders(items_json, total, customer_name, customer_phone, note, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'pending_payment', ?)
        """,
        (
            json.dumps(
                [
                    {
                        "product_id": item["product"]["id"],
                        "title": item["product"]["title"],
                        "price": item["product"]["price"],
                        "qty": item["qty"],
                    }
                    for item in cart_items
                ],
                ensure_ascii=False,
            ),
            total,
            customer_name,
            customer_phone,
            note,
            datetime.utcnow().isoformat(),
        ),
    )
    get_db().commit()
    return cursor.lastrowid


def create_payment_stub(order_id: int, total: int) -> str:
    # Здесь можно вызвать YooKassa/Tinkoff API и вернуть confirmation_url.
    return f"https://pay.example.com/checkout?order_id={order_id}&amount={total}"


def fetch_orders():
    return get_db().execute("SELECT * FROM orders ORDER BY id DESC LIMIT 30").fetchall()


def mark_order_paid(order_id: int) -> None:
    get_db().execute("UPDATE orders SET status='paid' WHERE id = ?", (order_id,))
    get_db().commit()


app = create_app()


@app.teardown_appcontext
def close_db(exc):
    conn = getattr(g, "_db", None)
    if conn is not None:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
