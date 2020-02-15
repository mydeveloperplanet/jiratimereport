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


if __name__ == '__main__':
    unittest.main()
