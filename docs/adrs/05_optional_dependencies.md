

# ADR 5: Splitting carbon-txt into optional dependency extras for smaller, focused installs

## Status

Accepted

## Context

The `carbon-txt` validator has grown to support three distinct use cases:

1. **Core library**: Parsing and validating `carbon.txt` files as a library or CLI tool
2. **CSRD processing**: Using Arelle to parse XBRL/CSRD sustainability reports linked from `carbon.txt`
3. **Web service**: Running a Django-based HTTP API for validation-as-a-service

Historically, all three were bundled into a single install target. This meant that a user who only wanted to validate `carbon.txt` syntax from the command line would still pull in Django (~30 MB), Granian (~16 MB), Arelle (~24 MB), NumPy (~21 MB), lxml (~20 MB), Pillow (~13 MB), and all their transitive dependencies. The total installed footprint exceeded **300 MB** even for the simplest use case.

This created friction for:
- CI pipelines that only need to validate files
- Embedded/library consumers who want a small dependency tree
- Deployment environments where disk space or security audit surface matters

## Decision

**Split the package into optional dependency extras using standard PEP 508 `[extras]` syntax, while keeping a single source tree and wheel.**

We define three install targets:

| Target | Command | What you get |
|--------|---------|-------------|
| **Core** | `uv pip install carbon-txt` | Parser, validator, CLI, AI model card processor |
| **CSRD** | `uv pip install "carbon-txt[csrd]"` | Core + Arelle + CSRD report processing |
| **Web** | `uv pip install "carbon-txt[web]"` | Core + Django + Granian + web API |
| **All** | `uv pip install "carbon-txt[all]"` | Convenience alias for `[csrd,web]` |

### Key design choices

1. **One wheel, runtime guards**: We publish a single `carbon-txt` wheel that contains all source files. Heavy imports (Django, Arelle) are deferred to runtime inside `try/except` blocks. This is the standard Python packaging convention — `pip install package[extra]` adds dependencies, it does not change wheel contents.

2. **CSRD is a peer plugin**: `GreenwebCSRDProcessor` is no longer eagerly exported from `carbon_txt.processors`. It must be imported explicitly from `carbon_txt.processors.csrd_document`, mirroring how external plugins would be consumed.

3. **CLI guards the `serve` command**: Running `carbon-txt serve` without `[web]` installed produces a clear error message directing the user to install the extra.

4. **Environment variable parsing without django-environ**: The core CLI no longer depends on `django-environ`. Plugin configuration is read directly from `os.environ`, removing a Django-affinity dependency from the core install.

5. **Dev dependencies migrated to `[dependency-groups]`**: The `[tool.uv] dev-dependencies` section was converted to the PEP 735 `[dependency-groups] dev` format, which is the modern standard and works cleanly with `uv sync`.

### Installed size comparison

| Variant | Total Size | Packages Installed |
|---------|-----------|-------------------|
| **Core only** | **22 MB** | 33 |
| **CSRD** | **107 MB** | ~52 |
| **Web** | **152 MB** | ~53 |
| **All** | **237 MB** | 72 |

#### Top 5 contributors by variant

| Rank | Core (22M) | CSRD (107M) | Web (152M) | All (237M) |
|------|-----------|-------------|------------|------------|
| 1 | `pygments` (4.9M) | `arelle` (24M) | `mypyc` .so (39M) | `mypyc` .so (39M) |
| 2 | `pydantic_core` (4.2M) | `numpy` (21M) | `django` (30M) | `django` (30M) |
| 3 | `pydantic` (1.9M) | `lxml` (20M) | `mypy` (17M) | `arelle` (24M) |
| 4 | `rich` (1.4M) | `Pillow` (13M) | `granian` (16M) | `numpy` (21M) |
| 5 | `dns` (1.3M) | `pygments` (4.9M) | `ninja` (9M) | `lxml` (20M) |

The default `carbon-txt` install is now **~90% smaller** than before (22 MB vs ~300 MB).

### Usage examples

#### Validate a carbon.txt file from the command line (core only)

```bash
uv pip install carbon-txt
carbon-txt validate file ./carbon.txt
```

Or programmatically:

```python
from carbon_txt.validators import CarbonTxtValidator

validator = CarbonTxtValidator()
result = validator.validate_url("https://example.com/carbon.txt")

if result.result:
    print("Valid!")
    print(result.result)
else:
    print("Invalid:", result.exceptions)
```

#### Process a CSRD report linked from a carbon.txt file

```bash
uv pip install "carbon-txt[csrd]"
```

```python
from carbon_txt.processors.csrd_document import GreenwebCSRDProcessor

processor = GreenwebCSRDProcessor(report_url="https://example.com/report.xhtml")
datapoints = processor.get_esrs_datapoint_values(processor.local_datapoint_codes)

for dp in datapoints:
    print(f"{dp.short_code}: {dp.value} {dp.unit}")
```

#### Run the validation web service

```bash
uv pip install "carbon-txt[web]"
carbon-txt serve --port 8000
```

Or with Granian in production:

```bash
carbon-txt serve --production --server granian
```

The Django settings module can be overridden:

```bash
carbon-txt serve --django-settings myproject.settings
```

## Consequences

### What becomes easier

- **Smaller CI pipelines**: Core validation runs in ~22 MB instead of 300+ MB
- **Faster installs**: Fewer compiled dependencies to fetch and link
- **Reduced security audit surface**: Production deployments don't include Django or Arelle unless needed
- **Clearer dependency intent**: `requirements.txt` or `pyproject.toml` dependencies communicate which features are used
- **Standard Python UX**: `pip install package[extra]` is familiar to Python users

### What becomes more difficult

- **Single wheel contains all files**: The wheel includes `web/` and `csrd_document.py` even for core installs. However, these are pure-Python source files (~40 KB combined) and do not affect runtime behaviour due to import guards. The real savings are in dependency exclusion.

- **One extra cannot see another's imports**: A project that installs `[csrd]` but not `[web]` cannot accidentally use Django features, and vice versa. This is usually desired, but could confuse users who expect all submodules to be importable after any install.

- **Testing matrix expansion**: We now need to verify behaviour across four install variants. A `scripts/verify_extras.py` script was added to support this.

### Future considerations

- The `[web]` extra previously included `django-stubs[compatible-mypy]`, which pulled in `mypy` (~17 MB) — a development tool, not a runtime dependency. Moving type stubs to `dev` dependencies reduced the web variant footprint.

- If installed size of source files themselves (not dependencies) becomes a genuine constraint, the next step would be to split into separate installable packages (e.g. `carbon-txt-core`, `carbon-txt-web`, `carbon-txt-csrd`) using uv workspaces or a monorepo structure. This is significantly more complex and not justified at current sizes.
