from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import altair as alt
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.demo.dashboard_service import (  # noqa: E402
    build_summary_table,
    get_query_record,
    get_random_query,
    list_available_methods,
    list_datasets,
    load_learning_snapshot,
    search_demo,
)


APP_TITLE = "Video Retrieval Agent"
PAGE_KEYS = {
    "home": "Home",
    "results": "Search Results",
    "history": "History",
    "logs": "Learning Logs",
    "ablations": "Ablations",
}
METHOD_LABELS = {
    "baseline": "Baseline",
    "rewrite": "Rewrite",
    "rerank": "Rewrite + Rerank",
}
QUERY_SOURCE_OPTIONS = {
    "random": "Random Benchmark Query",
    "qid": "Benchmark by QID",
    "manual": "Manual Query",
}

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "feedback"
SEARCH_HISTORY_PATH = OUTPUT_DIR / "frontend_search_history.jsonl"
USER_FEEDBACK_PATH = OUTPUT_DIR / "frontend_user_feedback.jsonl"
PAGE_ORDER = list(PAGE_KEYS.keys())


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _method_label(key: str) -> str:
    return METHOD_LABELS.get(key, key)


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        return _to_jsonable(vars(value))
    return str(value)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_to_jsonable(payload), ensure_ascii=False) + "\n")


def _latest_rows(path: Path, limit: int = 10) -> list[dict[str, Any]]:
    rows = _read_jsonl(path)
    return list(reversed(rows[-limit:]))


def _set_page(page_key: str) -> None:
    st.session_state["active_page"] = page_key


