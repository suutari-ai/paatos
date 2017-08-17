from .scanner import scan_dir


class ChangeScanResult(object):
    def __init__(self, changed, deleted, state):
        """
        Initialize result of a change scanning.

        :type changed: Iterable[DocumentInfo]
        :type deleted: Iterable[str]
        :type state: dict
        """
        self.changed = changed
        self.deleted = deleted
        self.state = state


def scan_for_changes(last_state=None, root='/files'):
    """
    Scan for changes on the server.

    Will create a list of changed and deleted files compared to given
    last state.  The list of changed files will include also all new
    files.  If no last state is given, will compare against empty state,
    i.e. all files are considered new.

    :type last_state: dict|None
    :param last_state: State from the last scan to compare against
    :rtype: ChangeScanResult
    :return: Changed and deleted files and updated state for next scan
    """
    if last_state is None:
        last_state = {}

    new_state = dict(last_state)
    doc_infos = scan_dir(root, max_depth=9999)
    changed = []
    deleted = set(last_state)
    for doc_info in doc_infos:
        deleted.discard(doc_info.path)
        if last_state.get(doc_info.path) != doc_info.mtime_text:
            new_state[doc_info.path] = doc_info.mtime_text
            changed.append(doc_info)

    for path in deleted:
        new_state.pop(path, None)

    return ChangeScanResult(changed, deleted, new_state)
