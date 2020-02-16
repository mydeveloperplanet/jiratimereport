class WorkLog:
    """A WorkLog object will represent a Jira WorkLog containing the registered time on an issue by an author
    """
    def __init__(self, issue_key, started, time_spent, author):
        self.issue_key = issue_key
        self.started = started
        self.time_spent = time_spent
        self.author = author

    def __eq__(self, other):
        try:
            return (self.issue_key, self.started, self.time_spent, self.author) == \
                   (other.issue_key, other.started, other.time_spent, other.author)
        except AttributeError:
            return NotImplemented
