"""GitHub integration helpers for PR comments and SARIF upload."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GitHubIntegration:
    """
    GitHub integration for posting PR comments and uploading SARIF.

    This is a separate Dagger function that can be called after scanning
    to integrate results with GitHub's UI.

    These functions require GitHub credentials passed as secrets.
    """

    @function
    async def post_pr_comment(
        self,
        token: Annotated[dagger.Secret, Doc("GitHub token with PR write access")],
        repository: Annotated[str, Doc("Repository in owner/repo format")],
        pr_number: Annotated[int, Doc("Pull request number")],
        report: Annotated[dagger.File, Doc("Markdown report file to post")],
        api_url: Annotated[str, Doc("GitHub API URL (for GHE)")] = "https://api.github.com",
    ) -> str:
        """
        Post or update a PR comment with scan results.

        Uses a marker comment to update existing comments instead of creating duplicates.

        Example:
            dagger call github post-pr-comment \
                --token env:GITHUB_TOKEN \
                --repository owner/repo \
                --pr-number 123 \
                --report ./hardening-report.md
        """
        report_content = await report.contents()

        # Add marker for finding/updating comment
        comment_body = f"""## Security Hardening Results

<!-- hardening-scan-comment-marker -->

{report_content}
"""

        script = f'''
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_URL = "{api_url}"
REPO = "{repository}"
PR_NUMBER = {pr_number}
MARKER = "hardening-scan-comment-marker"

token = os.environ.get("GITHUB_TOKEN", "")
if not token:
    print("ERROR: GITHUB_TOKEN not set")
    sys.exit(1)

headers = {{
    "Authorization": f"Bearer {{token}}",
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",
}}

# Read comment body
comment_body = open("/comment.md").read()

# List existing comments
list_url = f"{{API_URL}}/repos/{{REPO}}/issues/{{PR_NUMBER}}/comments"
req = Request(list_url, headers=headers)

try:
    with urlopen(req) as resp:
        comments = json.loads(resp.read().decode())
except HTTPError as e:
    print(f"ERROR listing comments: {{e.code}} {{e.reason}}")
    sys.exit(1)

# Find existing hardening comment
existing_id = None
for comment in comments:
    if MARKER in comment.get("body", ""):
        existing_id = comment["id"]
        break

if existing_id:
    # Update existing comment
    update_url = f"{{API_URL}}/repos/{{REPO}}/issues/comments/{{existing_id}}"
    req = Request(
        update_url,
        data=json.dumps({{"body": comment_body}}).encode(),
        headers={{**headers, "Content-Type": "application/json"}},
        method="PATCH",
    )
    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            print(f"Updated comment: {{result.get('html_url')}}")
    except HTTPError as e:
        print(f"ERROR updating comment: {{e.code}} {{e.reason}}")
        sys.exit(1)
else:
    # Create new comment
    create_url = f"{{API_URL}}/repos/{{REPO}}/issues/{{PR_NUMBER}}/comments"
    req = Request(
        create_url,
        data=json.dumps({{"body": comment_body}}).encode(),
        headers={{**headers, "Content-Type": "application/json"}},
        method="POST",
    )
    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            print(f"Created comment: {{result.get('html_url')}}")
    except HTTPError as e:
        print(f"ERROR creating comment: {{e.code}} {{e.reason}}")
        sys.exit(1)

print("SUCCESS")
'''

        result = await (
            dag.container()
            .from_("python:3.12-slim")
            .with_secret_variable("GITHUB_TOKEN", token)
            .with_new_file("/comment.md", comment_body)
            .with_new_file("/post_comment.py", script)
            .with_exec(["python", "/post_comment.py"])
            .stdout()
        )

        return result

    @function
    async def upload_sarif(
        self,
        token: Annotated[dagger.Secret, Doc("GitHub token with security-events write access")],
        repository: Annotated[str, Doc("Repository in owner/repo format")],
        sarif_file: Annotated[dagger.File, Doc("SARIF file to upload")],
        ref: Annotated[str, Doc("Git ref (branch or SHA)")],
        commit_sha: Annotated[str, Doc("Full commit SHA")],
        api_url: Annotated[str, Doc("GitHub API URL (for GHE)")] = "https://api.github.com",
    ) -> str:
        """
        Upload SARIF results to GitHub Code Scanning.

        Requires repository to have GitHub Advanced Security / Code Scanning enabled.

        Example:
            dagger call github upload-sarif \
                --token env:GITHUB_TOKEN \
                --repository owner/repo \
                --sarif-file ./hardening-report.sarif \
                --ref refs/heads/main \
                --commit-sha abc123...
        """
        script = f'''
import base64
import gzip
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_URL = "{api_url}"
REPO = "{repository}"
REF = "{ref}"
COMMIT_SHA = "{commit_sha}"

token = os.environ.get("GITHUB_TOKEN", "")
if not token:
    print("ERROR: GITHUB_TOKEN not set")
    sys.exit(1)

# Read and compress SARIF
with open("/sarif.sarif", "rb") as f:
    sarif_content = f.read()

compressed = gzip.compress(sarif_content)
encoded = base64.b64encode(compressed).decode()

# Upload to Code Scanning API
upload_url = f"{{API_URL}}/repos/{{REPO}}/code-scanning/sarifs"

payload = {{
    "commit_sha": COMMIT_SHA,
    "ref": REF,
    "sarif": encoded,
    "tool_name": "hardening-workflows",
}}

headers = {{
    "Authorization": f"Bearer {{token}}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
}}

req = Request(
    upload_url,
    data=json.dumps(payload).encode(),
    headers=headers,
    method="POST",
)

try:
    with urlopen(req) as resp:
        result = json.loads(resp.read().decode())
        sarif_id = result.get("id", "unknown")
        print(f"SARIF uploaded successfully. ID: {{sarif_id}}")
        print(f"Processing URL: {{result.get('url', 'N/A')}}")
except HTTPError as e:
    body = e.read().decode() if e.fp else ""
    print(f"ERROR uploading SARIF: {{e.code}} {{e.reason}}")
    print(f"Response: {{body}}")
    if e.code == 403:
        print("Note: Code Scanning may not be enabled for this repository")
    sys.exit(1)

print("SUCCESS")
'''

        sarif_content = await sarif_file.contents()

        result = await (
            dag.container()
            .from_("python:3.12-slim")
            .with_secret_variable("GITHUB_TOKEN", token)
            .with_new_file("/sarif.sarif", sarif_content)
            .with_new_file("/upload_sarif.py", script)
            .with_exec(["python", "/upload_sarif.py"])
            .stdout()
        )

        return result

    @function
    async def check_threshold(
        self,
        report_dir: Annotated[dagger.Directory, Doc("Directory containing scan reports")],
    ) -> bool:
        """
        Check if severity threshold was exceeded.

        Returns True if threshold was exceeded (for CI failure detection).
        Checks for presence of THRESHOLD_EXCEEDED file in report directory.
        """
        try:
            await report_dir.file("THRESHOLD_EXCEEDED").contents()
            return True
        except Exception:
            return False
