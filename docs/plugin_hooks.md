## Plugin Hooks

The Carbon.txt validator exposes a set of "hooks" for extending functionality via a plugin interface.

These hooks are listed below:

### `process_document`

Called once for each `Disclosure` document linked in a successfully parsed carbon.txt file.

Accepts three arguments - the document itself `document`, the parsed carbon.txt file the document came from `parsed_carbon_txt_file`, and a list of logging statements `logs`, to append log messages to if you want these to show up in the output of API requests and command line invocations.

Let's say you want to see if a document links to a file that is still reachable.

```python
from carbon_txt.plugins import hookimpl
from httpx

@hookimpl

def process_document(document, parsed_carbon_txt_file, logs):

    response = httpx.head(document.url, follow_redirects=True)
    logs.append(f"Tried reaching file at {url}. HTTP status code was {response.status_code}")

    return {
        "title": document.title
        "url": document.url
        "response": response
        "logs": logs
        }

```
