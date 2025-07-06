from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import qrcode
import io
import base64
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'smart_cafe_secret_key_2024'
app.config['DATABASE'] = 'smart_cafe.db'

# Veritabanı köməkçi funksiyaları
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Cədvəlləri yarat
    conn.executescript('''
        -- İstifadəçilər cədvəli
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK (role IN ('system_admin', 'restaurant_owner')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );
        
        -- Restoranlar cədvəli
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            owner_id INTEGER NOT NULL,
            address TEXT,
            phone VARCHAR(20),
            email VARCHAR(100),
            table_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        );
        
        -- Masalar cədvəli
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            table_number INTEGER NOT NULL,
            qr_code TEXT,
            is_active BOOLEAN DEFAULT 1,
            UNIQUE(restaurant_id, table_number),
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
        );
        
        -- Menyu kateqoriyaları cədvəli
        CREATE TABLE IF NOT EXISTS menu_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
        );
        
        -- Menyu məhsulları cədvəli
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            category_id INTEGER,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            image_url VARCHAR(255),
            is_available BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id),
            FOREIGN KEY (category_id) REFERENCES menu_categories (id)
        );
        
        -- Sifarişlər cədvəli
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            table_number INTEGER NOT NULL,
            customer_name VARCHAR(100),
            total_amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'preparing', 'ready', 'served', 'cancelled')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
        );
        
        -- Sifariş məhsulları cədvəli
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        );
    ''')
    
    # Default sistem admini əlavə et
    conn.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, role) 
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin@smartcafe.com', generate_password_hash('admin123'), 'system_admin'))
    
    conn.commit()
    conn.close()

