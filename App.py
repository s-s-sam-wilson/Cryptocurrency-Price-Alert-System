from flask import Flask, request, render_template, redirect, url_for, session, flash
from db import Database
from user import User
from tickers import Ticker
from alerts import Alert

app = Flask(__name__)
app.secret_key = "mysecretkey123"

Database.initdb()

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'userid' not in session:
        return redirect(url_for('login'))

    user = User.get_user_by_id(session['userid'])
    if not user:
        session.pop("userid", None)
        return redirect(url_for('login'))

    # Get top 10 tickers for display
    top_tickers = Database.select(
        table="tickers",
        columns=["coin_id", "name", "symbol", "price_usd", "market_cap_usd", "volume_24h_usd", "rank"],
        condition="1=1 ORDER BY rank ASC LIMIT 10",
        fetch_all=True
    )

    # Get all tickers for alert selection
    all_tickers = Database.select(
        table="tickers",
        columns=["coin_id", "name", "symbol"],
        condition="1=1 ORDER BY name ASC",
        fetch_all=True
    )

    # Get user's active alerts
    user_alerts = Database.select(
        table="alerts",
        columns=["id", "coin_id", "alert_type", "condition", "threshold", "percentage", "last_triggered_at"],
        condition="user_id = ? AND is_active = 1",
        params=[session['userid']],
        fetch_all=True
    )

    if request.method == 'POST':
        coin_id = request.form['coin_id']
        alert_type = request.form['alert_type']
        condition = request.form['condition']
        threshold_input = float(request.form['threshold'])

        # Get current price for percentage calculation
        if alert_type == "price_percent":
            current_ticker = Database.select(
                table="tickers",
                columns=["price_usd"],
                condition="coin_id = ?",
                params=[coin_id]
            )
            if current_ticker:
                current_price = current_ticker[0]
                percentage = threshold_input  # User inputs percentage (e.g., 5 for 5%)
                # Calculate threshold: current_price * (1 + percentage/100) for 'above', or * (1 - percentage/100) for 'below'
                threshold = current_price * (1 + percentage / 100) if condition == "above" else current_price * (1 - percentage / 100)
            else:
                flash("Error: Coin data not found.")
                return redirect(url_for('index'))
        else:
            threshold = threshold_input  # For non-percentage alerts, use input directly
            percentage = None  # No percentage for other alert types

        # Insert alert with threshold and percentage
        Database.insert(
            table="alerts",
            columns=["user_id", "coin_id", "alert_type", "condition", "threshold", "percentage"],
            values=[session['userid'], coin_id, alert_type, condition, threshold, percentage]
        )
        flash("Alert added successfully!")
        return redirect(url_for('index'))

    return render_template('home.html',
                         username=user[1],
                         tickers=top_tickers,
                         all_tickers=all_tickers,
                         alerts=user_alerts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.check_user(email, password)
        if user:
            session['userid'] = user[0]
            return redirect(url_for('index'))
        else:
            return "Wrong email or password! Try again."

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if len(username) < 3:
            flash("Username must be at least 3 characters long")
            return render_template('signup.html')

        if User.is_valid_password(email):
            flash("Please enter a valid email address.")
            return render_template('signup.html')

        if User.email_exists(email):
            flash("Email already taken! Try a different one.")
            return render_template('signup.html')


        if User.is_valid_password(password):
            flash("Password must contain at least 8 characters, including one uppercase letter, one lowercase letter, one number, and one special character (@$!%*?&)")
            return render_template('signup.html')

        User.add_user(username, email, password)
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    Ticker.start_ticker_thread()
    Alert.start_alert_thread()
    app.run(debug=True)