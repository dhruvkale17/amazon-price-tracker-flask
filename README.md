# amazon-price-tracker-flask
Web Scraping application that tracks the price of product in the entered url and sends email to the user when price falls below the expected price.

Python framework- Flask
Database - SqLite, SQLAlchemy used to provide ORM feature to interact with database.

For web scraping - BeautifulSoup 
For sending email - smtplib

Multithreading used to keep checking prices of products in the background.