def _inject_style() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(197, 221, 244, 0.55), transparent 32%),
                radial-gradient(circle at bottom left, rgba(248, 225, 196, 0.45), transparent 28%),
                linear-gradient(180deg, #f7f4ef 0%, #f4f1eb 100%);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #18222b 0%, #223241 100%);
        }
        [data-testid="stSidebar"] * {
            color: #f6f2ea;
        }
        .hero-card {
            padding: 1.1rem 1.2rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.74);
            border: 1px solid rgba(24,34,43,0.08);
            box-shadow: 0 18px 45px rgba(24,34,43,0.08);
            margin-bottom: 1rem;
        }
        .section-card {
            padding: 0.9rem 1rem;
            border-radius: 16px;
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(24,34,43,0.08);
            margin-bottom: 0.8rem;
        }
        .small-note {
            color: #56636d;
            font-size: 0.92rem;
        }
        .nav-wrap {
            padding: 0.15rem 0 0.85rem 0;
            margin-bottom: 0.65rem;
            border-bottom: 1px solid rgba(21, 32, 42, 0.10);
        }
        div[role="radiogroup"] {
            gap: 1.1rem;
        }
        div[role="radiogroup"] > label {
            background: transparent;
            border: none;
            border-bottom: 3px solid transparent;
            border-radius: 0;
            padding: 0.45rem 0.15rem 0.7rem 0.15rem;
            transition: all 180ms ease;
            min-width: fit-content;
        }
        div[role="radiogroup"] > label:hover {
            border-bottom-color: rgba(209, 72, 54, 0.40);
            transform: translateY(-1px);
        }
        div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
            display: none;
        }
        div[role="radiogroup"] > label span {
            font-size: 1.05rem;
            font-weight: 500;
            color: #243545;
        }
        div[role="radiogroup"] > label:has(input:checked) {
            border-bottom-color: #d64b3b;
        }
        div[role="radiogroup"] > label:has(input:checked) span {
            color: #d64b3b;
            font-weight: 600;
        }
        .stButton > button {
            border-radius: 12px;
            border: 1px solid rgba(24,34,43,0.15);
            background: #fffdf9;
            color: #15202a;
            font-weight: 600;
            transition: all 180ms ease;
        }
        .stButton > button:hover {
            border-color: #24465e;
            color: #10202d;
            box-shadow: 0 10px 24px rgba(36, 70, 94, 0.12);
            transform: translateY(-1px);
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #173247 0%, #2a516f 100%);
            color: #f8f3eb;
            border: none;
        }
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(24,34,43,0.08);
            padding: 0.85rem 0.95rem;
            border-radius: 16px;
            box-shadow: 0 12px 28px rgba(24,34,43,0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _estimate_seconds(methods: list[str], topk: int, search_depth: int) -> int:
    base = max(2, int(search_depth / 25))
    extra = 0
    if "rewrite" in methods:
        extra += 6
    if "rerank" in methods:
        extra += max(8, int(topk / 2))
    return base + extra


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    if seconds < 60:
        return f"{seconds}s"
    minutes, rest = divmod(seconds, 60)
    return f"{minutes}m {rest}s"


def _estimate_remaining_seconds(
    elapsed_seconds: float,
    completed: int,
    total: int,
    fallback_total_seconds: int,
) -> float:
    remaining_steps = max(0, total - completed)
    if remaining_steps == 0:
        return 0.0
    if completed > 0:
        return (elapsed_seconds / completed) * remaining_steps
    return max(0.0, float(fallback_total_seconds))


def _metric_curve_chart(
    chart_rows: list[dict[str, Any]],
    *,
    mark: str = "line",
) -> alt.Chart:
    data: list[dict[str, Any]] = []
    for idx, row in enumerate(chart_rows, start=1):
        label = str(row.get("file", f"run_{idx}"))
        short_label = label.replace(".json", "")[-36:]
        for metric in ("R@1", "R@5", "R@10"):
            data.append(
                {
                    "step": idx,
                    "run": short_label,
                    "metric": metric,
                    "value": _safe_float(row.get(metric)),
                }
            )

    base = alt.Chart(alt.Data(values=data)).encode(
        x=alt.X("step:O", title="实验轮次"),
        y=alt.Y("value:Q", title="Recall (%)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "metric:N",
            title="指标",
            scale=alt.Scale(
                domain=["R@1", "R@5", "R@10"],
                range=["#C44E52", "#4C78A8", "#59A14F"],
            ),
        ),
        tooltip=[
            alt.Tooltip("run:N", title="实验"),
            alt.Tooltip("metric:N", title="指标"),
            alt.Tooltip("value:Q", title="数值", format=".2f"),
        ],
    )
    if mark == "area":
        return base.mark_area(opacity=0.22, interpolate="monotone") + base.mark_line(
            point=True,
            strokeWidth=2.2,
            interpolate="monotone",
        )
    return base.mark_line(point=True, strokeWidth=2.2, interpolate="monotone")


def _resolve_query_record(dataset_key: str, source_key: str) -> dict[str, Any] | None:
    if source_key == "manual":
        query_text = st.session_state.get("manual_query_input", "").strip()
        if not query_text:
            return None
        manual_gt = st.session_state.get("manual_gt_video_id", "").strip()
        return {
            "qid": "manual",
            "query": query_text,
            "gt_video_id": manual_gt or None,
        }
    if source_key == "qid":
        qid = st.session_state.get("benchmark_qid", 0)
        return get_query_record(dataset_key, qid)
    current = st.session_state.get("selected_query_record")
    if current:
        return current
    seed = _safe_int(st.session_state.get("random_seed", 0), 0)
    current = get_random_query(dataset_key, seed=seed)
    st.session_state["selected_query_record"] = current
    return current


def _search_record_payload(
    *,
    dataset_key: str,
    source_key: str,
    query_record: dict[str, Any],
    methods: list[str],
    topk: int,
    search_depth: int,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "time": datetime.now().isoformat(timespec="seconds"),
        "dataset_key": dataset_key,
        "query_source": source_key,
        "query_record": query_record,
        "methods": methods,
        "topk": topk,
        "search_depth": search_depth,
        "results": results,
    }


def _save_history(record: dict[str, Any]) -> None:
    _append_jsonl(SEARCH_HISTORY_PATH, _to_jsonable(record))


def _save_feedback(
    *,
    history_id: str,
    query_text: str,
    preferred_video_id: str,
    feedback_type: str,
    note: str,
    search_results: list[dict[str, Any]],
) -> None:
    payload = {
        "schema_version": "frontend_user_feedback_v1",
        "time": datetime.now().isoformat(timespec="seconds"),
        "history_id": history_id,
        "query": query_text,
        "preferred_video_id": preferred_video_id,
        "feedback_type": feedback_type,
        "note": note,
        "search_results": search_results,
        "status": "queued_for_learning",
    }
    _append_jsonl(USER_FEEDBACK_PATH, _to_jsonable(payload))


def _show_result_card(result: dict[str, Any], idx: int) -> None:
    st.markdown(f"#### Top {idx}")
    left, right = st.columns([1.5, 1.0])
    with left:
        st.write(f"video_id: `{result.get('video_id', '')}`")
        st.write(f"segment_id: `{result.get('segment_id', '')}`")
        st.write(
            f"retrieval_score={_safe_float(result.get('retrieval_score')):.4f}"
            + (
                f" | llm_score={_safe_float(result.get('llm_score')):.4f}"
                if result.get("llm_score") is not None else ""
            )
        )
        st.write(f"time={_safe_float(result.get('start_sec')):.2f}s -> {_safe_float(result.get('end_sec')):.2f}s")
        if result.get("semantic_summary"):
            st.write(f"summary: {result['semantic_summary']}")
        tags = result.get("semantic_tags") or []
        if tags:
            st.write("tags: " + ", ".join(map(str, tags)))
        if result.get("rerank_reason"):
            st.write(f"rerank_reason: {result['rerank_reason']}")
    with right:
        video_path = result.get("video_path")
        if video_path and Path(video_path).exists():
            st.video(str(video_path), start_time=_safe_int(result.get("start_sec"), 0))
        else:
            st.info("Video file not found in local path.")


def _show_method_result(method_result: dict[str, Any], show_gt: bool) -> None:
    method_key = str(method_result.get("method", ""))
    llm_needed = method_key in {"rewrite", "rerank"}
    rewrite_meta = method_result.get("rewrite_meta") or {}
    rewrite_state = "N/A"
    if method_key in {"rewrite", "rerank"}:
        rewrite_state = "Yes" if rewrite_meta.get("used_rewrite") else "No"

    row1 = st.columns(4)
    row1[0].metric("Method", _method_label(method_key))
    row1[1].metric("Returned", len(method_result.get("results", [])))
    row1[2].metric("Search Time", f"{_safe_int(method_result.get('estimated_seconds', 0))}s")
    row1[3].metric("LLM Ready", "Yes" if (llm_needed and method_result.get("llm_available")) else ("N/A" if not llm_needed else "No"))

    if show_gt:
        row2 = st.columns(4)
        row2[0].metric("GT Video", method_result.get("gt_video_id") or "unknown")
        row2[1].metric("GT Rank@Depth", method_result.get("retrieval_gt_rank") or "N/A")
        row2[2].metric("GT Rank@Top5", method_result.get("final_gt_rank") or "N/A")
        row2[3].metric("Rewrite Used", rewrite_state)
    else:
        st.caption("Manual query mode: GT rank is hidden because no benchmark ground truth is provided.")

    ambiguity = method_result.get("ambiguity") or {}
    if ambiguity:
        with st.expander("Ambiguity Analysis"):
            st.json(_to_jsonable(ambiguity))

    rewrite_meta = method_result.get("rewrite_meta") or {}
    if rewrite_meta:
        with st.expander("Rewrite Details"):
            st.json(_to_jsonable(rewrite_meta))

    for idx, item in enumerate(method_result.get("results", [])[:5], start=1):
        _show_result_card(item, idx)


def _show_feedback_form(active_record: dict[str, Any]) -> None:
    query_record = active_record.get("query_record") or {}
    if query_record.get("gt_video_id"):
        return
    st.markdown("### User Feedback")
    method_options = active_record.get("results") or []
    candidate_options: list[tuple[str, str]] = [("none", "None of the Top5 is correct")]
    for result in method_options:
        for item in result.get("results", [])[:5]:
            video_id = str(item.get("video_id", ""))
            label = f"{_method_label(str(result.get('method', '')))} | {video_id}"
            candidate_options.append((video_id, label))
    selected_label = st.selectbox("Preferred result", [label for _vid, label in candidate_options], key="feedback_choice")
    selected_video_id = next((vid for vid, label in candidate_options if label == selected_label), "none")
    feedback_type = st.radio("Feedback type", ["prefer_top_candidate", "all_wrong", "partial_match"], horizontal=True)
    note = st.text_area("Feedback note", height=100, key="feedback_note")
    if st.button("Save Feedback And Queue Learning", use_container_width=True):
        _save_feedback(
            history_id=str(active_record.get("id", "")),
            query_text=str(query_record.get("query", "")),
            preferred_video_id=selected_video_id,
            feedback_type=feedback_type,
            note=note.strip(),
            search_results=method_options,
        )
        st.success("Feedback saved. It has been added to the learning queue.")


def _render_results_record(active_record: dict[str, Any]) -> None:
    query_record = active_record.get("query_record") or {}
    show_gt = bool(query_record.get("gt_video_id"))
    st.markdown(
        f"""
        <div class="hero-card">
            <h3 style="margin:0;">Search Results</h3>
            <div class="small-note">Query: {query_record.get("query", "")}</div>
            <div class="small-note">Source: {active_record.get("query_source", "unknown")} | Time: {active_record.get("time", "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    results = active_record.get("results") or []
    if not results:
        st.warning("No search results available.")
        return
    tabs = st.tabs([_method_label(str(item.get("method", ""))) for item in results])
    for tab, method_result in zip(tabs, results):
        with tab:
            _show_method_result(method_result, show_gt=show_gt)
    _show_feedback_form(active_record)


def _render_top_nav() -> None:
    st.markdown('<div class="nav-wrap"></div>', unsafe_allow_html=True)
    current_page = st.session_state.get("active_page", "home")
    current_index = PAGE_ORDER.index(current_page) if current_page in PAGE_ORDER else 0
    selected_label = st.radio(
        "Navigation",
        [PAGE_KEYS[key] for key in PAGE_ORDER],
        index=current_index,
        horizontal=True,
        label_visibility="collapsed",
    )
    selected_key = next((key for key, label in PAGE_KEYS.items() if label == selected_label), "home")
    if selected_key != current_page:
        _set_page(selected_key)
        st.rerun()


def _render_home_page() -> None:
    datasets = list_datasets()
    dataset_labels = {meta["label"]: key for key, meta in datasets.items()}

    st.markdown(
        """
        <div class="hero-card">
            <h2 style="margin:0;">Natural Language Video Retrieval Agent</h2>
            <p class="small-note" style="margin-top:0.35rem;">
                Search with baseline / rewrite / rerank, inspect GT rank on benchmark queries,
                collect manual feedback, and keep a compact learning trace for later self-improvement.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.15, 0.85])
    with col_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        dataset_label = st.selectbox("Dataset", list(dataset_labels.keys()))
        dataset_key = dataset_labels[dataset_label]

        query_source_label = st.radio("Query Source", list(QUERY_SOURCE_OPTIONS.values()))
        source_key = {value: key for key, value in QUERY_SOURCE_OPTIONS.items()}[query_source_label]

        method_keys = [item["key"] for item in list_available_methods()]
        selected_methods = st.multiselect(
            "Search Methods",
            method_keys,
            default=["baseline"],
            format_func=_method_label,
        )
        topk = st.slider("Displayed Top-k", min_value=3, max_value=5, value=5)
        search_depth = st.slider("Search Depth", min_value=20, max_value=200, value=50, step=10)

        if source_key == "random":
            seed_col, button_col = st.columns([2.5, 1.0])
            with seed_col:
                st.number_input("Random Seed", min_value=0, max_value=100000, value=0, step=1, key="random_seed")
            with button_col:
                st.write("")
                st.write("")
                if st.button("Random Query", use_container_width=True):
                    seed = _safe_int(st.session_state.get("random_seed", 0), 0)
                    draw_index = _safe_int(st.session_state.get("random_query_draw_index", 0), 0)
                    st.session_state["selected_query_record"] = get_random_query(dataset_key, seed=seed + draw_index)
                    st.session_state["random_query_draw_index"] = draw_index + 1
                    st.rerun()
        elif source_key == "qid":
            st.number_input("Benchmark QID", min_value=0, value=0, step=1, key="benchmark_qid")

        query_record = _resolve_query_record(dataset_key, source_key)
        default_query = str(query_record.get("query", "")) if query_record else ""
        if source_key == "manual":
            st.text_area("Query", value=default_query, height=130, key="manual_query_input")
            st.text_input("Optional GT Video ID", key="manual_gt_video_id")
        else:
            st.text_area("Query", value=default_query, height=130, disabled=True)

        estimated = _estimate_seconds(selected_methods, topk, search_depth)
        st.info(f"Estimated search time: about {estimated}s")
        if st.button("Search", type="primary", use_container_width=True):
            query_record = _resolve_query_record(dataset_key, source_key)
            if not query_record or not str(query_record.get("query", "")).strip():
                st.warning("Please provide a query before searching.")
            elif not selected_methods:
                st.warning("Please select at least one search method.")
            else:
                collected = []
                search_started_at = time.perf_counter()
                progress = st.progress(0.0, text="Preparing search...")
                status = st.empty()
                total_steps = max(1, len(selected_methods))
                for method_idx, method_key in enumerate(selected_methods, start=1):
                    completed_before = method_idx - 1
                    elapsed_before = time.perf_counter() - search_started_at
                    remaining_before = _estimate_remaining_seconds(
                        elapsed_seconds=elapsed_before,
                        completed=completed_before,
                        total=total_steps,
                        fallback_total_seconds=estimated,
                    )
                    progress.progress(
                        completed_before / total_steps,
                        text=(
                            f"Running {_method_label(method_key)} "
                            f"({completed_before}/{total_steps} completed) | "
                            f"elapsed {_format_duration(elapsed_before)} | "
                            f"ETA {_format_duration(remaining_before)}"
                        ),
                    )
                    status.info(
                        f"Searching with {_method_label(method_key)}... "
                        f"Elapsed {_format_duration(elapsed_before)}, "
                        f"estimated remaining {_format_duration(remaining_before)}."
                    )
                    method_started_at = time.perf_counter()
                    collected.append(
                        search_demo(
                            dataset_key=dataset_key,
                            query_text=str(query_record.get("query", "")),
                            method=method_key,
                            topk=topk,
                            gt_video_id=query_record.get("gt_video_id"),
                            search_depth=search_depth,
                        )
                    )
                    elapsed_now = time.perf_counter() - search_started_at
                    method_elapsed = time.perf_counter() - method_started_at
                    remaining_now = _estimate_remaining_seconds(
                        elapsed_seconds=elapsed_now,
                        completed=method_idx,
                        total=total_steps,
                        fallback_total_seconds=estimated,
                    )
                    progress.progress(
                        method_idx / total_steps,
                        text=(
                            f"Completed {method_idx}/{total_steps} methods | "
                            f"last {_method_label(method_key)} {_format_duration(method_elapsed)} | "
                            f"elapsed {_format_duration(elapsed_now)} | "
                            f"ETA {_format_duration(remaining_now)}"
                        ),
                    )
                total_elapsed = time.perf_counter() - search_started_at
                status.success(f"Search completed in {_format_duration(total_elapsed)}.")
                record = _search_record_payload(
                    dataset_key=dataset_key,
                    source_key=source_key,
                    query_record=query_record,
                    methods=selected_methods,
                    topk=topk,
                    search_depth=search_depth,
                    results=collected,
                )
                st.session_state["active_search_record"] = record
                _save_history(record)
                _set_page("results")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        query_record = _resolve_query_record(dataset_key, source_key)
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Current Query")
        if query_record:
            st.write(query_record.get("query", ""))
            if query_record.get("gt_video_id"):
                st.caption(f"qid={query_record.get('qid')} | gt_video_id={query_record.get('gt_video_id')}")
            else:
                st.caption("Manual query mode")
        else:
            st.info("Use Random Query or input your own query.")
        st.markdown("</div>", unsafe_allow_html=True)

        recent = _latest_rows(SEARCH_HISTORY_PATH, limit=3)
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Recent Searches")
        if recent:
            with st.container(height=220):
                for row in recent:
                    if st.button(f"{row.get('time', '')} | {str((row.get('query_record') or {}).get('query', ''))[:48]}", key=f"recent_{row.get('id')}"):
                        st.session_state["active_search_record"] = row
                        _set_page("results")
                        st.rerun()
        else:
            st.info("No recent searches yet.")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_results_page() -> None:
    active_record = st.session_state.get("active_search_record")
    if not active_record:
        st.info("No active search result. Run a search from Home or open one from History.")
        return
    _render_results_record(active_record)


