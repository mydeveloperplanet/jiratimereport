class WorkLog:
    """A WorkLog object will represent a Jira WorkLog containing the registered time on an issue by an author
    """
    def __init__(self, issue_key, started, time_spent, author):
        self.issue_key = issue_key
        self.started = started
        self.time_spent = time_spent
        self.author = author