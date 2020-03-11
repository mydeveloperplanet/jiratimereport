Jira Time Report Generator
==========================

The Jira Time Report Generator will provide an overview of the work spent on issues of a particular Jira project in a 
timespan period.

The script can be invoked by means of a bash script. Set the `PYTHONIOENCODING` env variable in case you are using non ASCII characters.
By default, the output will be sent to the console.

    export PYTHONIOENCODING=UTF-8  
    read -s -p "Enter Password: " mypassword
    python jiratimereport.py jira_url user_name $mypassword project from_date

Usage of the script:

    usage: jiratimereport.py [-h] [--to_date TO_DATE]
                             [--output {excel,csv,console}]
                             [--ssl_certificate SSL_CERTIFICATE]
                             jira_url user_name api_token project from_date
    
    Generate a Jira time report.
    
    positional arguments:
      jira_url              The Jira URL
      user_name             The user name to use for connecting to Jira
      api_token             The API token to use for connecting to Jira
      project               The Jira project to retrieve the time report
      from_date             The date to start the time report, format yyyy-mm-dd
    
    optional arguments:
      -h, --help            show this help message and exit
      --to_date TO_DATE     The date to end the time report (the end date is
                            inclusive), format yyyy-mm-dd
      --output {excel,csv,console}
                            The output format
      --ssl_certificate SSL_CERTIFICATE
                            The location of the SSL certificate, needed in case of
                            self-signed certificates
                            
See also the corresponding blog posts: 

https://mydeveloperplanet.com/2020/02/12/how-to-use-the-jira-api/

https://mydeveloperplanet.com/2020/03/11/how-to-mock-a-rest-api-in-python/
