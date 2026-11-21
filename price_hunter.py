import json
import os
import smtplib
import sys
import time
from datetime import datetime
from email.message import EmailMessage

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# work from the project folder, so the files are found even when windows starts the script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# email settings come from .env, the alerts come from alerts.json
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

# some websites block requests that don't look like a browser
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def log(text):
    # print it and also save it in log.txt, so you can see what happened when it ran in the background
    line = f"{datetime.now():%Y-%m-%d %H:%M} {text}"
    print(line)
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_price(url, selector):
    response = requests.get(url, headers=HEADERS, timeout=30)

    # 200 means ok, anything else means we didn't get the real product page
    if response.status_code == 404:
        raise Exception("page not found (404), check the link")
    if response.status_code != 200:
        raise Exception(f"the website blocked the request ({response.status_code}), it probably doesn't allow bots")

    soup = BeautifulSoup(response.text, "html.parser")

    price_tag = soup.select_one(selector)
    if price_tag is None:
        return None

    # keep only digits, dots and commas: "3.599,99 Lei" -> "3.599,99"
    price_text = price_tag.get_text()
    price_text = "".join(c for c in price_text if c.isdigit() or c in ".,")

    # the tag has no number in it (like "price unavailable"), so treat it like no price found
    if not any(c.isdigit() for c in price_text):
        return None

    # whichever comes last (dot or comma) is the decimal separator
    if price_text.rfind(",") > price_text.rfind("."):
        # european style "3.599,99" -> "3599.99"
        price_text = price_text.replace(".", "").replace(",", ".")
    else:
        # us style "1,299.99" -> "1299.99"
        price_text = price_text.replace(",", "")
    return float(price_text)


def send_email(drops):
    # one email with all the products that got cheaper since last time
    lines = []
    for alert, old_price, new_price in drops:
        lines.append(f"{alert['name']}: {alert['url']} - price from {old_price} to {new_price}")

    msg = EmailMessage()
    msg["Subject"] = f"Price drop! {len(drops)} product(s) got cheaper"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO
    msg.set_content("\n\n".join(lines))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


def check_price(alert):
    try:
        price = get_price(alert["url"], alert["selector"])
        if price is None:
            log(f"{alert['name']}: could not find the price, check the selector")
        return price
    except Exception as error:
        # one broken alert should not stop the others
        log(f"{alert['name']}: error: {error}")
        return None


def load_json(file_name, empty):
    if not os.path.exists(file_name):
        return empty
    with open(file_name, encoding="utf-8") as f:
        return json.load(f)


def main():
    # python price_hunter.py            -> check all alerts now (the "Check all now" button)
    # python price_hunter.py --startup  -> windows runs this when the pc starts
    if "--startup" in sys.argv:
        # give the pc a minute to connect to the internet
        time.sleep(60)

    history = load_json("history.json", {})
    drops = []

    for alert in load_json("alerts.json", []):
        price = check_price(alert)
        if price is None:
            continue

        prices = history.setdefault(alert["url"], [])
        last_price = prices[-1]["price"] if prices else None

        # only save it in the history if the price changed since last time
        if price == last_price:
            log(f"{alert['name']}: {price}, same as last time")
            continue

        prices.append({"date": f"{datetime.now():%Y-%m-%d %H:%M}", "price": price})
        if last_price is None:
            # first check, nothing to compare with yet
            log(f"{alert['name']}: first price {price}")
        elif price < last_price:
            log(f"{alert['name']}: price dropped from {last_price} to {price}")
            drops.append((alert, last_price, price))
        else:
            log(f"{alert['name']}: price went up from {last_price} to {price}")

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    if drops:
        try:
            send_email(drops)
            log(f"email sent with {len(drops)} product(s)")
        except Exception as error:
            log(f"could not send the email: {error}")


# only run the checks when this file is started directly, not when another file imports it
if __name__ == "__main__":
    main()
