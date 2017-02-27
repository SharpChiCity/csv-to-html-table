import os
from datetime import datetime
import time

while True:

    print(datetime.today())
    os.system("c://users//monstar/python//stubhub//bot//season_tickets//upload_bleacher_prices.py")

    commit_message = str(datetime.today())[0:10]

    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git checkout master')
    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git add "C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//data//github_prices.csv"')
    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git commit -m "{}"'.format(commit_message))
    os.system("git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git push origin master")

    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git checkout gh-pages')
    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git merge origin master -m "{}"'.format(commit_message))
    os.system("git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git push origin gh-pages")

    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git checkout master')
    
    print('done')

    time.sleep(3600)