Jira Time Report Generator
==========================

Under construction

Can be invoked with bash script. Set the PYTHONIOENCODING env variable in case you are using non ASCII characters

export PYTHONIOENCODING=UTF-8

read -s -p "Enter Password: " mypassword

python jiratimereport.py [jira_url] [user_name] $mypassword [project] [from date in format yyyy-mm-dd]