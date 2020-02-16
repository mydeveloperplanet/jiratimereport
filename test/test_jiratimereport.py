import unittest
import requests_mock
import jiratimereport
from worklog import WorkLog
from datetime import datetime


class MyTestCase(unittest.TestCase):
    def test_get_updated_issues_one_page(self):
        """
        Test the single page response when retrieving Jira issues
        """
        with open("issues_one_page.json", "r") as issues_file:
            mock_response = issues_file.read()

        expected_result = [
            {'expand': 'operations,versionedRepresentations,editmeta,changelog,renderedFields', 'id': '10005',
             'self': 'https://jira_url/rest/api/2/issue/10005', 'key': 'MYB-5'},
            {'expand': 'operations,versionedRepresentations,editmeta,changelog,renderedFields', 'id': '10004',
             'self': 'https://jira_url/rest/api/2/issue/10004', 'key': 'MYB-4'}]

        with requests_mock.Mocker() as m:
            m.register_uri('GET', '/rest/api/2/search', text=mock_response)
            response = jiratimereport.get_updated_issues("https://jira_url", "user_name", "api_token",  "MYB",
                                                         "2020-01-10", "2020-01-20", "")
        self.assertEqual(expected_result, response)

    def test_get_updated_issues_multiple_pages(self):
        """
        Test the multiple pages response when retrieving Jira issues (pagination)
        """
        with open("issues_multiple_first_page.json", "r") as issues_first_file:
            mock_response_first_page = issues_first_file.read()

        with open("issues_multiple_second_page.json", "r") as issues_second_file:
            mock_response_second_page = issues_second_file.read()

        expected_result = [
            {'expand': 'operations,versionedRepresentations,editmeta,changelog,renderedFields', 'id': '10005',
             'self': 'https://jira_url/rest/api/2/issue/10005', 'key': 'MYB-5'},
            {'expand': 'operations,versionedRepresentations,editmeta,changelog,renderedFields', 'id': '10004',
             'self': 'https://jira_url/rest/api/2/issue/10004', 'key': 'MYB-4'},
            {'expand': 'operations,versionedRepresentations,editmeta,changelog,renderedFields', 'id': '10006',
             'self': 'https://jira_url/rest/api/2/issue/10006', 'key': 'MYB-6'}]

        with requests_mock.Mocker() as m:
            m.register_uri('GET', '/rest/api/2/search', [{'text': mock_response_first_page},
                                                         {'text': mock_response_second_page}])
            response = jiratimereport.get_updated_issues("https://jira_url", "user_name", "api_token",  "MYB",
                                                         "2020-01-10", "2020-01-20", "")

        self.assertEqual(expected_result, response)

    def test_get_work_logs_one_page(self):
        """
        Test the single page response when retrieving Jira work logs
        """
        with open("work_logs_first_issue_one_page.json", "r") as first_issue_file:
            mock_response_first_issue = first_issue_file.read()

        with open("work_logs_second_issue_one_page.json", "r") as second_issue_file:
            mock_response_second_issue = second_issue_file.read()

        issues_json = [
            {'expand': 'operations,versionedRepresentations,editmeta,changelog,renderedFields', 'id': '10005',
             'self': 'https://jira_url/rest/api/2/issue/10005', 'key': 'MYB-5'},
            {'expand': 'operations,versionedRepresentations,editmeta,changelog,renderedFields', 'id': '10004',
             'self': 'https://jira_url/rest/api/2/issue/10004', 'key': 'MYB-4'}]

        with requests_mock.Mocker() as m:
            m.register_uri('GET', '/rest/api/2/issue/MYB-5/worklog/', text=mock_response_first_issue)
            m.register_uri('GET', '/rest/api/2/issue/MYB-4/worklog/', text=mock_response_second_issue)
            work_logs = jiratimereport.get_work_logs("https://jira_url", "user_name", "api_token",
                                                     "2020-01-10", "2020-01-20", "", issues_json)

        self.assertEqual(work_logs[0], WorkLog("MYB-5", datetime(2020, 1, 18), 3600, "John Doe"))
        self.assertEqual(work_logs[1], WorkLog("MYB-5", datetime(2020, 1, 18), 5400, "John Doe"))
        self.assertEqual(work_logs[2], WorkLog("MYB-4", datetime(2020, 1, 12), 3600, "John Doe"))

    def test_get_work_logs_multiple_pages(self):
        """
        Test the multiple pages response when retrieving Jira issues (pagination)
        """
        with open("work_logs_multiple_first_page.json", "r") as issues_first_file:
            mock_response_first_page = issues_first_file.read()

        with open("work_logs_multiple_second_page.json", "r") as issues_second_file:
            mock_response_second_page = issues_second_file.read()

        issues_json = [
            {'expand': 'operations,versionedRepresentations,editmeta,changelog,renderedFields', 'id': '10005',
             'self': 'https://jira_url/rest/api/2/issue/10005', 'key': 'MYB-5'}]

        with requests_mock.Mocker() as m:
            m.register_uri('GET', '/rest/api/2/issue/MYB-5/worklog/', [{'text': mock_response_first_page},
                                                                       {'text': mock_response_second_page}])
            work_logs = jiratimereport.get_work_logs("https://jira_url", "user_name", "api_token",
                                                     "2020-01-10", "2020-01-20", "", issues_json)

        self.assertEqual(work_logs[0], WorkLog("MYB-5", datetime(2020, 1, 18), 3600, "John Doe"))
        self.assertEqual(work_logs[1], WorkLog("MYB-5", datetime(2020, 1, 18), 5400, "John Doe"))
        self.assertEqual(work_logs[2], WorkLog("MYB-5", datetime(2020, 1, 12), 3600, "John Doe"))


if __name__ == '__main__':
    unittest.main()