# Autentifikasiya dekoratorları
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'system_admin':
            flash('Giriş qadağandır. Admin hüquqları tələb olunur.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def restaurant_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['system_admin', 'restaurant_owner']:
            flash('Giriş qadağandır.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route-lar
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = 1', 
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Daxil oldunuz!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Yanlış istifadəçi adı və ya şifrə', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Çıxış etdiniz', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    
    if session['role'] == 'system_admin':
        # Admin paneli
        restaurants = conn.execute('''
            SELECT r.*, u.username as owner_name, 
                   COUNT(DISTINCT t.id) as table_count,
                   COUNT(DISTINCT o.id) as total_orders
            FROM restaurants r
            LEFT JOIN users u ON r.owner_id = u.id
            LEFT JOIN tables t ON r.id = t.restaurant_id AND t.is_active = 1
            LEFT JOIN orders o ON r.id = o.restaurant_id
            WHERE r.is_active = 1
            GROUP BY r.id
            ORDER BY r.created_at DESC
        ''').fetchall()
        
        users = conn.execute('''
            SELECT * FROM users WHERE role = 'restaurant_owner' AND is_active = 1
            ORDER BY created_at DESC
        ''').fetchall()
        
        conn.close()
        return render_template('admin_dashboard.html', restaurants=restaurants, users=users)
    
    else:
        # Restoran sahibi paneli
        restaurant = conn.execute('''
            SELECT * FROM restaurants WHERE owner_id = ? AND is_active = 1
        ''', (session['user_id'],)).fetchone()
        
        if not restaurant:
            conn.close()
            flash('Hesabınıza heç bir restoran təyin edilməyib', 'error')
            return render_template('no_restaurant.html')
        
        # Son sifarişlər
        recent_orders = conn.execute('''
            SELECT o.*, COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.restaurant_id = ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT 10
        ''', (restaurant['id'],)).fetchall()
        
        # Menyu məhsullarının sayı
        menu_count = conn.execute('''
            SELECT COUNT(*) as count FROM menu_items 
            WHERE restaurant_id = ? AND is_available = 1
        ''', (restaurant['id'],)).fetchone()['count']
        
        conn.close()
        return render_template('restaurant_dashboard.html', 
                             restaurant=restaurant, 
                             recent_orders=recent_orders,
                             menu_count=menu_count)

@app.route('/admin/restaurants/new', methods=['GET', 'POST'])
@admin_required
def new_restaurant():
    if request.method == 'POST':
        name = request.form['name']
        slug = request.form['slug']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        owner_id = request.form['owner_id']
        table_count = int(request.form['table_count'])
        
        conn = get_db_connection()
        try:
            # Restoran əlavə et
            cursor = conn.execute('''
                INSERT INTO restaurants (name, slug, owner_id, address, phone, email, table_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, slug, owner_id, address, phone, email, table_count))
            
            restaurant_id = cursor.lastrowid
            
            # Masalar və QR kodlar yarat
            for i in range(1, table_count + 1):
                qr_url = f"{request.url_root}{slug}/masa-{i}"
                conn.execute('''
                    INSERT INTO tables (restaurant_id, table_number, qr_code)
                    VALUES (?, ?, ?)
                ''', (restaurant_id, i, qr_url))
            
            conn.commit()
            flash('Restoran uğurla yaradıldı!', 'success')
            return redirect(url_for('dashboard'))
            
        except sqlite3.IntegrityError:
            flash('Restoran slug artıq mövcuddur', 'error')
        finally:
            conn.close()
    
    # Restoran sahiblərini götür
    conn = get_db_connection()
    owners = conn.execute('''
        SELECT * FROM users WHERE role = 'restaurant_owner' AND is_active = 1
    ''').fetchall()
    conn.close()
    
    return render_template('new_restaurant.html', owners=owners)

@app.route('/admin/users/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, 'restaurant_owner')
            ''', (username, email, generate_password_hash(password)))
            conn.commit()
            flash('Restoran sahibi uğurla yaradıldı!', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('İstifadəçi adı və ya e-poçt artıq mövcuddur', 'error')
        finally:
            conn.close()
    
    return render_template('new_user.html')

@app.route('/restaurant/menu')
@restaurant_owner_required
def menu_management():
    conn = get_db_connection()
    restaurant = conn.execute('''
        SELECT * FROM restaurants WHERE owner_id = ? AND is_active = 1
    ''', (session['user_id'],)).fetchone()
    
    if not restaurant:
        conn.close()
        flash('Restoran tapılmadı', 'error')
        return redirect(url_for('dashboard'))
    
    categories = conn.execute('''
        SELECT * FROM menu_categories WHERE restaurant_id = ? AND is_active = 1
        ORDER BY sort_order, name
    ''', (restaurant['id'],)).fetchall()
    
    menu_items = conn.execute('''
        SELECT mi.*, mc.name as category_name
        FROM menu_items mi
        LEFT JOIN menu_categories mc ON mi.category_id = mc.id
        WHERE mi.restaurant_id = ? AND mi.is_available = 1
        ORDER BY mi.sort_order, mi.name
    ''', (restaurant['id'],)).fetchall()
    
    conn.close()
    return render_template('menu_management.html', 
                         restaurant=restaurant, 
                         categories=categories, 
                         menu_items=menu_items)

@app.route('/restaurant/menu/item/new', methods=['GET', 'POST'])
@restaurant_owner_required
def new_menu_item():
    conn = get_db_connection()
    restaurant = conn.execute('''
        SELECT * FROM restaurants WHERE owner_id = ? AND is_active = 1
    ''', (session['user_id'],)).fetchone()
    
    if not restaurant:
        conn.close()
        flash('Restoran tapılmadı', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        category_id = request.form.get('category_id') or None
        
        conn.execute('''
            INSERT INTO menu_items (restaurant_id, category_id, name, description, price)
            VALUES (?, ?, ?, ?, ?)
        ''', (restaurant['id'], category_id, name, description, price))
        conn.commit()
        conn.close()
        
        flash('Menyu məhsulu uğurla əlavə edildi!', 'success')
        return redirect(url_for('menu_management'))
    
    categories = conn.execute('''
        SELECT * FROM menu_categories WHERE restaurant_id = ? AND is_active = 1
        ORDER BY sort_order, name
    ''', (restaurant['id'],)).fetchall()
    
    conn.close()
    return render_template('new_menu_item.html', categories=categories)

@app.route('/restaurant/orders')
@restaurant_owner_required
def orders():
    conn = get_db_connection()
    restaurant = conn.execute('''
        SELECT * FROM restaurants WHERE owner_id = ? AND is_active = 1
    ''', (session['user_id'],)).fetchone()
    
    if not restaurant:
        conn.close()
        flash('Restoran tapılmadı', 'error')
        return redirect(url_for('dashboard'))
    
    orders = conn.execute('''
        SELECT o.*, COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.restaurant_id = ? AND o.status != 'served'
        GROUP BY o.id
        ORDER BY o.created_at DESC
    ''', (restaurant['id'],)).fetchall()
    
    conn.close()
    return render_template('orders.html', orders=orders, restaurant=restaurant)

@app.route('/restaurant/qr-codes')
@restaurant_owner_required
def qr_codes():
    conn = get_db_connection()
    restaurant = conn.execute('''
        SELECT * FROM restaurants WHERE owner_id = ? AND is_active = 1
    ''', (session['user_id'],)).fetchone()
    
    if not restaurant:
        conn.close()
        flash('Restoran tapılmadı', 'error')
        return redirect(url_for('dashboard'))
    
    tables = conn.execute('''
        SELECT * FROM tables WHERE restaurant_id = ? AND is_active = 1
        ORDER BY table_number
    ''', (restaurant['id'],)).fetchall()
    
    # QR kodlar yarat
    qr_codes_data = []
    for table in tables:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(table['qr_code'])
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        qr_codes_data.append({
            'table_number': table['table_number'],
            'qr_url': table['qr_code'],
            'qr_image': img_str
        })
    
    conn.close()
    return render_template('qr_codes.html', restaurant=restaurant, qr_codes=qr_codes_data)

# Müştəri menyu route-ları
@app.route('/<restaurant_slug>/masa-<int:table_number>')
def customer_menu(restaurant_slug, table_number):
    conn = get_db_connection()
    restaurant = conn.execute('''
        SELECT * FROM restaurants WHERE slug = ? AND is_active = 1
    ''', (restaurant_slug,)).fetchone()
    
    if not restaurant:
        conn.close()
        return render_template('restaurant_not_found.html'), 404
    
    # Masanın olub olmadığını yoxla
    table = conn.execute('''
        SELECT * FROM tables WHERE restaurant_id = ? AND table_number = ? AND is_active = 1
    ''', (restaurant['id'], table_number)).fetchone()
    
    if not table:
        conn.close()
        return render_template('table_not_found.html'), 404
    
    categories = conn.execute('''
        SELECT * FROM menu_categories WHERE restaurant_id = ? AND is_active = 1
        ORDER BY sort_order, name
    ''', (restaurant['id'],)).fetchall()
    
    menu_items = conn.execute('''
        SELECT mi.*, mc.name as category_name
        FROM menu_items mi
        LEFT JOIN menu_categories mc ON mi.category_id = mc.id
        WHERE mi.restaurant_id = ? AND mi.is_available = 1
        ORDER BY mi.sort_order, mi.name
    ''', (restaurant['id'],)).fetchall()
    
    conn.close()
    return render_template('customer_menu.html', 
                         restaurant=restaurant, 
                         table_number=table_number,
                         categories=categories,
                         menu_items=menu_items)

@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.json
    restaurant_id = data['restaurant_id']
    table_number = data['table_number']
    customer_name = data.get('customer_name', '')
    items = data['items']
    notes = data.get('notes', '')
    
    conn = get_db_connection()
    
    # Ümumi məbləği hesabla
    total_amount = 0
    for item in items:
        menu_item = conn.execute('''
            SELECT price FROM menu_items WHERE id = ?
        ''', (item['menu_item_id'],)).fetchone()
        total_amount += menu_item['price'] * item['quantity']
    
    # Sifariş yarat
    cursor = conn.execute('''
        INSERT INTO orders (restaurant_id, table_number, customer_name, total_amount, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (restaurant_id, table_number, customer_name, total_amount, notes))
    
    order_id = cursor.lastrowid
    
    # Sifariş məhsullarını əlavə et
    for item in items:
        menu_item = conn.execute('''
            SELECT price FROM menu_items WHERE id = ?
        ''', (item['menu_item_id'],)).fetchone()
        
        conn.execute('''
            INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, item['menu_item_id'], item['quantity'], 
              menu_item['price'], item.get('notes', '')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'order_id': order_id})

@app.route('/api/orders/<int:restaurant_id>')
@restaurant_owner_required
def get_orders(restaurant_id):
    conn = get_db_connection()
    
    # Restoran sahibliyini yoxla
    restaurant = conn.execute('''
        SELECT * FROM restaurants WHERE id = ? AND owner_id = ?
    ''', (restaurant_id, session['user_id'])).fetchone()
    
    if not restaurant and session['role'] != 'system_admin':
        conn.close()
        return jsonify({'error': 'Giriş qadağandır'}), 403
    
    orders = conn.execute('''
        SELECT o.*, 
               GROUP_CONCAT(mi.name || ' x' || oi.quantity) as items_summary
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE o.restaurant_id = ? AND o.status != 'served'
        GROUP BY o.id
        ORDER BY o.created_at DESC
    ''', (restaurant_id,)).fetchall()
    
    conn.close()
    
    orders_list = []
    for order in orders:
        orders_list.append({
            'id': order['id'],
            'table_number': order['table_number'],
            'customer_name': order['customer_name'],
            'total_amount': order['total_amount'],
            'status': order['status'],
            'items_summary': order['items_summary'],
            'notes': order['notes'],
            'created_at': order['created_at']
        })
    
    return jsonify(orders_list)

@app.route('/api/order/<int:order_id>/status', methods=['PUT'])
@restaurant_owner_required
def update_order_status(order_id):
    data = request.json
    new_status = data['status']
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_status, order_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)