import unittest
import requests_mock
import jiratimereport


class MyTestCase(unittest.TestCase):
    def test_get_updated_issues_one_page(self):
        """
        Test the single page response when retrieving Jira issues
        """
        mock_response = '{"expand":"schema,names","startAt":0,"maxResults":50,"total":2,"issues":[{' \
                        '"expand":"operations,versionedRepresentations,editmeta,changelog,renderedFields",' \
                        '"id":"10005","self":"https://jira_url/rest/api/2/issue/10005", "key":"MYB-5"},' \
                        '{"expand":"operations,versionedRepresentations,editmeta,changelog,renderedFields",' \
                        '"id":"10004","self":"https://jira_url/rest/api/2/issue/10004","key":"MYB-4"}]} '
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
        Test the multiple pages response when retrieving Jira  (pagination)
        """
        mock_response_first_page = \
            '{"expand":"schema,names","startAt":0,"maxResults":2,"total":3,"issues":[{' \
            '"expand":"operations,versionedRepresentations,editmeta,changelog,renderedFields",' \
            '"id":"10005","self":"https://jira_url/rest/api/2/issue/10005", "key":"MYB-5"},' \
            '{"expand":"operations,versionedRepresentations,editmeta,changelog,renderedFields",' \
            '"id":"10004","self":"https://jira_url/rest/api/2/issue/10004","key":"MYB-4"}]} '
        mock_response_second_page = \
            '{"expand":"schema,names","startAt":2,"maxResults":2,"total":3,"issues":[{' \
            '"expand":"operations,versionedRepresentations,editmeta,changelog,renderedFields",' \
            '"id":"10006","self":"https://jira_url/rest/api/2/issue/10006", "key":"MYB-6"}]} '
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


if __name__ == '__main__':
    unittest.main()
