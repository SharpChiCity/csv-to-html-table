import os
from datetime import datetime
import time

while True:

    os.system("c://users//monstar/python//stubhub//cubs//stubhub_make_min_pricing_file.py")

    commit_message = str(datetime.today())[0:10]

    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git checkout master')
    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git add "C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//data//github prices.csv"')
    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git commit -m "{}"'.format(commit_message))
    os.system("git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git push origin master")

    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git checkout gh-pages')
    os.system('git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git merge -m "{}"'.format(commit_message))
    os.system("git --git-dir=C://Users//Monstar//Python//Stubhub//cubs-bleacher-prices//.git push origin gh-pages")

    print('done')

    time.sleep(3600)