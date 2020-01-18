# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import argparse
from datetime import datetime
import json

import requests
from requests.auth import HTTPBasicAuth


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

    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    return response


def get_updated_issues(args):
    query = {
        'jql': 'project = "' + args.project + '" and timeSpent is not null and updated > "' + args.from_date + '"',
        'fields': 'id,key'
    }

    response = get_request(args, "/rest/api/2/search", query)
    response_json = json.loads(response.text)
    issues_json = response_json['issues']
    for x in issues_json:
        print(x)

    return issues_json


def get_work_log(args, issues_json):

    total_time = 0
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
                time_spent_seconds = work_log_json['timeSpentSeconds']
                total_time += int(time_spent_seconds)

    print("the total work time is:" + str(total_time))


def main():
    parser = argparse.ArgumentParser(description='Generate a Jira time report.')
    parser.add_argument('--jira_url',
                        help='The Jira URL')
    parser.add_argument('--user_name',
                        help='The user name to use for connecting to Jira')
    parser.add_argument('--api_token',
                        help='The API token to use for connecting to Jira')
    parser.add_argument('--project',
                        help='The Jira project to retrieve the time report')
    parser.add_argument('--from_date',
                        help='The date to start the time report')
    args = parser.parse_args()

    issues_json = get_updated_issues(args)
    get_work_log(args, issues_json)


if __name__ == "__main__":
    main()

# Design
# retrieve updated issues in a timespan period
# for every issue, retrieve the worklogs
# if the worklog is inside the timespan, add the worklog to a list
# is it possible to sort the list on user and timestamps?
# Print a report
