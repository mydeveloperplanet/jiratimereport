class Issue:
    """A Issue object will represent a Jira Issue containing limited fields
    """
    def __init__(self, issue_id, key, summary, parent_key, parent_summary):
        self.issue_id = issue_id
        self.key = key
        self.summary = summary
        self.parent_key = parent_key
        self.parent_summary = parent_summary

    def __eq__(self, other):
        try:
            return (self.issue_id, self.key, self.summary, self. parent_key, self.parent_summary) == \
                   (other.issue_id, other.key, other.summary, other.parent_key, other.parent_summary)
        except AttributeError:
            return NotImplemented
