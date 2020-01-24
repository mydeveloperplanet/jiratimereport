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

    response = requests.request(
        "GET",
        args.jira_url + url,
        headers=headers,
        params=params,
        auth=auth
    )

    # print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    return response


def get_updated_issues(args):
    query = {
        'jql': 'project = "' + args.project + '" and timeSpent is not null and updated > "' + args.from_date + '"',
        'fields': 'id,key'
    }

    # TODO: check whether there are more results and recall the request

    response = get_request(args, "/rest/api/2/search", query)
    response_json = json.loads(response.text)
    issues_json = response_json['issues']

    return issues_json


def get_work_logs(args, issues_json):
    work_logs = []
    from_date = datetime.strptime(args.from_date, "%Y-%m-%d")

    for issue_json in issues_json:
        url = "/rest/api/2/issue/" + issue_json['key'] + "/worklog/"
        response = get_request(args, url, '')
        response_json = json.loads(response.text)
        work_logs_json = response_json['worklogs']
        for work_log_json in work_logs_json:
            started = work_log_json['started']
            started_date = datetime.strptime(started[0:10], "%Y-%m-%d")
            if started_date >= from_date:
                author_json = work_log_json['updateAuthor']
                work_logs.append(WorkLog(issue_json['key'],
                                         started_date,
                                         int(work_log_json['timeSpentSeconds']),
                                         author_json['displayName']))

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
                        help='The date to start the time report')
    args = parser.parse_args()

    issues_json = get_updated_issues(args)
    work_logs = get_work_logs(args, issues_json)
    process_work_logs(work_logs)


if __name__ == "__main__":
    main()
