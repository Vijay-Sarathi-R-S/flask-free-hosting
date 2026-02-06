from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'this-is-my-gym-diet-app-secret-2025'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create db instance
db = SQLAlchemy(app)

# Define the model right here (no separate file needed)
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100))
    item_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Food data
foods = {
    'morning': {
        'weight_gain': [
            {'name': 'Oatmeal with Nuts & Banana', 'price': 180, 'desc': 'High-calorie breakfast for bulking', 'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800'},
            {'name': 'Protein Pancakes', 'price': 220, 'desc': 'Whey protein + oats', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800'},
            {'name': 'Eggs & Whole Wheat Toast', 'price': 190, 'desc': 'Protein + carbs', 'image': 'https://images.unsplash.com/photo-1525351326368-efbb5cb6814d?w=800'}
        ],
        'weight_loss': [
            {'name': 'Green Smoothie Bowl', 'price': 120, 'desc': 'Spinach, kale, low-fat yogurt', 'image': 'https://images.unsplash.com/photo-1546039907-7fa05f864c02?w=800'},
            {'name': 'Boiled Egg Whites', 'price': 100, 'desc': 'High protein, low calorie', 'image': 'https://images.unsplash.com/photo-1582728720176-0f7e5e0e5c0e?w=800'},
            {'name': 'Oats with Berries', 'price': 140, 'desc': 'Light and filling', 'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800'}
        ]
    },
    'afternoon': {
        'weight_gain': [
            {'name': 'Chicken Rice Bowl', 'price': 280, 'desc': 'Grilled chicken + brown rice', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800'},
            {'name': 'Peanut Butter Banana Sandwich', 'price': 200, 'desc': 'Calorie dense snack', 'image': 'https://images.unsplash.com/photo-1559054663-e8d23213f55c?w=800'},
            {'name': 'Tuna Salad Wrap', 'price': 250, 'desc': 'Protein + healthy fats', 'image': 'https://images.unsplash.com/photo-1627308594178-35e991e28a0a?w=800'}
        ],
        'weight_loss': [
            {'name': 'Grilled Chicken Salad', 'price': 180, 'desc': 'Low-fat dressing', 'image': 'https://images.unsplash.com/photo-1505253758473-96b7015fcd40?w=800'},
            {'name': 'Vegetable Stir Fry', 'price': 150, 'desc': 'No oil, high fiber', 'image': 'https://images.unsplash.com/photo-1511688878353-3a2f5be94cd7?w=800'},
            {'name': 'Quinoa & Veggie Bowl', 'price': 200, 'desc': 'Balanced & light', 'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800'}
        ]
    },
    'evening': {
        'weight_gain': [
            {'name': 'Beef & Sweet Potato', 'price': 320, 'desc': 'High protein & carbs', 'image': 'https://images.unsplash.com/photo-1606857521015-7f9fcf423740?w=800'},
            {'name': 'Mass Gainer Shake', 'price': 250, 'desc': 'Quick post-workout calories', 'image': 'https://images.unsplash.com/photo-1570545887596-2a6a3e0e4a9a?w=800'},
            {'name': 'Greek Yogurt with Honey & Nuts', 'price': 220, 'desc': 'Recovery meal', 'image': 'https://images.unsplash.com/photo-1562440499-64c9a0a8c0e9?w=800'}
        ],
        'weight_loss': [
            {'name': 'Grilled Fish', 'price': 220, 'desc': 'Omega-3 rich', 'image': 'https://images.unsplash.com/photo-1627308594178-35e991e28a0a?w=800'},
            {'name': 'Cottage Cheese & Cucumber', 'price': 140, 'desc': 'Low calorie protein', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800'},
            {'name': 'Herbal Tea & Fruit Plate', 'price': 90, 'desc': 'Light evening snack', 'image': 'https://images.unsplash.com/photo-1551024601-bec78aea704b?w=800'}
        ]
    }
}

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
    try:
        item = {
            'name': request.form.get('item'),
            'price': float(request.form.get('price')),
            'image': request.form.get('image')
        }
        session['cart'] = item  # single item only
        return redirect(url_for('cart'))
    except (TypeError, ValueError):
        return "Invalid selection. Please try again.", 400

@app.route('/cart')
def cart():
    cart_item = session.get('cart')
    if not cart_item:
        return redirect(url_for('home'))
    return render_template('cart.html', cart_item=cart_item, total=cart_item['price'])

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    cart_item = session.get('cart')
    if not cart_item:
        return redirect(url_for('home'))

    new_order = Order(
        item_name=cart_item['name'],
        item_price=cart_item['price']
    )
    db.session.add(new_order)
    db.session.commit()

    session.pop('cart', None)

    return redirect(url_for('confirmation', order_id=new_order.id))

@app.route('/confirmation/<int:order_id>')
def confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('confirmation.html', order=order)

if __name__ == '__main__':
    app.run(debug=True)