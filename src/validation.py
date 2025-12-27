class TaskYamlError(Exception):
    def __init__(self, details: dict):
        self.details = details
        super().__init__("TASK_YAML_INVALID")


def _err(path: str, kind: str, expected=None, actual=None):
    err = {
        "path": path,
        "kind": kind,
    }
    if expected is not None:
        err["expected"] = expected
    if actual is not None:
        err["actual"] = actual

    raise TaskYamlError({"errors": [err]})


def validate_task_yaml_v1(cfg: dict) -> dict:
    # ---------- Phase 0: basic ----------
    if not isinstance(cfg, dict):
        _err("$", "type", "dict", type(cfg).__name__)

    # ---------- Phase 1: root ----------
    allowed_root = {"version", "task", "time", "sources", "filters", "output"}
    for k in cfg.keys():
        if k not in allowed_root:
            _err(k, "unknown_field")

    for k in ("version", "task", "time", "sources", "output"):
        if k not in cfg:
            _err(k, "missing_field")

    # ---------- Phase 2: version ----------
    if not isinstance(cfg["version"], int) or cfg["version"] != 1:
        _err("version", "version_not_supported", 1, cfg.get("version"))

    # ---------- Phase 3: task ----------
    task = cfg["task"]
    if not isinstance(task, dict):
        _err("task", "type", "dict", type(task).__name__)

    for k in task.keys():
        if k not in {"name", "description"}:
            _err(f"task.{k}", "unknown_field")

    name = task.get("name")
    if not isinstance(name, str) or not name.strip():
        _err("task.name", "empty")

    description = ""
    if "description" in task:
        if not isinstance(task["description"], str):
            _err(
                "task.description",
                "type",
                "str",
                type(task["description"]).__name__,
            )
        description = task["description"].strip()

    # ---------- Phase 4: time ----------
    time = cfg["time"]
    if not isinstance(time, dict):
        _err("time", "type", "dict", type(time).__name__)

    for k in time.keys():
        if k not in {"lookback_hours"}:
            _err(f"time.{k}", "unknown_field")

    lookback_hours = time.get("lookback_hours")
    if not isinstance(lookback_hours, int) or not (1 <= lookback_hours <= 8760):
        _err(
            "time.lookback_hours",
            "range",
            "1..8760",
            lookback_hours,
        )

    # ---------- Phase 5: sources ----------
    sources = cfg["sources"]
    if not isinstance(sources, dict):
        _err("sources", "type", "dict", type(sources).__name__)

    for k in sources.keys():
        if k not in {"telegram", "web", "api"}:
            _err(f"sources.{k}", "unknown_field")

    # require at least one source
    if not any(k in sources for k in ("telegram", "web", "api")):
        _err("sources", "missing_field")

    normalized_channels = []
    limit_per_channel = None
    normalized_web_sites = []
    normalized_api = None

    # ---------- telegram ----------
    if "telegram" in sources:
        telegram = sources["telegram"]
        if not isinstance(telegram, dict):
            _err("sources.telegram", "type", "dict", type(telegram).__name__)

        for k in telegram.keys():
            if k not in {"channels", "limit_per_channel"}:
                _err(f"sources.telegram.{k}", "unknown_field")

        channels = telegram.get("channels")
        if not isinstance(channels, list) or not channels:
            _err("sources.telegram.channels", "empty")

        for i, ch in enumerate(channels):
            if not isinstance(ch, str):
                _err(f"sources.telegram.channels[{i}]", "type", "str", type(ch).__name__)
            c = ch.lstrip("@").strip()
            if not c:
                _err(f"sources.telegram.channels[{i}]", "empty")
            normalized_channels.append(c)

        if len(set(normalized_channels)) != len(normalized_channels):
            _err("sources.telegram.channels", "duplicate")

        limit_per_channel = telegram.get("limit_per_channel")
        if not isinstance(limit_per_channel, int) or not (1 <= limit_per_channel <= 5000):
            _err(
                "sources.telegram.limit_per_channel",
                "range",
                "1..5000",
                limit_per_channel,
            )

    # ---------- web ----------
    if "web" in sources:
        web = sources["web"]
        if not isinstance(web, dict):
            _err("sources.web", "type", "dict", type(web).__name__)

        for k in web.keys():
            if k not in {"sites"}:
                _err(f"sources.web.{k}", "unknown_field")

        sites = web.get("sites")
        if not isinstance(sites, list) or not sites:
            _err("sources.web.sites", "empty")

        seen = set()
        for i, s in enumerate(sites):
            if not isinstance(s, dict):
                _err(f"sources.web.sites[{i}]", "type", "dict", type(s).__name__)

            for k in s.keys():
                if k not in {"site", "feed_url"}:
                    _err(f"sources.web.sites[{i}].{k}", "unknown_field")

            site = s.get("site")
            if not isinstance(site, str) or not site.strip():
                _err(f"sources.web.sites[{i}].site", "empty")

            feed_url = s.get("feed_url")
            if not isinstance(feed_url, str) or not feed_url.strip():
                _err(f"sources.web.sites[{i}].feed_url", "empty")

            key = (site.strip(), feed_url.strip())
            if key in seen:
                _err("sources.web.sites", "duplicate")
            seen.add(key)

            normalized_web_sites.append(
                {"site": site.strip(), "feed_url": feed_url.strip()}
            )

    # ---------- api ----------
    if "api" in sources:
        api = sources["api"]
        if not isinstance(api, dict):
            _err("sources.api", "type", "dict", type(api).__name__)

        for k in api.keys():
            if k not in {"server", "item_ids", "locations", "qualities"}:
                _err(f"sources.api.{k}", "unknown_field")

        server = api.get("server", "west")
        if not isinstance(server, str) or not server.strip():
            _err("sources.api.server", "empty")

        def _list_of_str(path, v):
            if not isinstance(v, list) or not v:
                _err(path, "empty")
            out = []
            for i, x in enumerate(v):
                if not isinstance(x, str) or not x.strip():
                    _err(f"{path}[{i}]", "empty")
                out.append(x.strip())
            if len(set(out)) != len(out):
                _err(path, "duplicate")
            return out

        def _list_of_int(path, v):
            if not isinstance(v, list) or not v:
                _err(path, "empty")
            out = []
            for i, x in enumerate(v):
                if not isinstance(x, int) or not (1 <= x <= 5):
                    _err(f"{path}[{i}]", "range", "1..5", x)
                out.append(x)
            if len(set(out)) != len(out):
                _err(path, "duplicate")
            return out

        normalized_api = {
            "server": server.strip(),
            "item_ids": _list_of_str("sources.api.item_ids", api.get("item_ids")),
            "locations": _list_of_str("sources.api.locations", api.get("locations")),
            "qualities": _list_of_int("sources.api.qualities", api.get("qualities")),
        }

    # ---------- Phase 6: filters ----------
    filters = cfg.get("filters", {})
    if not isinstance(filters, dict):
        _err("filters", "type", "dict", type(filters).__name__)

    for k in filters.keys():
        if k not in {"include_keywords", "exclude_keywords"}:
            _err(f"filters.{k}", "unknown_field")

    def _parse_keywords(path: str, value):
        if not isinstance(value, list):
            _err(path, "type", "list", type(value).__name__)
        out = []
        for i, v in enumerate(value):
            if not isinstance(v, str):
                _err(f"{path}[{i}]", "type", "str", type(v).__name__)
            s = v.strip()
            if not s:
                _err(f"{path}[{i}]", "empty")
            out.append(s)
        if len(set(out)) != len(out):
            _err(path, "duplicate")
        return out

    include_keywords = _parse_keywords(
        "filters.include_keywords",
        filters.get("include_keywords", []),
    )
    if not include_keywords:
        _err("filters.include_keywords", "missing_include_keywords")

    exclude_keywords = []
    if "exclude_keywords" in filters:
        exclude_keywords = _parse_keywords(
            "filters.exclude_keywords",
            filters.get("exclude_keywords", []),
        )

    # ---------- Phase 7: output ----------
    output = cfg["output"]
    if not isinstance(output, dict):
        _err("output", "type", "dict", type(output).__name__)

    for k in output.keys():
        if k not in {"max_items"}:
            _err(f"output.{k}", "unknown_field")

    max_items = output.get("max_items")
    if not isinstance(max_items, int) or not (1 <= max_items <= 200):
        _err("output.max_items", "range", "1..200", max_items)

    # ---------- Final normalized config ----------
    normalized_sources = {}

    if normalized_channels:
        normalized_sources["telegram"] = {
            "channels": normalized_channels,
            "limit_per_channel": limit_per_channel,
        }

    if normalized_web_sites:
        normalized_sources["web"] = {
            "sites": normalized_web_sites,
        }

    if normalized_api:
        normalized_sources["api"] = normalized_api

    return {
        "version": 1,
        "task": {
            "name": name.strip(),
            "description": description,
        },
        "time": {
            "lookback_hours": lookback_hours,
        },
        "sources": normalized_sources,
        "filters": {
            "include_keywords": include_keywords,
            "exclude_keywords": exclude_keywords,
        },
        "output": {
            "max_items": max_items,
        },
    }
