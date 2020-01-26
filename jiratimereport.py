import argparse
from datetime import datetime, timedelta
import json
from operator import attrgetter

import requests
from requests.auth import HTTPBasicAuth


class WorkLog:
    def __init__(self, issue_key, started, time_spent, author):
        self.issue_key = issue_key
        self.started = started
        self.time_spent = time_spent
        self.author = author


def get_request(args, url, params):
    auth = HTTPBasicAuth(args.user_name, args.api_token)

    headers = {
        "Accept": "application/json"
    }

    if args.ssl_certificate:

        response = requests.request(
            "GET",
            args.jira_url + url,
            headers=headers,
            params=params,
            auth=auth,
            verify=args.ssl_certificate
        )

    else:

        response = requests.request(
            "GET",
            args.jira_url + url,
            headers=headers,
            params=params,
            auth=auth
        )

    # print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    return response


def convert_to_date(args):
    if args.to_date:
        to_date = datetime.strptime(args.to_date, "%Y-%m-%d") + timedelta(days=1)
    else:
        to_date = datetime.now() + timedelta(days=1)
    return to_date


def get_updated_issues(args):
    issues_json = []
    start_at = 0

    while True:

        query = {
            'jql': 'project = "' + args.project + '" and timeSpent is not null and updated > "' + args.from_date + '"' +
                   ' and updated < "' + convert_to_date(args).strftime("%Y-%m-%d") + '"',
            'fields': 'id,key',
            'startAt': str(start_at)
        }

        response = get_request(args, "/rest/api/2/search", query)
        response_json = json.loads(response.text)
        issues_json.extend(response_json['issues'])

        total_number_of_issues = int(response_json['total'])
        max_results = int(response_json['maxResults'])
        max_number_of_issues_processed = start_at + max_results
        if max_number_of_issues_processed < total_number_of_issues:
            start_at = max_number_of_issues_processed
        else:
            break

    return issues_json


def get_work_logs(args, issues_json):
    work_logs = []
    from_date = datetime.strptime(args.from_date, "%Y-%m-%d")
    to_date = convert_to_date(args)

    for issue_json in issues_json:
        start_at = 0
        while True:
            params = {
                'startAt': str(start_at)
            }
            url = "/rest/api/2/issue/" + issue_json['key'] + "/worklog/"
            response = get_request(args, url, params)
            response_json = json.loads(response.text)
            work_logs_json = response_json['worklogs']
            for work_log_json in work_logs_json:
                started = work_log_json['started']
                started_date = datetime.strptime(started[0:10], "%Y-%m-%d")
                if from_date <= started_date < to_date:
                    author_json = work_log_json['updateAuthor']
                    work_logs.append(WorkLog(issue_json['key'],
                                             started_date,
                                             int(work_log_json['timeSpentSeconds']),
                                             author_json['displayName']))

            total_number_of_issues = int(response_json['total'])
            max_results = int(response_json['maxResults'])
            max_number_of_issues_processed = start_at + max_results
            if max_number_of_issues_processed < total_number_of_issues:
                start_at = max_number_of_issues_processed
            else:
                break

    return work_logs


def process_work_logs(work_logs):
    sorted_on_issue = sorted(work_logs, key=attrgetter('author', 'started', 'issue_key'))
    print("The Jira time report")
    print("====================")
    for work_log in sorted_on_issue:
        print(work_log.author + ";" + work_log.started.strftime('%Y-%m-%d') + ";" + work_log.issue_key + ";" +
              str(timedelta(seconds=work_log.time_spent)))


def main():
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
    parser.add_argument('--ssl_certificate',
                        help='The location of the SSL certificate, needed in case of self-signed certificates')
    args = parser.parse_args()

    issues_json = get_updated_issues(args)
    work_logs = get_work_logs(args, issues_json)
    process_work_logs(work_logs)


if __name__ == "__main__":
    main()
