# price-hunter

Simple python script that checks a product page and sends you an email when the price goes under the price you want.

How it works: it downloads the page with requests, finds the price with beautifulsoup, and if its lower than the target it sends an email with smtplib (gmail). thats it

to use it:

pip install -r requirements.txt

then run gui.py, put in the product link, the price selector, target price and your email + password and press save. it saves everything in a .env file (you can also just copy example.env to .env and edit it by hand). check now button runs it once and shows you the result.

python gui.py

for gmail you need an app password not your normal one, you can make one by accessing https://myaccount.google.com/apppasswords, give it a name (e.g. price-hunter) and copy that into target price

run it with
python price_hunter.py

it only checks once when you run it, so to make it check every day I use windows task scheduler (cron if you're on mac/linux)

note: if it stops finding the price its probably because the website changed their layout, just put the new css selector in the gui. to find it right click the price in chrome > inspect and look at the class
