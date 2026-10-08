# Exercise 02.0: status codes with curl

**Goal:** get only the status code of a page, with one curl command.

## Task

Write a curl command that prints only the status code (for example `200`) of a page. Run it for these 3 pages:

1. `http://example.com`
2. `http://google.com`
3. `https://example.com/nothing-here`

Which code does each one give? What does each code mean?

## What you need

Everything is in the README of this folder:
- `-s` and `-o /dev/null` (Steps 5 and 6): no progress bar, no body;
- `-w` and the variable `%{http_code}` (Step 8).

## Check

Three numbers, one per page: three different classes of status codes.

<details>
<summary>Solution</summary>

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://example.com
curl -s -o /dev/null -w '%{http_code}\n' http://google.com
curl -s -o /dev/null -w '%{http_code}\n' https://example.com/nothing-here
```
```
200
301
404
```
`200` OK (2xx success), `301` Moved Permanently (3xx redirect: curl does not follow it without `-L`), `404` Not Found (4xx client error: the page does not exist).
</details>
