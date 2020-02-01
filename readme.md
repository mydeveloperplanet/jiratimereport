Jira Time Report Generator
==========================

The Jira Time Report Generator will provide an overview of the work spent on issues of a particular Jira project in a 
timespan period.

The script can be invoked by means of a bash script. Set the `PYTHONIOENCODING` env variable in case you are using non ASCII characters.
By default, the output will be sent to the console.

    export PYTHONIOENCODING=UTF-8  
    read -s -p "Enter Password: " mypassword
    python jiratimereport.py [jira_url] [user_name] $mypassword [project] [from date in format yyyy-mm-dd]

Optional arguments are
- `--to_date` The date to end the time report (the end date is inclusive), format yyyy-mm-dd
- `--output` The output format, can be one of the following:
  - `console` print the output to the console
  - `csv` print the output to a semi-colon separated file
  - `excel` print the output to an Excel file
- `--ssl_certificate` The location of the SSL certificate, needed in case of self-signed certificates