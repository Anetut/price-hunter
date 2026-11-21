# price-hunter

Simple python app that watches product pages and sends you an email when the price drops.

How it works: it downloads the page with requests, finds the price with beautifulsoup, and if its lower than the last time it checked it sends an email with smtplib (gmail). thats it


## ONLY WORKS WITH SITES THAT SEND PLAIN HTML

**If the price is loaded with javascript or the site has a bot check (like cloudflare "Just a moment...") it WONT work.** To check: open the product page, press ctrl+u and search for the price. If the price is not there, this script can't see it either.

to use it:

python -m pip install -r requirements.txt
then open the app: python gui.py

first put your gmail, app password and where to send the alerts and press save email settings (it saves them in a .env file, you can also copy example.env to .env and edit it by hand).

for gmail you need an app password not your normal one, you can make one by accessing https://myaccount.google.com/apppasswords, give it a name (e.g. price-hunter) and copy that into app password

Alerts are saved in alerts.json.
Check all now checks everything right away and shows you the result.
Check when pc starts: press turn on and your alerts get checked every time you start the pc. It puts a small file in the windows startup folder that runs price_hunter.py once (no window), checks everything, sends the email and closes. Turn off removes the file. Everything goes in log.txt so look there to see what happened.

Note: if it stops finding the price its probably because the website changed their layout, just put the new css selector in the alert. To find it right click the price in chrome > inspect and look at the class

Price history: every time it checks it saves the price in history.json, but only if its different from last time. You get one email with all the products that got cheaper since the last check, like: name: link - price from 3799.99 to 3599.99. The first check just saves the price (nothing to compare yet), and if the price goes up or stays the same you dont get an email (so it doesnt spam you every time you start the pc)
