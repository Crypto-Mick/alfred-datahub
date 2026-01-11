# Smart Parser UI

This is a local-only Streamlit UI that controls the smart parser by writing runtime input files and invoking the parser script. It is an engineering tool meant for running ad-hoc parsing jobs on Alfred.

**This UI does not import or depend on smart-parser code.**

## How to run

From this directory:

```bash
streamlit run app.py
```

The UI writes to `runtime/input/input.json`, runs the parser via `scripts/run_parser.sh`, and reads results from `runtime/output/summary.md` (and optionally `runtime/output/mapper_report.json`).
