import threading
import time
from datetime import datetime
from db import Database
import smtplib
from email.mime.text import MIMEText

class Alert:
    ALERT_CHECK_INTERVAL = 60
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "YOURMAIL@gmail.com"
    SMTP_PASSWORD = "APPSECRETPASSORD"

    @staticmethod
    def send_alert_email(user_email, coin_id, alert_type, condition, threshold, current_value):
        subject = f"Crypto Alert: {coin_id} {alert_type} Triggered"
        body = f"""
        Your alert for {coin_id} has been triggered!
        Alert Type: {alert_type}
        Condition: {condition} {threshold}
        Current Value: {current_value}
        Time: {datetime.utcnow().isoformat()}
        """
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = Alert.SMTP_USER
        msg['To'] = user_email

        try:
            with smtplib.SMTP(Alert.SMTP_SERVER, Alert.SMTP_PORT) as server:
                server.starttls()
                server.login(Alert.SMTP_USER, Alert.SMTP_PASSWORD)
                server.send_message(msg)
            print(f"Email sent to {user_email} for {coin_id}")
        except Exception as e:
            print(f"Failed to send email to {user_email}: {e}")

    @staticmethod
    def check_alerts():
        print("checking alert")
        while True:
            try:
                alerts = Database.select(
                    table="alerts a JOIN users u ON a.user_id = u.id",
                    columns=["a.id", "a.user_id", "a.coin_id", "a.alert_type", "a.condition", "a.threshold", "u.email"],
                    condition="a.is_active = 1",
                    fetch_all=True
                )

                if not alerts:
                    time.sleep(Alert.ALERT_CHECK_INTERVAL)
                    continue

                for alert in alerts:
                    alert_id, user_id, coin_id, alert_type, condition, threshold, user_email = alert
                    ticker = Database.select(
                        table="tickers",
                        columns=["price_usd", "market_cap_usd", "volume_24h_usd"],
                        condition="coin_id = ?",
                        params=[coin_id]
                    )
                    if not ticker:
                        continue

                    price, market_cap, volume = ticker
                    current_value = {
                        "price": price,
                        "price_percent": price,  # Compare against pre-calculated threshold
                        "volume": volume,
                        "market_cap": market_cap
                    }.get(alert_type, 0)

                    triggered = (
                        (condition == "above" and current_value > threshold) or
                        (condition == "below" and current_value < threshold)
                    )

                    if triggered:
                        Alert.send_alert_email(user_email, coin_id, alert_type, condition, threshold, current_value)
                        Database.update(
                            table="alerts",
                            columns=["last_triggered_at","is_active"],
                            values=[datetime.utcnow().isoformat(), 0],
                            condition="id = ?",
                            condition_params=[alert_id]
                        )

            except Exception as e:
                print(f"Error checking alerts: {e}")

            time.sleep(Alert.ALERT_CHECK_INTERVAL)

    @staticmethod
    def start_alert_thread():
        alert_thread = threading.Thread(target=Alert.check_alerts, daemon=True)
        alert_thread.start()