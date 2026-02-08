from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random
import time
import uuid


app = Flask(__name__)
app.secret_key = 'this-is-my-gym-diet-app-secret-2025'

# =========================
# DATABASE CONFIG
# =========================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# =========================
# DATABASE MODELS
# =========================
class Order(db.Model):
    __tablename__ = 'orders'   # IMPORTANT
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    item_name = db.Column(db.String(100))
    item_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Payment(db.Model):
    __tablename__ = 'payments'   # IMPORTANT
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    transaction_id = db.Column(db.String(50), unique=True)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20))
    method = db.Column(db.String(20))   # UPI / CARD / COD
    created_at = db.Column(db.DateTime, server_default=db.func.now())




with app.app_context():
    db.create_all()

# =========================
# LOCAL PAYMENT ENGINE (REALISTIC SIMULATION)
# =========================
def local_payment_gateway(amount, method):
    time.sleep(1.5)  # simulate processing delay

    if method == "UPI":
        # UPI: very high success rate, rare pending/failure
        status = random.choices(
            ["SUCCESS", "PENDING", "FAILED"],
            weights=[88, 7, 5]
        )[0]

    elif method == "CARD":
        # Card: success + possible failure + some pending
        status = random.choices(
            ["SUCCESS", "FAILED", "PENDING"],
            weights=[70, 20, 10]
        )[0]

    elif method == "COD":
        # COD: always confirmed but payment pending
        status = "PENDING"

    else:
        status = "FAILED"

    txn_id = f"TXN{random.randint(100000, 999999)}"
    return txn_id, status


# =========================
# FOOD DATA
# =========================
foods = {
    'morning': {
        'weight_gain': [
            {'name': 'Oatmeal with Nuts & Banana', 'price': 180, 'desc': 'High-calorie breakfast', 'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800'},
            {'name': 'Protein Pancakes', 'price': 220, 'desc': 'Whey protein + oats', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800'},
            {'name': 'Eggs & Whole Wheat Toast', 'price': 190, 'desc': 'Protein + carbs', 'image': 'https://images.unsplash.com/photo-1525351326368-efbb5cb6814d?w=800'}
        ],
        'weight_loss': [
            {'name': 'Green Smoothie Bowl', 'price': 120, 'desc': 'Low calorie', 'image': 'https://images.unsplash.com/photo-1546039907-7fa05f864c02?w=800'},
            {'name': 'Boiled Egg Whites', 'price': 100, 'desc': 'High protein', 'image': 'https://images.unsplash.com/photo-1582728720176-0f7e5e0e5c0e?w=800'},
            {'name': 'Oats with Berries', 'price': 140, 'desc': 'Light meal', 'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800'}
        ]
    }
}

# =========================
# ROUTES
# =========================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    goal = request.form.get('goal')
    time_of_day = request.form.get('time')

    if not goal or not time_of_day:
        return redirect(url_for('home'))

    menu = foods.get(time_of_day, {}).get(goal, [])
    return render_template('menu.html', menu=menu, goal=goal.capitalize(), time=time_of_day.capitalize())

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item = {
        'name': request.form.get('item'),
        'price': float(request.form.get('price')),
        'image': request.form.get('image')
    }
    session['cart'] = item
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_item = session.get('cart')
    if not cart_item:
        return redirect(url_for('home'))
    return render_template('cart.html', cart_item=cart_item, total=cart_item['price'])

# =========================
# PAYMENT FLOW
# =========================

# Step 1 → Click Pay
@app.route('/pay', methods=['POST'])
def pay():
    return redirect(url_for('payment_page'))

# Step 2 → Payment UI
@app.route('/payment_page')
def payment_page():
    cart_item = session.get('cart')
    if not cart_item:
        return redirect(url_for('home'))
    return render_template('payment_page.html', cart_item=cart_item)

# Step 3 → Process Payment
@app.route('/process_payment', methods=['POST'])
def process_payment():
    cart_item = session.get('cart')
    if not cart_item:
        return redirect(url_for('home'))

    amount = cart_item['price']
    method = request.form.get('method')  # UPI / CARD / COD (UI simulation)
    user_id = session.get('user_id')

    # Create Order
    new_order = Order(
        user_id=user_id,
        item_name=cart_item['name'],
        item_price=amount
    )
    db.session.add(new_order)
    db.session.commit()

    # Local Payment Engine (fake gateway simulation)
    txn_id, status = local_payment_gateway(amount, method)

    # Store Payment
    payment = Payment(
        order_id=new_order.id,
        user_id=user_id,
        transaction_id=txn_id,
        amount=amount,
        status=status,
        method=method
    )
    db.session.add(payment)
    db.session.commit()

    # Clear cart
    session.pop('cart', None)

    return redirect(url_for('payment_result', payment_id=payment.id))

@app.route('/my_orders')
def my_orders():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('home'))

    orders = (
        db.session.query(Order, Payment)
        .join(Payment, Payment.order_id == Order.id)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return render_template('my_orders.html', orders=orders)

@app.before_request
def create_user_session():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

# Step 4 → Result Page
@app.route('/payment_result/<int:payment_id>')
def payment_result(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    order = Order.query.get(payment.order_id)
    return render_template('payment_result.html', payment=payment, order=order)

# =========================
if __name__ == '__main__':
    app.run(debug=True)
