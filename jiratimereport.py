import argparse
import csv
from datetime import datetime, timedelta
import json
from operator import attrgetter

import requests
import xlsxwriter as xlsxwriter
from requests.auth import HTTPBasicAuth

from issue import Issue
from worklog import WorkLog

CSV_FILE_NAME = "jira-time-report.csv"
EXCEL_FILE_NAME = "jira-time-report.xlsx"


def get_request(jira_url, user_name, api_token, ssl_certificate, url, params):
    """Perform the GET request to the Jira server

    :param jira_url: The base Jira URL
    :param user_name The user name to use for connecting to Jira
    :param api_token The API token to use for connecting to Jira
    :param ssl_certificate The location of the SSL certificate, needed in case of self-signed certificates
    :param url: the complete Jira URL for invoking the request
    :param params: the parameters to be added to the Jira URL
    :return: the complete response as returned from the Jira API
    """
    auth = HTTPBasicAuth(user_name, api_token)

    headers = {
        "Accept": "application/json"
    }

    if ssl_certificate:

        response = requests.request(
            "GET",
            jira_url + url,
            headers=headers,
            params=params,
            auth=auth,
            verify=ssl_certificate
        )

    else:

        response = requests.request(
            "GET",
            jira_url + url,
            headers=headers,
            params=params,
            auth=auth
        )

    return response


def convert_to_date(to_date):
    """Convert the to_date argument

    The to_date argument is an up and including date. The easiest way to cope with this, is to strip of the time and
    to add one day to the given to_date. This will make it easier to use in queries.

    :param to_date The date to end the time report (the end date is inclusive), format yyyy-mm-dd
    :return: the to_date plus one day at time 00:00:00
    """
    if to_date:
        converted_to_date = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
    else:
        converted_to_date = datetime.now() + timedelta(days=1)
    return converted_to_date


def get_updated_issues(jira_url, user_name, api_token, project, from_date, to_date, ssl_certificate):
    """Retrieve the updated issues from Jira

    Only the updated issues containing time spent and between the given from and to date are retrieved.

    :param jira_url: The base Jira URL
    :param user_name The user name to use for connecting to Jira
    :param api_token The API token to use for connecting to Jira
    :param project The Jira project to retrieve the time report
    :param from_date The date to start the time report, format yyyy-mm-dd
    :param to_date The date to end the time report (the end date is inclusive), format yyyy-mm-dd
    :param ssl_certificate The location of the SSL certificate, needed in case of self-signed certificates
    :return: a list of issues
    """

    issues = []
    start_at = 0

    while True:

        query = {
            'jql': 'project = "' + project + '" and timeSpent is not null and worklogDate >= "' + from_date +
                   '"' + ' and worklogDate < "' + convert_to_date(to_date).strftime("%Y-%m-%d") + '"',
            'fields': 'id,key,summary,parent',
            'startAt': str(start_at)
        }

        response = get_request(jira_url, user_name, api_token, ssl_certificate, "/rest/api/2/search", query)
        response_json = json.loads(response.text)
        issues.extend(convert_json_to_issues(response_json))

        # Verify whether it is necessary to invoke the API request again because of pagination
        total_number_of_issues = int(response_json['total'])
        max_results = int(response_json['maxResults'])
        max_number_of_issues_processed = start_at + max_results
        if max_number_of_issues_processed < total_number_of_issues:
            start_at = max_number_of_issues_processed
        else:
            break

    return issues


def convert_json_to_issues(response_json):
    """
    Convert JSON issues into Issue objects
    :param response_json: the JSON text as received from Jira
    :return: a list of Issues
    """
    issues = []
    for issue_json in response_json['issues']:
        issues.append(Issue(int(issue_json['id']),
                            issue_json['key'],
                            issue_json['fields']['summary'],
                            issue_json['fields']['parent']['key'],
                            issue_json['fields']['parent']['fields']['summary']))

    return issues


