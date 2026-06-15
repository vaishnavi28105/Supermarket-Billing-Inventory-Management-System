from flask import Flask, render_template, request, redirect,session
from db_config import get_db_connection

app = Flask(__name__)
app.secret_key = "supermarket_secret_key"


# ==========================
# DASHBOARD
# ==========================

@app.route('/')
def dashboard():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM sm_categories")
    total_categories = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sm_products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sm_customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sm_bills")
    total_bills = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        total_categories=total_categories,
        total_products=total_products,
        total_customers=total_customers,
        total_bills=total_bills
    )


# ==========================
# VIEW PRODUCTS
# ==========================

@app.route('/products')
def products():

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        p.product_id,
        p.product_name,
        c.category_name,
        p.price,
        p.stock_quantity,
        p.product_status
    FROM sm_products p
    JOIN sm_categories c
        ON p.category_id = c.category_id
    ORDER BY p.product_id
    """

    cursor.execute(query)
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'products.html',
        products=products
    )


# ==========================
# MAIN
# ==========================
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':

        product_name = request.form['product_name']
        category_id = request.form['category_id']
        price = request.form['price']
        stock_quantity = request.form['stock_quantity']

        if int(stock_quantity) == 0:
            status = "Out of Stock"
        elif int(stock_quantity) <= 5:
            status = "Low Stock"
        else:
            status = "Available"

        query = """
        INSERT INTO sm_products
        (product_name, category_id, price, stock_quantity, product_status)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            product_name,
            category_id,
            price,
            stock_quantity,
            status
        )

        cursor.execute(query, values)

        conn.commit()

        cursor.close()
        conn.close()

        return redirect('/products')

    cursor.execute("""
        SELECT category_id, category_name
        FROM sm_categories
    """)

    categories = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'add_product.html',
        categories=categories
    )
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':

        product_name = request.form['product_name']
        category_id = request.form['category_id']
        price = request.form['price']
        stock_quantity = request.form['stock_quantity']

        if int(stock_quantity) == 0:
            status = "Out of Stock"
        elif int(stock_quantity) <= 5:
            status = "Low Stock"
        else:
            status = "Available"

        update_query = """
        UPDATE sm_products
        SET
            product_name=%s,
            category_id=%s,
            price=%s,
            stock_quantity=%s,
            product_status=%s
        WHERE product_id=%s
        """

        values = (
            product_name,
            category_id,
            price,
            stock_quantity,
            status,
            product_id
        )

        cursor.execute(update_query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return redirect('/products')

    product_query = """
    SELECT
        product_id,
        product_name,
        category_id,
        price,
        stock_quantity
    FROM sm_products
    WHERE product_id=%s
    """

    cursor.execute(product_query, (product_id,))
    product = cursor.fetchone()

    cursor.execute("""
        SELECT category_id, category_name
        FROM sm_categories
    """)

    categories = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'edit_product.html',
        product=product,
        categories=categories
    )
@app.route('/restock_product/<int:product_id>', methods=['GET', 'POST'])
def restock_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DATABASE()")
    print("Current Database:", cursor.fetchone())

    if request.method == 'POST':

        quantity_added = int(request.form['quantity_added'])

        cursor.execute("""
            SELECT stock_quantity
            FROM sm_products
            WHERE product_id=%s
        """, (product_id,))

        current_stock = cursor.fetchone()[0]

        new_stock = current_stock + quantity_added

        if new_stock == 0:
            status = "Out of Stock"
        elif new_stock <= 5:
            status = "Low Stock"
        else:
            status = "Available"

        cursor.execute("""
            UPDATE sm_products
            SET stock_quantity=%s,
                product_status=%s
            WHERE product_id=%s
        """, (new_stock, status, product_id))

        cursor.execute("""
            INSERT INTO sm_restock_history
            (product_id, quantity_added)
            VALUES (%s, %s)
        """, (product_id, quantity_added))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect('/products')

    cursor.execute("""
        SELECT
            product_id,
            product_name,
            stock_quantity
        FROM sm_products
        WHERE product_id=%s
    """, (product_id,))

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'restock_product.html',
        product=product
    )
