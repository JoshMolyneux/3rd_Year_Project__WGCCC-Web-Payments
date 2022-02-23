from flask import Blueprint, render_template, redirect, request, session, flash, url_for
from datetime import datetime
from urllib.parse import urlparse
from .__init__ import sql_connect, login_required
import stripe
import os

views = Blueprint('views', __name__)

SQL_HOST = os.getenv("SQL_HOST")
SQL_PORT = int(os.getenv("SQL_PORT"))
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_DATABASE = os.getenv("SQL_DATABASE")
stripe.api_key = os.getenv('STRIPE_API_TEST_SK')

connect = sql_connect(
    SQL_HOST,
    SQL_PORT,
    SQL_USER,
    SQL_PASSWORD,
    SQL_DATABASE
)

price_dict = {
    'social': ['3', 'price_1KTT07HuaTKPzffSkYKw4EPw', 's'],
    'senior': ['4', 'price_1KTNDVHuaTKPzffS1ubgGAr7', 's'],
    'senior_edu': ['5', 'price_1KTS4HHuaTKPzffSsYTpJcNQ', 's'],
    'junior': [None, 'price_1KTOPyHuaTKPzffS5yvO1LSb', 'j'],
    'junior_dev': [None, 'price_1KTnk8HuaTKPzffSo8JBgFX2', 'j']
}


@views.route('/')
def home():
    return render_template("home.html", datetime=str(datetime.now().year))


@views.route('/subscriptions', methods=['GET', 'POST'])
def subscriptions():
    url = urlparse(request.base_url)
    hostname = url.hostname
    port = ''
    if hostname == 'localhost':
        port = ':5000'
    else:
        port = ':80'

    if request.method == "POST":
        if 'loggedin' not in session:
            flash('You must be logged in to make purchases', category='error')
            return redirect(url_for('auth.login'))

        price_id = None
        for k, v in price_dict.items():
            if request.form.get(k):
                price_id = v[1]
        if price_id is None:
            flash(
                "There was an error - please contact the system administrator",
                category='error')
            return redirect(url_for('views.home'))

        stripe_session = stripe.checkout.Session.create(
            customer_email=session['email'],
            line_items=[{
                'price': price_id,
                'quantity': 1
            }],
            metadata={'user_id': session['id']},
            mode='subscription',
            success_url='http://%s%s/success?session_id={CHECKOUT_SESSION_ID}&price_id=%s' %
            (hostname, port, price_id),
            cancel_url='http://%s%s/subscriptions' % (hostname, port)
        )
        session['stripe_session'] = stripe_session.id
        return redirect(stripe_session.url, code=303)
    return render_template("subscriptions.html", datetime=str(datetime.now().year))


@views.route('/success')
@login_required
def success():
    if 'stripe_session' not in session or 'session_id' not in request.args or session['stripe_session'] != request.args.get('session_id'):
        flash("You cannot access this page from here", category='error')
        return redirect(url_for('views.home'))
    session.pop('stripe_session', None)

    cursor = connect.cursor()
    # check if product is junior or senior
    for k, v in price_dict.items():
        if v[2] == 's':
            cursor.execute('''
                UPDATE seniors
                SET group_id = %i
                WHERE price_id = %s
                ''') % (v[0], v[1])
            connect.commit()
            cursor.close()
        elif v[2] == 'j':
            cursor.execute('''
                INSERT INTO juniors
            ''')
    # if senior, update via session['email'] (user) with new usergroup
    return render_template("success.html", datetime=str(datetime.now().year))
# @views.route('/index')
# def index():
#     return render_template("home.html", datetime=str(datetime.now().year))
#
#
# @views.route('/projects')
# def projects():
#   return render_template("projects.html", datetime=str(datetime.now().year))
#
#
# @views.route('/about')
# def about():
#     return render_template("about.html", datetime=str(datetime.now().year))
#
#
# @views.route('/contact')
# def contact():
#     return render_template("contact.html", datetime=str(datetime.now().year))
