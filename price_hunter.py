import os
import smtplib
from email.message import EmailMessage

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# load the settings from the .env file
load_dotenv()

PRODUCT_URL = os.getenv("PRODUCT_URL")
TARGET_PRICE = float(os.getenv("TARGET_PRICE"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

# the css selector of the price on the page
# change this if the website changes its layout
PRICE_SELECTOR = os.getenv("PRICE_SELECTOR", ".price")

# some websites block requests that don't look like a browser
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get_price():
    response = requests.get(PRODUCT_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    price_tag = soup.select_one(PRICE_SELECTOR)
    if price_tag is None:
        print("Could not find the price, check PRICE_SELECTOR")
        return None

    # keep only digits, dots and commas: "3.599,99 Lei" -> "3.599,99"
    price_text = price_tag.get_text()
    price_text = "".join(c for c in price_text if c.isdigit() or c in ".,")

    # whichever comes last (dot or comma) is the decimal separator
    if price_text.rfind(",") > price_text.rfind("."):
        # european style "3.599,99" -> "3599.99"
        price_text = price_text.replace(".", "").replace(",", ".")
    else:
        # us style "1,299.99" -> "1299.99"
        price_text = price_text.replace(",", "")
    return float(price_text)


def send_email(price):
    msg = EmailMessage()
    msg["Subject"] = f"Price drop! Now {price}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO
    msg.set_content(f"The price is now {price} (your target was {TARGET_PRICE}).\n\n{PRODUCT_URL}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


price = get_price()
if price is not None:
    print(f"Current price: {price}")
    if price < TARGET_PRICE:
        send_email(price)
        print("Email sent!")
    else:
        print(f"Still too expensive: {price} > {TARGET_PRICE}")
