import json
import os
import smtplib
import sys
import time
from datetime import datetime
from email.message import EmailMessage

import requests
from bs4 import BeautifulSoup
from dotenv import dotenv_values

# work from the program's folder, so the files are found even when windows starts it
# when it runs as PriceHunter.exe, __file__ is in a temporary folder, so use the exe's folder instead
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

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

    # 1. try the hidden product data first, it doesn't need a selector
    price = find_json_ld_price(soup)
    if price is not None:
        return price

    # 2. if the shop doesn't have it, use the selector (if the alert has one)
    if not selector:
        return None
    price_tag = soup.select_one(selector)
    if price_tag is None:
        return None
    return parse_price(price_tag.get_text())


def find_json_ld_price(soup):
    # many shops hide the product info for google in <script type="application/ld+json">
    # it looks like: {"@type": "Product", "offers": {"price": "3599.99", "priceCurrency": "RON"}}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            # strict=False because some shops (like emag) have line breaks inside the text, which normal json doesn't allow
            data = json.loads(script.get_text(), strict=False)
        except ValueError:
            continue

        # it can be one item, a list of items, or a list inside "@graph"
        if isinstance(data, dict):
            items = data.get("@graph", [data])
        else:
            items = data

        for item in items:
            if not isinstance(item, dict) or "Product" not in str(item.get("@type")):
                continue
            offers = item.get("offers")
            # some shops have a list of offers, then take the first one
            if isinstance(offers, list) and offers:
                offers = offers[0]
            if isinstance(offers, dict):
                price = offers.get("price") or offers.get("lowPrice")
                if price is not None:
                    return parse_price(str(price))
    return None


def parse_price(text):
    # keep only digits, dots and commas: "3.599,99 Lei" -> "3.599,99"
    price_text = "".join(c for c in text if c.isdigit() or c in ".,")

    # no number in it (like "price unavailable"), so treat it like no price found
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


def send_email(drops, broken):
    # one email with the products that got cheaper and the alerts that don't work anymore
    lines = []
    if drops:
        lines.append("GOT CHEAPER:")
        for alert, old_price, new_price in drops:
            lines.append(f"{alert['name']}: {alert['url']} - price from {old_price} to {new_price}")
    if broken:
        lines.append("NOT WORKING (fix the selector or the link in the app):")
        for alert, problem in broken:
            lines.append(f"{alert['name']}: {alert['url']} - {problem}")

    subject = []
    if drops:
        subject.append(f"{len(drops)} product(s) got cheaper")
    if broken:
        subject.append(f"{len(broken)} alert(s) not working")

    # read the email settings now, so changes saved in the app are used right away
    settings = dotenv_values(".env")
    email_address = settings.get("EMAIL_ADDRESS") or ""
    email_password = settings.get("EMAIL_PASSWORD") or ""

    msg = EmailMessage()
    msg["Subject"] = "Price Hunter: " + ", ".join(subject)
    msg["From"] = email_address
    msg["To"] = settings.get("EMAIL_TO") or ""
    msg.set_content("\n\n".join(lines))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_address, email_password)
        server.send_message(msg)


def check_price(alert):
    # gives back (price, None) if it worked, or (None, "what went wrong") if not
    try:
        # .get() because the selector is optional now, old alerts always have one
        price = get_price(alert["url"], alert.get("selector", ""))
    except Exception as error:
        # one broken alert should not stop the others
        return None, f"error: {error}"
    if price is None:
        if alert.get("selector"):
            return None, "could not find the price, check the selector"
        return None, "could not find the price by itself, add a price selector in the app"
    return price, None


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
    broken = []

    for alert in load_json("alerts.json", []):
        price, problem = check_price(alert)
        if price is None:
            log(f"{alert['name']}: {problem}")
            broken.append((alert, problem))
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

    if drops or broken:
        try:
            send_email(drops, broken)
            log(f"email sent: {len(drops)} cheaper, {len(broken)} not working")
        except Exception as error:
            log(f"could not send the email: {error}")


# only run the checks when this file is started directly, not when another file imports it
if __name__ == "__main__":
    main()