def _render_history_page() -> None:
    st.markdown('<div class="hero-card"><h3 style="margin:0;">Search History</h3><div class="small-note">Only the most recent 10 searches are shown.</div></div>', unsafe_allow_html=True)
    rows = _latest_rows(SEARCH_HISTORY_PATH, limit=10)
    if not rows:
        st.info("No history yet.")
        return
    with st.container(height=460):
        for idx, row in enumerate(rows, start=1):
            query_text = str((row.get("query_record") or {}).get("query", ""))
            gt_video_id = (row.get("query_record") or {}).get("gt_video_id")
            left, right = st.columns([4.5, 1.0])
            with left:
                st.markdown(
                    f"""
                    <div class="section-card">
                        <strong>{idx}. {query_text[:120]}</strong><br/>
                        <span class="small-note">{row.get('time', '')} | source={row.get('query_source', '')} | gt={'yes' if gt_video_id else 'no'}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with right:
                if st.button("Open", key=f"open_history_{row.get('id')}"):
                    st.session_state["active_search_record"] = row
                    _set_page("results")
                    st.rerun()


def _render_logs_page() -> None:
    snapshot = load_learning_snapshot()
    auto_log_rows = _latest_rows(OUTPUT_DIR / "auto_continual_learning_log.jsonl", limit=12)
    user_feedback_rows = _latest_rows(USER_FEEDBACK_PATH, limit=12)
    st.markdown('<div class="hero-card"><h3 style="margin:0;">Learning Logs</h3><div class="small-note">Shows system learning traces, user feedback queue, and current stage snapshot.</div></div>', unsafe_allow_html=True)

    cols = st.columns(4)
    learning_counts = snapshot.get("learning_counts", {})
    cols[0].metric("Diary Events", learning_counts.get("total", 0))
    cols[1].metric("User Feedback", len(_read_jsonl(USER_FEEDBACK_PATH)))
    cols[2].metric("Auto Learning Logs", len(_read_jsonl(OUTPUT_DIR / "auto_continual_learning_log.jsonl")))
    cols[3].metric("Recent Search History", len(_read_jsonl(SEARCH_HISTORY_PATH)))

    left, right = st.columns(2)
    with left:
        st.subheader("User Feedback Queue")
        if not user_feedback_rows:
            st.info("No user feedback yet.")
        else:
            with st.container(height=340):
                for row in user_feedback_rows:
                    with st.expander(f"{row.get('time', '')} | {row.get('feedback_type', '')} | {str(row.get('query', ''))[:72]}"):
                        st.json(row)
    with right:
        st.subheader("Auto Learning Log")
        if not auto_log_rows:
            st.info("No auto learning runs yet.")
        else:
            with st.container(height=340):
                for row in auto_log_rows:
                    with st.expander(f"{row.get('time', '')} | {row.get('event', '')}"):
                        st.json(row)

    st.subheader("Learning Diary")
    diary_rows = snapshot.get("learning_diary") or []
    if diary_rows:
        with st.container(height=360):
            for row in reversed(diary_rows[-10:]):
                title = str(row.get("stage_label") or row.get("event_type") or row.get("time"))
                with st.expander(title):
                    st.json(row)
    else:
        st.info("No learning diary entries found.")


def _render_ablation_page() -> None:
    st.markdown('<div class="hero-card"><h3 style="margin:0;">Ablations And Analysis</h3><div class="small-note">Summary tables, current best comparisons, candidate recall, and failure-diagnosis signals.</div></div>', unsafe_allow_html=True)

    summary_rows = build_summary_table()
    if summary_rows:
        st.subheader("Summary Table")
        with st.container(height=320):
            st.dataframe(summary_rows, use_container_width=True)
        chart_rows = [
            {
                "file": row.get("file", ""),
                "R@1": _safe_float(row.get("R@1")),
                "R@5": _safe_float(row.get("R@5")),
                "R@10": _safe_float(row.get("R@10")),
            }
            for row in summary_rows[-20:]
        ]
        if chart_rows:
            st.subheader("Recent Metric Curves")
            st.altair_chart(_metric_curve_chart(chart_rows, mark="line"), use_container_width=True)
            st.subheader("Agent Learning Curve")
            st.altair_chart(_metric_curve_chart(chart_rows, mark="area"), use_container_width=True)
    else:
        st.info("No summary files found.")

    candidate_recall_path = PROJECT_ROOT / "outputs" / "tables" / "analysis" / "baseline_vith14_candidate_recall_top30_1kA_full.json"
    if candidate_recall_path.exists():
        payload = json.loads(candidate_recall_path.read_text(encoding="utf-8"))
        st.subheader("Candidate Recall")
        st.json(payload)

    failure_path = PROJECT_ROOT / "outputs" / "tables" / "analysis" / "failure_diagnosis_v35_1kA_q200.json"
    if failure_path.exists():
        failure_payload = json.loads(failure_path.read_text(encoding="utf-8"))
        st.subheader("Failure Diagnosis")
        cols = st.columns(2)
        with cols[0]:
            st.write("Rank Buckets")
            st.bar_chart(failure_payload.get("rank_buckets", {}))
        with cols[1]:
            st.write("Failure Tags")
            st.bar_chart(failure_payload.get("failure_tag_counts", {}))
        top_cases = failure_payload.get("failure_cases_top50", [])[:10]
        if top_cases:
            st.write("Representative Failure Cases")
            st.dataframe(top_cases, use_container_width=True)

    st.subheader("Analysis Notes")
    st.markdown(
        """
        - If `object / relation / person_attribute` dominate the failure chart, the model still lacks fine-grained cross-modal grounding.
        - If `gt_outside_top30` remains high, the next step should focus on stronger feedback teacher construction instead of only reranking.
        - If `R@5 / R@10` rise without `R@1`, the agent is learning broader recall but not top-1 calibration.
        """
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    _inject_style()
    st.session_state.setdefault("active_page", "home")
    st.markdown(f"# {APP_TITLE}")
    st.caption("Compact retrieval console with feedback-aware learning traces.")
    _render_top_nav()

    page = st.session_state.get("active_page", "home")
    if page == "home":
        _render_home_page()
    elif page == "results":
        _render_results_page()
    elif page == "history":
        _render_history_page()
    elif page == "logs":
        _render_logs_page()
    elif page == "ablations":
        _render_ablation_page()
    else:
        _render_home_page()


if __name__ == "__main__":
    main()
