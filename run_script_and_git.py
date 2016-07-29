import os
from datetime import datetime

execfile("c://users//monstar/python//stubhub//cubs//stubhub_make_min_pricing_file.py")

commit_message = str(datetime.today())[0:10]

os.system("git add .")
os.system('git commit -m "{}"'.format(commit_message))
os.system("git push origin master")

os.system('git checkout gh-pages')
os.system('git merge -m "{}"'.format(commit_message))
os.system("git push origin gh-pages")
