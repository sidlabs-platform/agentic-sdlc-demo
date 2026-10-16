"""Small GitHub.com API adapter for controller operations and read-only advisory checks."""

import json
import urllib.error
import urllib.parse
import urllib.request


class APIError(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(f"GitHub API {status}: {message}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise APIError(code, "Redirect refused; update the repository identity")


class GitHub:
    def __init__(self, token):
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, method, path, data=None):
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("Expected a relative GitHub API path")
        request = urllib.request.Request(
            "https://api.github.com" + path,
            data=None if data is None else json.dumps(data).encode(),
            method=method,
            headers={"Authorization": f"Bearer {self.token}",
                     "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json",
                     "X-GitHub-Api-Version": "2022-11-28"},
        )
        try:
            with self.opener.open(request, timeout=45) as response:
                body = response.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as error:
            # Do not log requests, bodies, or arbitrary API responses containing user data.
            raise APIError(error.code, error.reason) from error
        except urllib.error.URLError as error:
            raise APIError(0, "Network failure; reconcile before retrying writes") from error

    def pages(self, path, field=None):
        separator = "&" if "?" in path else "?"
        page = 1
        while True:
            result = self.request("GET", f"{path}{separator}per_page=100&page={page}")
            items = result[field] if field else result
            if not isinstance(items, list):
                raise ValueError("Expected a paginated GitHub collection")
            yield from items
            if len(items) < 100:
                break
            page += 1

    def closing_issues(self, repo, number):
        owner, name = repo.split("/")
        result = self.request("POST", "/graphql", {
            "query": """query($owner:String!,$name:String!,$number:Int!){
              repository(owner:$owner,name:$name){
                pullRequest(number:$number){
                  closingIssuesReferences(first:100){
                    nodes{number repository{nameWithOwner}} pageInfo{hasNextPage}
                  }
                }
              }
            }""",
            "variables": {"owner": owner, "name": name, "number": number},
        })
        if result.get("errors"):
            raise APIError(200, "GraphQL closing-issue query failed")
        references = result["data"]["repository"]["pullRequest"]["closingIssuesReferences"]
        if references["pageInfo"]["hasNextPage"]:
            raise ValueError("PR closes more than 100 issues; split it before proceeding")
        return {x["number"] for x in references["nodes"] if x["repository"]["nameWithOwner"] == repo}

    def associated_prs(self, repo, issue):
        owner, name = repo.split("/")
        cursor = None
        while True:
            result = self.request("POST", "/graphql", {
                "query": """query($owner:String!,$name:String!,$issue:Int!,$cursor:String){
                  repository(owner:$owner,name:$name){
                    issue(number:$issue){
                      closedByPullRequestsReferences(first:100,after:$cursor,includeClosedPrs:true){
                        nodes{number} pageInfo{hasNextPage endCursor}
                      }
                    }
                  }
                }""",
                "variables": {"owner": owner, "name": name, "issue": issue, "cursor": cursor},
            })
            if result.get("errors"):
                raise APIError(200, "GraphQL issue-to-PR query failed")
            references = result["data"]["repository"]["issue"]["closedByPullRequestsReferences"]
            yield from (node["number"] for node in references["nodes"])
            if not references["pageInfo"]["hasNextPage"]:
                return
            cursor = references["pageInfo"]["endCursor"]

    def review_comments(self, repo, number, sha):
        """Only unresolved, non-outdated inline feedback on this head is actionable."""
        owner, name = repo.split("/")
        cursor = None
        comments = []
        while True:
            result = self.request("POST", "/graphql", {
                "query": """query($owner:String!,$name:String!,$number:Int!,$cursor:String){
                  repository(owner:$owner,name:$name){
                    pullRequest(number:$number){
                      reviewThreads(first:100,after:$cursor){
                        nodes{isResolved isOutdated comments(first:1){
                          nodes{databaseId author{login} commit{oid}}
                        }}
                        pageInfo{hasNextPage endCursor}
                      }
                    }
                  }
                }""",
                "variables": {"owner": owner, "name": name, "number": number, "cursor": cursor},
            })
            if result.get("errors"):
                raise APIError(200, "GraphQL review-thread query failed")
            threads = result["data"]["repository"]["pullRequest"]["reviewThreads"]
            for thread in threads["nodes"]:
                for comment in thread["comments"]["nodes"]:
                    if (not thread["isResolved"] and not thread["isOutdated"]
                            and comment.get("commit") and comment["commit"]["oid"] == sha
                            and comment.get("author")):
                        comments.append(comment)
            if not threads["pageInfo"]["hasNextPage"]:
                return comments
            cursor = threads["pageInfo"]["endCursor"]