def get_work_logs(jira_url, user_name, api_token, from_date, to_date, ssl_certificate, issues):
    """Retrieve the work logs from Jira

    All work logs from the list of issues are retrieved. Only the work logs which have been started between the from and
    to date are used, the other work logs are not taken into account.

    :param jira_url: The base Jira URL
    :param user_name The user name to use for connecting to Jira
    :param api_token The API token to use for connecting to Jira
    :param from_date The date to start the time report, format yyyy-mm-dd
    :param to_date The date to end the time report (the end date is inclusive), format yyyy-mm-dd
    :param ssl_certificate The location of the SSL certificate, needed in case of self-signed certificates
    :param issues: a list of issues
    :return: the list of work logs which has been requested
    """
    work_logs = []
    from_date = datetime.strptime(from_date, "%Y-%m-%d")
    to_date = convert_to_date(to_date)

    for issue in issues:
        start_at = 0
        while True:
            params = {
                'startAt': str(start_at)
            }

            url = "/rest/api/2/issue/" + issue.key + "/worklog/"
            response = get_request(jira_url, user_name, api_token, ssl_certificate, url, params)
            response_json = json.loads(response.text)
            work_logs_json = response_json['worklogs']

            for work_log_json in work_logs_json:
                started = work_log_json['started']
                started_date = datetime.strptime(started[0:10], "%Y-%m-%d")
                if from_date <= started_date < to_date:
                    author_json = work_log_json['updateAuthor']
                    work_logs.append(WorkLog(issue.key,
                                             started_date,
                                             int(work_log_json['timeSpentSeconds']),
                                             author_json['displayName']))

            # Verify whether it is necessary to invoke the API request again because of pagination
            total_number_of_issues = int(response_json['total'])
            max_results = int(response_json['maxResults'])
            max_number_of_issues_processed = start_at + max_results
            if max_number_of_issues_processed < total_number_of_issues:
                start_at = max_number_of_issues_processed
            else:
                break

    return work_logs


def output_to_console(work_logs):
    """Print the work logs to the console

    :param work_logs: the list of work logs which must be printed
    """
    print("\nThe Jira time report")
    print("====================")
    for work_log in work_logs:
        print(work_log.author + ";" + work_log.started.strftime('%Y-%m-%d') + ";" + work_log.issue_key + ";" +
              str(timedelta(seconds=work_log.time_spent)))


def output_to_csv(work_logs):
    """Print the work logs to a CSV file

    :param work_logs: the list of work logs which must be printed
    """
    with open(CSV_FILE_NAME, 'w', newline='') as csvfile:
        fieldnames = ['author', 'date', 'issue', 'time_spent']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect=csv.unix_dialect)

        writer.writeheader()

        for work_log in work_logs:
            writer.writerow({'author': work_log.author,
                             'date': work_log.started.strftime('%Y-%m-%d'),
                             'issue': work_log.issue_key,
                             'time_spent': str(timedelta(seconds=work_log.time_spent))})


def output_to_excel(work_logs):
    """Print the work logs to an Excel file

    :param work_logs: the list of work logs which must be printed
    """
    with xlsxwriter.Workbook(EXCEL_FILE_NAME) as workbook:
        worksheet = workbook.add_worksheet()
        row = 0

        for work_log in work_logs:
            worksheet.write(row, 0, work_log.author)
            worksheet.write(row, 1, work_log.started.strftime('%Y-%m-%d'))
            worksheet.write(row, 2, work_log.issue_key)
            worksheet.write(row, 3, str(timedelta(seconds=work_log.time_spent)))

            row += 1


def process_work_logs(output, work_logs):
    """Process the retrieved work logs from the Jira API

    The work logs are sorted and printed to the specified output format

    :param output: The output format
    :param work_logs: the list of work logs which must be printed
    """
    sorted_on_issue = sorted(work_logs, key=attrgetter('author', 'started', 'issue_key'))

    if output == "csv":
        output_to_csv(sorted_on_issue)
    elif output == "excel":
        output_to_excel(sorted_on_issue)
    else:
        output_to_console(sorted_on_issue)


def main():
    """The main entry point of the application

    The responsibilities are:
    - parse the arguments
    - retrieve the updated issues
    - retrieve the work logs of the updated issues
    - generate the output report
    """
    parser = argparse.ArgumentParser(description='Generate a Jira time report.')
    parser.add_argument('jira_url',
                        help='The Jira URL')
    parser.add_argument('user_name',
                        help='The user name to use for connecting to Jira')
    parser.add_argument('api_token',
                        help='The API token to use for connecting to Jira')
    parser.add_argument('project',
                        help='The Jira project to retrieve the time report')
    parser.add_argument('from_date',
                        help='The date to start the time report, format yyyy-mm-dd')
    parser.add_argument('--to_date',
                        help='The date to end the time report (the end date is inclusive), format yyyy-mm-dd')
    parser.add_argument('--output', choices={"console", "csv", "excel"}, default="console",
                        help='The output format')
    parser.add_argument('--ssl_certificate',
                        help='The location of the SSL certificate, needed in case of self-signed certificates')
    args = parser.parse_args()

    issues = get_updated_issues(args.jira_url, args.user_name, args.api_token, args.project, args.from_date,
                                args.to_date, args.ssl_certificate)
    work_logs = get_work_logs(args.jira_url, args.user_name, args.api_token, args.from_date, args.to_date,
                              args.ssl_certificate, issues)
    process_work_logs(args.output, work_logs)


if __name__ == "__main__":
    main()
