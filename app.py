from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import random
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'shakil_boot_house_secret_key_2026'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_PATH = os.path.join('database', 'products.json')
COLORS_PATH = os.path.join('database', 'colors.json')
ADMIN_PATH = os.path.join('database', 'admin.json')
ORDERS_PATH = os.path.join('database', 'orders.json')

os.makedirs('database', exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(COLORS_PATH) or os.path.getsize(COLORS_PATH) == 0:
    default_colors = ["Black", "Brown", "White", "Navy Blue", "Tan", "Maroon", "Grey", "Red", "Off White", "Sakib"]
    with open(COLORS_PATH, 'w', encoding='utf-8') as f:
        json.dump(default_colors, f)

if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(ORDERS_PATH) or os.path.getsize(ORDERS_PATH) == 0:
    with open(ORDERS_PATH, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(ADMIN_PATH) or os.path.getsize(ADMIN_PATH) == 0:
    default_admin = {
        "username": "sadman sakib",
        "password": "sakib1999@@"
    }
    with open(ADMIN_PATH, 'w', encoding='utf-8') as f:
        json.dump(default_admin, f, indent=4)

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
            except json.JSONDecodeError:
                return []
    return []

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

CATEGORIES_DATA = {
    "Men": ["Formal Shoes", "Casual Shoes", "Boots", "Canvas", "Sports Shoes", "Sandals", "Sports Sandals"],
    "Women": ["Heels", "Sandals", "Sports Shoe", "Canvas", "Jutti", "Pumpies"],
    "Kids": ["Shoes", "Sports Shoes", "Sandals", "School Shoes"]
}

BRANDS_LIST = ["Liberty", "Sardar", "Lotus", "Chinese", "Bata", "Apex"]

@app.route('/')
def home():
    products = load_json(DB_PATH)
    
    gender_filter = request.args.get('gender', '')
    cat_filter = request.args.get('category', '')
    brand_filter = request.args.get('brand', '')
    size_filter = request.args.get('size', '')
    color_filter = request.args.get('color', '')
    search_query = request.args.get('q', '').lower()
    
    if gender_filter == 'Kids' and not brand_filter:
        brand_filter = 'Chinese'

    if gender_filter:
        products = [p for p in products if p.get('gender') == gender_filter]
    if cat_filter:
        products = [p for p in products if p.get('sub_category') == cat_filter]
    if brand_filter:
        products = [p for p in products if p.get('brand') == brand_filter]
    if size_filter:
        products = [p for p in products if size_filter in p.get('sizes', [])]
    if color_filter:
        products = [p for p in products if color_filter in p.get('colors', [])]
    if search_query:
        products = [p for p in products if search_query in p.get('name', '').lower() or search_query in p.get('product_code', '').lower()]

    colors_list = load_json(COLORS_PATH)
    
    if gender_filter == 'Kids':
        available_sizes = ["21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36"]
    else:
        available_sizes = ["36", "37", "38", "39", "40", "41", "42", "43", "44"]
    
    return render_template('index.html', 
                           products=products, 
                           gender=gender_filter, 
                           category=cat_filter, 
                           brand=brand_filter,
                           selected_size=size_filter,
                           selected_color=color_filter,
                           colors_list=colors_list,
                           brands_list=BRANDS_LIST,
                           available_sizes=available_sizes)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    products = load_json(DB_PATH)
    product = next((p for p in products if p.get('id') == product_id), None)
    
    if not product:
        return redirect(url_for('home'))
        
    img_list = []
    if product.get('img'):
        img_list.append(product.get('img'))
    if product.get('images'):
        for im in product.get('images'):
            if im and im not in img_list:
                img_list.append(im)
    product['all_images'] = img_list
        
    selected_color = request.args.get('color', product.get('colors', [''])[0])
    return render_template('product_detail.html', product=product, selected_color=selected_color)

@app.route('/order/<int:product_id>')
def order_page(product_id):
    products = load_json(DB_PATH)
    product = next((p for p in products if p.get('id') == product_id), None)
    
    if not product:
        return redirect(url_for('home'))
        
    price = product.get('price', 0)
    discount = product.get('discount_pct', 0)
    if discount > 0:
        final_price = int(price - (price * discount / 100))
    else:
        final_price = int(price)
        
    selected_color = request.args.get('color', product.get('colors', [''])[0])
    selected_size = request.args.get('size', product.get('sizes', [''])[0])
    quantity = int(request.args.get('qty', 1))
    
    return render_template('order.html', product=product, final_price=final_price, selected_color=selected_color, selected_size=selected_size, quantity=quantity)

@app.route('/order/confirm/<int:product_id>', methods=['POST'])
def confirm_order(product_id):
    products = load_json(DB_PATH)
    product = next((p for p in products if p.get('id') == product_id), None)
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    location = request.form.get('location')
    address = request.form.get('address')
    color = request.form.get('color')
    size = request.form.get('size')
    quantity = int(request.form.get('quantity', 1))
    
    price = product.get('price', 0) if product else 0
    discount = product.get('discount_pct', 0) if product else 0
    final_price = int(price - (price * discount / 100)) if discount > 0 else int(price)
    delivery_charge = 60 if location == 'Inside Rangpur' else 130
    total_amount = (final_price * quantity) + delivery_charge

    orders = load_json(ORDERS_PATH)
    
    new_order = {
        "order_id": f"SBH-{random.randint(1000, 9999)}",
        "product_name": product.get('name') if product else "Unknown",
        "product_code": product.get('product_code') if product else "N/A",
        "product_img": product.get('img') if product else "",
        "name": name,
        "phone": phone,
        "location": location,
        "address": address,
        "color": color,
        "size": size,
        "quantity": quantity,
        "total_amount": total_amount
    }
    
    orders.insert(0, new_order)
    save_json(ORDERS_PATH, orders)
    
    return render_template('order_success.html', order=new_order)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with open(ADMIN_PATH, 'r', encoding='utf-8') as f:
            admin_data = json.load(f)
        
        if username == admin_data.get('username') and password == admin_data.get('password'):
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error='Invalid Username or Password!')
    return render_template('admin_login.html')

@app.route('/admin/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        with open(ADMIN_PATH, 'r', encoding='utf-8') as f:
            admin_data = json.load(f)
            
        if username == admin_data.get('username') and current_password == admin_data.get('password'):
            admin_data['password'] = new_password
            with open(ADMIN_PATH, 'w', encoding='utf-8') as f:
                json.dump(admin_data, f, indent=4)
            return render_template('admin_change_password.html', success='Password updated successfully!')
        else:
            return render_template('admin_change_password.html', error='Invalid Username or Current Password!')
            
    return render_template('admin_change_password.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('home'))

@app.route('/admin')
@login_required
def admin():
    products = load_json(DB_PATH)
    colors = load_json(COLORS_PATH)
    return render_template('admin.html', products=products, colors=colors)

@app.route('/admin/orders')
@login_required
def admin_orders():
    orders = load_json(ORDERS_PATH)
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/colors', methods=['POST'])
@login_required
def manage_colors():
    colors = load_json(COLORS_PATH)
    new_color = request.form.get('new_color')
    if new_color and new_color.strip() not in colors:
        colors.append(new_color.strip())
        save_json(COLORS_PATH, colors)
    return redirect(url_for('admin'))

@app.route('/admin/colors/delete/<color_name>')
@login_required
def delete_color(color_name):
    colors = load_json(COLORS_PATH)
    if color_name in colors:
        colors.remove(color_name)
        save_json(COLORS_PATH, colors)
    return redirect(url_for('admin'))

@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def admin_add():
    colors = load_json(COLORS_PATH)
    gender = request.args.get('gender', 'Men')
    
    if gender == 'Kids':
        available_sizes = ["21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36"]
    else:
        available_sizes = ["36", "37", "38", "39", "40", "41", "42", "43", "44"]
    
    if request.method == 'POST':
        products = load_json(DB_PATH)
        
        file = request.files.get('img_file')
        img_url = ""
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_url = url_for('static', filename=f'uploads/{filename}')
        else:
            img_url = request.form.get('img_url', '')

        additional_images = []
        files = request.files.getlist('images')
        for f in files:
            if f and f.filename != '':
                fname = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                additional_images.append(url_for('static', filename=f'uploads/{fname}'))

        new_product = {
            "id": len(products) + 1,
            "product_code": request.form.get('product_code'),
            "name": request.form.get('name'),
            "gender": gender,
            "sub_category": request.form.get('sub_category'),
            "brand": request.form.get('brand'),
            "price": int(request.form.get('price', 0)),
            "colors": request.form.getlist('colors'),
            "sizes": request.form.getlist('sizes'),
            "discount_pct": 0,
            "img": img_url,
            "images": additional_images
        }
        
        products.append(new_product)
        save_json(DB_PATH, products)
        return redirect(url_for('admin_manage'))

    sub_cat = request.args.get('sub_cat', '')
    sub_categories = CATEGORIES_DATA.get(gender, [])
    
    return render_template('admin_add.html', 
                           gender=gender, 
                           sub_categories=sub_categories, 
                           selected_sub=sub_cat,
                           brands=BRANDS_LIST,
                           colors=colors,
                           available_sizes=available_sizes)

@app.route('/admin/manage', methods=['GET', 'POST'])
@login_required
def admin_manage():
    products = load_json(DB_PATH)
    
    gender_filter = request.args.get('gender', '')
    cat_filter = request.args.get('category', '')
    brand_filter = request.args.get('brand', '')
    
    filtered_products = products
    if gender_filter:
        filtered_products = [p for p in filtered_products if p.get('gender') == gender_filter]
    if cat_filter:
        filtered_products = [p for p in filtered_products if p.get('sub_category') == cat_filter]
    if brand_filter:
        filtered_products = [p for p in filtered_products if p.get('brand') == brand_filter]
        
    return render_template('admin_manage.html', 
                           products=filtered_products, 
                           total_products=len(products),
                           gender=gender_filter, 
                           category=cat_filter, 
                           brand=brand_filter,
                           categories_data=CATEGORIES_DATA,
                           brands_list=BRANDS_LIST)

@app.route('/admin/discount-policy', methods=['GET', 'POST'])
@login_required
def discount_policy():
    products = load_json(DB_PATH)
    
    if request.method == 'POST':
        discount_type = request.form.get('discount_type')
        discount_pct = int(request.form.get('discount_pct', 0))
        selected_ids = [int(i) for i in request.form.getlist('product_ids')]
        
        for p in products:
            if discount_type == 'all':
                p['discount_pct'] = discount_pct
            elif discount_type == 'manual':
                if p['id'] in selected_ids:
                    p['discount_pct'] = discount_pct
        
        save_json(DB_PATH, products)
        return redirect(url_for('discount_policy'))
        
    return render_template('admin_discount.html', products=products)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    products = load_json(DB_PATH)
    colors = load_json(COLORS_PATH)
    product = next((p for p in products if p.get('id') == product_id), None)
    
    if not product:
        return redirect(url_for('admin_manage'))
        
    if request.method == 'POST':
        product['product_code'] = request.form.get('product_code')
        product['name'] = request.form.get('name')
        product['price'] = int(request.form.get('price', 0))
        product['brand'] = request.form.get('brand')
        product['colors'] = request.form.getlist('colors')
        product['discount_pct'] = int(request.form.get('discount_pct', 0))
        
        sizes_input = request.form.getlist('sizes')
        if "All" in sizes_input:
            product['sizes'] = ["36", "37", "38", "39", "40", "41", "42", "43", "44"]
        else:
            product['sizes'] = [s.strip() for s in request.form.get('manual_sizes', '').split(',') if s.strip()]
            
        save_json(DB_PATH, products)
        return redirect(url_for('admin_manage'))
        
    return render_template('admin_edit.html', product=product, colors=colors, brands=BRANDS_LIST)

@app.route('/admin/product/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    products = load_json(DB_PATH)
    products = [p for p in products if p.get('id') != product_id]
    save_json(DB_PATH, products)
    return redirect(url_for('admin_manage'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)