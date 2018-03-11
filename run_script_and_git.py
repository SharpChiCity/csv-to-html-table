import os
from datetime import datetime
import time

while True:

    print(datetime.today())
    os.system('echo -----------{}'.format(datetime.today()))
    os.system("sudo python3 /home/ec2-user/sh_scraper/season_tickets/upload_bleacher_prices.py")

    commit_message = str(datetime.today())[0:10]

    os.system('sudo git --git-dir=/home/ec2-user/cubs-bleacher-prices/.git checkout master')
    os.system('sudo git --git-dir=/home/ec2-user/cubs-bleacher-prices/.git add "/home/ec2-user/cubs-bleacher-prices/data/github_prices.csv"')
    os.system('sudo git --git-dir=/home/ec2-user/cubs-bleacher-prices/.git commit -m "{}"'.format(commit_message))
    os.system("sudo git --git-dir=/home/ec2-user/cubs-bleacher-prices/.git push origin master")

    os.system('sudo git --git-dir=/home/ec2-user/cubs-bleacher-prices/.git checkout gh-pages')
    os.system('sudo git --git-dir=/home/ec2-user/cubs-bleacher-prices/.git merge origin master -m "{}"'.format(commit_message))
    os.system("sudo git --git-dir=/home/ec2-user/cubs-bleacher-prices/.git push origin gh-pages")

    os.system('sudo git --git-dir=/home/ec2-user/cubs-bleacher-prices/.git checkout master')
    
    print('done')
    os.system('echo ----------- sleeping')
    time.sleep(3600)