@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM sm_products
        WHERE product_id=%s
    """, (product_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/products')
@app.route('/billing')
def billing():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category_id, category_name
        FROM sm_categories
        ORDER BY category_name
    """)
    categories = cursor.fetchall()

    cursor.execute("""
        SELECT
            product_id,
            product_name,
            category_id,
            price,
            stock_quantity
        FROM sm_products
        ORDER BY product_name
    """)
    products = cursor.fetchall()

    cursor.close()
    conn.close()
    if 'cart' not in session:
        session['cart'] = []
    subtotal = 0

    for item in session.get('cart', []):
        subtotal += item['subtotal']

    return render_template(
        'billing.html',
        categories=categories,
        products=products,
        subtotal=subtotal
    )
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():

    session['customer_name'] = request.form['customer_name']
    session['contact'] = request.form['contact']
    session['email'] = request.form['email']
    session['payment_method'] = request.form['payment_method']

    if not request.form.get('quantity'):
        return redirect('/billing')

    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            product_id,
            product_name,
            price,
            stock_quantity
        FROM sm_products
        WHERE product_id=%s
    """, (product_id,))

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if not product:
        return redirect('/billing')

    if quantity > product[3]:
        return redirect('/billing')

    subtotal = float(product[2]) * quantity

    cart_item = {
        'product_id': product[0],
        'product_name': product[1],
        'price': float(product[2]),
        'quantity': quantity,
        'subtotal': subtotal
    }

    cart = session.get('cart', [])
    cart.append(cart_item)

    session['cart'] = cart

    return redirect('/billing')
@app.route('/remove_from_cart/<int:index>')
def remove_from_cart(index):

    cart = session.get('cart', [])

    if 0 <= index < len(cart):
        cart.pop(index)

    session['cart'] = cart

    return redirect('/billing')
@app.route('/generate_bill', methods=['POST'])
def generate_bill():

    cart = session.get('cart', [])

    if not cart:
        return redirect('/billing')

    customer_name = session.get('customer_name')
    contact = session.get('contact')
    email = session.get('email')
    payment_method = session.get('payment_method')

    discount = float(request.form.get('discount_amount', 0))

    subtotal = 0

    for item in cart:
        subtotal += item['subtotal']

    amount_after_discount = subtotal - discount

    if amount_after_discount < 0:
        amount_after_discount = 0

    gst = amount_after_discount * 0.05

    final_amount = amount_after_discount + gst

    conn = get_db_connection()
    cursor = conn.cursor()

    # CUSTOMER

    cursor.execute("""
        INSERT INTO sm_customers
        (customer_name, contact, email)
        VALUES (%s, %s, %s)
    """, (
        customer_name,
        contact,
        email
    ))

    customer_id = cursor.lastrowid

    # BILL

    cursor.execute("""
        INSERT INTO sm_bills
        (
            customer_id,
            total_amount,
            discount_amount,
            gst_amount,
            final_amount
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        customer_id,
        subtotal,
        discount,
        gst,
        final_amount
    ))

    bill_id = cursor.lastrowid

    # BILL ITEMS + STOCK UPDATE

    for item in cart:

        cursor.execute("""
            INSERT INTO sm_bill_items
            (
                bill_id,
                product_id,
                quantity,
                unit_price,
                subtotal
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            bill_id,
            item['product_id'],
            item['quantity'],
            item['price'],
            item['subtotal']
        ))

        cursor.execute("""
            UPDATE sm_products
            SET stock_quantity = stock_quantity - %s
            WHERE product_id = %s
        """, (
            item['quantity'],
            item['product_id']
        ))

    # PAYMENT

    cursor.execute("""
        INSERT INTO sm_payments
        (
            bill_id,
            payment_method
        )
        VALUES (%s, %s)
    """, (
        bill_id,
        payment_method
    ))

    conn.commit()

    cursor.close()
    conn.close()

    session['cart'] = []
    session.pop('customer_name', None)
    session.pop('contact', None)
    session.pop('email', None)
    session.pop('payment_method', None)

    return redirect(f'/receipt/{bill_id}')
@app.route('/receipt/<int:bill_id>')
def receipt(bill_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM sm_bills
        WHERE bill_id=%s
    """, (bill_id,))

    bill = cursor.fetchone()

    cursor.execute("""
        SELECT *
        FROM sm_customers
        WHERE customer_id=%s
    """, (bill['customer_id'],))

    customer = cursor.fetchone()

    cursor.execute("""
        SELECT payment_method
        FROM sm_payments
        WHERE bill_id=%s
    """, (bill_id,))

    payment = cursor.fetchone()

    cursor.execute("""
        SELECT
            p.product_name,
            bi.quantity,
            bi.unit_price,
            bi.subtotal
        FROM sm_bill_items bi
        JOIN sm_products p
            ON bi.product_id = p.product_id
        WHERE bi.bill_id=%s
    """, (bill_id,))

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'receipt.html',
        bill=bill,
        customer=customer,
        payment_method=payment['payment_method'],
        cart=items,
        subtotal=bill['total_amount'],
        discount=bill['discount_amount'],
        gst=bill['gst_amount'],
        final_amount=bill['final_amount']
    )
@app.route('/bill_history')
def bill_history():

    search = request.args.get('search', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            b.bill_id,
            c.customer_name,
            b.bill_date,
            b.final_amount
        FROM sm_bills b
        JOIN sm_customers c
        ON b.customer_id = c.customer_id
    """

    if search:

        query += """
        WHERE c.customer_name LIKE %s
        OR b.bill_id LIKE %s
        """

        cursor.execute(
            query + " ORDER BY b.bill_id DESC",
            (f"%{search}%", f"%{search}%")
        )

    else:

        cursor.execute(
            query + " ORDER BY b.bill_id DESC"
        )

    bills = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'bill_history.html',
        bills=bills,
        search=search
    )
@app.route('/reports')
def reports():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM sm_bills")
    total_bills = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sm_customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sm_products")
    total_products = cursor.fetchone()[0]

    cursor.execute("""
        SELECT IFNULL(SUM(final_amount),0)
        FROM sm_bills
    """)
    total_sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            product_name,
            stock_quantity
        FROM sm_products
        WHERE stock_quantity <= 5
    """)
    low_stock = cursor.fetchall()

    cursor.execute("""
        SELECT
            p.product_name,
            SUM(bi.quantity) AS total_sold
        FROM sm_bill_items bi
        JOIN sm_products p
            ON bi.product_id = p.product_id
        GROUP BY p.product_name
        ORDER BY total_sold DESC
        LIMIT 5
    """)
    top_products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'reports.html',
        total_bills=total_bills,
        total_customers=total_customers,
        total_products=total_products,
        total_sales=total_sales,
        low_stock=low_stock,
        top_products=top_products
    )
if __name__ == '__main__':
    app.run(debug=True)