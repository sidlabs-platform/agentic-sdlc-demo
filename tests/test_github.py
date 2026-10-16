import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sdlc.github import APIError, GitHub, NoRedirect  # noqa: E402


class APITests(unittest.TestCase):
    def test_credential_cannot_be_redirected_to_another_host(self):
        with self.assertRaisesRegex(APIError, "Redirect refused"):
            NoRedirect().redirect_request(None, None, 302, "", {}, "https://external.invalid")
        api = GitHub("not-a-real-token")
        for path in ("https://external.invalid", "//external.invalid", "repos/owner/repo"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                api.request("GET", path)

    def test_paginated_graphql_associations(self):
        api = GitHub("not-a-real-token")
        cursors = []

        def request(method, path, data=None):
            cursor = data["variables"]["cursor"]
            cursors.append(cursor)
            connection = {"nodes": [{"number": 2 if cursor is None else 3}],
                          "pageInfo": {"hasNextPage": cursor is None, "endCursor": "next"}}
            return {"data": {"repository": {"issue": {"closedByPullRequestsReferences": connection}}}}

        api.request = request
        self.assertEqual(list(api.associated_prs("owner/repo", 1)), [2, 3])
        self.assertEqual(cursors, [None, "next"])

    def test_review_threads_exclude_resolved_outdated_and_other_heads(self):
        api = GitHub("not-a-real-token")
        threads = []
        for index, (resolved, outdated, sha) in enumerate(
                ((False, False, "head"), (True, False, "head"),
                 (False, True, "head"), (False, False, "old"))):
            threads.append({"isResolved": resolved, "isOutdated": outdated,
                            "comments": {"nodes": [{"databaseId": index,
                                                   "author": {"login": "Copilot"}, "commit": {"oid": sha}}]}})
        api.request = lambda *args: {"data": {"repository": {"pullRequest": {"reviewThreads": {
            "nodes": threads, "pageInfo": {"hasNextPage": False}}}}}}
        self.assertEqual([c["databaseId"] for c in api.review_comments("owner/repo", 1, "head")], [0])

    def test_graphql_errors_do_not_look_like_empty_results(self):
        api = GitHub("not-a-real-token")
        api.request = lambda *args: {"errors": [{"message": "Denied"}]}
        for run in (lambda: list(api.associated_prs("owner/repo", 1)),
                    lambda: api.closing_issues("owner/repo", 2),
                    lambda: api.review_comments("owner/repo", 2, "head")):
            with self.assertRaises(APIError):
                run()

    def test_closing_references_must_belong_to_repository(self):
        api = GitHub("not-a-real-token")
        references = {"nodes": [{"number": 1, "repository": {"nameWithOwner": "owner/repo"}},
                                {"number": 99, "repository": {"nameWithOwner": "external/repo"}}],
                      "pageInfo": {"hasNextPage": False}}
        api.request = lambda *args: {"data": {"repository": {"pullRequest": {
            "closingIssuesReferences": references}}}}
        self.assertEqual(api.closing_issues("owner/repo", 2), {1})
        references["pageInfo"]["hasNextPage"] = True
        with self.assertRaisesRegex(ValueError, "100 issues"):
            api.closing_issues("owner/repo", 2)


if __name__ == "__main__":
    unittest.main()
