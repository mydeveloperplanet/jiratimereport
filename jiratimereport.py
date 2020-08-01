import argparse
import csv
import json
from datetime import datetime, timedelta
from operator import attrgetter

import requests
import xlsxwriter as xlsxwriter
from requests.auth import HTTPBasicAuth

from issue import Issue
from worklog import WorkLog

CSV_FILE_NAME = "jira-time-report.csv"
EXCEL_FILE_NAME = "jira-time-report.xlsx"
FIELD_NAMES = ['author', 'date', 'issue', 'time_spent', 'original_estimate', 'total_time_spent', 'issue_start_date', 'issue_end_date', 'summary', 'parent', 'parent summary']


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
            'fields': 'id,key,summary,parent,timeoriginalestimate,timespent,resolutiondate',
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
        resolution_date = issue_json['fields']['resolutiondate']
        issues.append(Issue(int(issue_json['id']),
                            issue_json['key'],
                            issue_json['fields']['summary'],
                            issue_json['fields']['parent']['key'] if 'parent' in issue_json['fields'] else None,
                            issue_json['fields']['parent']['fields']['summary'] if 'parent' in issue_json['fields'] else None,
                            issue_json['fields']['timeoriginalestimate'],
                            issue_json['fields']['timespent'],
                            datetime.strptime(resolution_date[0:10], "%Y-%m-%d") if resolution_date is not None else None))

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
    :return: the list of work logs which has been requested and the updated list of issues
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
                if issue.issue_start_date is None:
                    issue.issue_start_date = started_date
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

    return work_logs, issues


def format_optional_time_field(field, empty_field):
    """
    Formats the given time field
    :param field: the time field in seconds
    :param empty_field: the return value when the time field is empty
    :return: The formatted time field as a datetime
    """
    if field is None:
        return empty_field
    else:
        hour = field // 3600
        field %= 3600
        minutes = field // 60
        field %= 60

        return "%d:%02d:%02d" % (hour, minutes, field)


def format_optional_date_field(field, empty_field):
    """
    Formats the given date field
    :param field: the date field in seconds
    :param empty_field: the return value when the date field is empty
    :return: The formatted date field as a datetime
    """
    return field.strftime('%Y-%m-%d') if field is not None else empty_field


def output_to_console(issues, work_logs):
    """Print the work logs to the console

    :param issues: the list of issues which must be printed
    :param work_logs: the list of work logs which must be printed
    """
    print("\nThe Jira time report")
    print("====================")
    for work_log in work_logs:
        work_log_issue = next((issue for issue in issues if issue.key == work_log.issue_key), None)
        print(work_log.author + ";" +
              work_log.started.strftime('%Y-%m-%d') + ";" +
              work_log.issue_key + ";" +
              str(timedelta(seconds=work_log.time_spent)) + ";" +
              format_optional_time_field(work_log_issue.original_estimate, "") + ";" +
              format_optional_time_field(work_log_issue.time_spent, "") + ";" +
              format_optional_date_field(work_log_issue.issue_start_date, "") + ";" +
              format_optional_date_field(work_log_issue.issue_end_date, "") + ";" +
              work_log_issue.summary + ";" +
              (str(work_log_issue.parent_key) if work_log_issue.parent_key is not None else "") + ";" +
              (str(work_log_issue.parent_summary) if work_log_issue.parent_summary is not None else ""))


def output_to_csv(issues, work_logs):
    """Print the work logs to a CSV file

    :param issues: the list of issues which must be printed
    :param work_logs: the list of work logs which must be printed
    """
    with open(CSV_FILE_NAME, 'w', newline='') as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES, dialect=csv.unix_dialect)

        writer.writeheader()

        for work_log in work_logs:
            work_log_issue = next((issue for issue in issues if issue.key == work_log.issue_key), None)
            writer.writerow({'author': work_log.author,
                             'date': work_log.started.strftime('%Y-%m-%d'),
                             'issue': work_log.issue_key,
                             'time_spent': work_log.time_spent,
                             'original_estimate': work_log_issue.original_estimate,
                             'total_time_spent': work_log_issue.time_spent,
                             'issue_start_date': format_optional_date_field(work_log_issue.issue_start_date, None),
                             'issue_end_date': format_optional_date_field(work_log_issue.issue_end_date, None),
                             'summary': work_log_issue.summary,
                             'parent': work_log_issue.parent_key,
                             'parent summary': work_log_issue.parent_summary})


def write_excel_header(worksheet):
    """
    Writes a column header to the Excel file
    :param worksheet: The worksheet to write the header to
    """
    cell_number = 0
    for field_name in FIELD_NAMES:
        worksheet.write(0, cell_number, field_name)
        cell_number += 1


def output_to_excel(issues, work_logs):
    """Print the work logs to an Excel file

    :param issues: the list of issues which must be printed
    :param work_logs: the list of work logs which must be printed
    """
    with xlsxwriter.Workbook(EXCEL_FILE_NAME) as workbook:
        worksheet = workbook.add_worksheet()
        write_excel_header(worksheet)

        row = 1
        time_format = workbook.add_format({'num_format': '[h]:mm:ss;@'})

        for work_log in work_logs:
            work_log_issue = next((issue for issue in issues if issue.key == work_log.issue_key), None)
            worksheet.write(row, 0, work_log.author)
            worksheet.write(row, 1, work_log.started.strftime('%Y-%m-%d'))
            worksheet.write(row, 2, work_log.issue_key)
            worksheet.write(row, 3, (work_log.time_spent / 86400) if work_log.time_spent else None, time_format)
            worksheet.write(row, 4, (work_log_issue.original_estimate / 86400) if work_log_issue.original_estimate else None, time_format)
            worksheet.write(row, 5, (work_log_issue.time_spent / 86400) if work_log_issue.time_spent else None, time_format)
            worksheet.write(row, 6, format_optional_date_field(work_log_issue.issue_start_date, None))
            worksheet.write(row, 7, format_optional_date_field(work_log_issue.issue_end_date, None))
            worksheet.write(row, 8, work_log_issue.summary)
            worksheet.write(row, 9, work_log_issue.parent_key)
            worksheet.write(row, 10, work_log_issue.parent_summary)

            row += 1


def process_work_logs(output, issues, work_logs):
    """Process the retrieved work logs from the Jira API

    The work logs are sorted and printed to the specified output format

    :param output: The output format
    :param issues: the list of issues which must be printed
    :param work_logs: the list of work logs which must be printed
    """
    sorted_on_issue = sorted(work_logs, key=attrgetter('author', 'started', 'issue_key'))

    if output == "csv":
        output_to_csv(issues, sorted_on_issue)
    elif output == "excel":
        output_to_excel(issues, sorted_on_issue)
    else:
        output_to_console(issues, sorted_on_issue)


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
    work_logs, issues = get_work_logs(args.jira_url, args.user_name, args.api_token, args.from_date, args.to_date,
                                      args.ssl_certificate, issues)
    process_work_logs(args.output, issues, work_logs)


if __name__ == "__main__":
    main()
