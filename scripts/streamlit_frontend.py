"""Interactive Streamlit frontend for search, ablation, diary, and memory views."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.demo.dashboard_service import (
    build_summary_table,
    get_query_record,
    get_random_query,
    list_available_methods,
    list_datasets,
    load_learning_snapshot,
    search_demo,
)


METHOD_LABELS = {
    "baseline": "Baseline",
    "rewrite": "Rewrite Awareness",
    "rerank": "Rewrite + Rerank",
}

QUERY_SOURCE_OPTIONS = {
    "random": "Random Benchmark Query",
    "qid": "Benchmark by QID",
    "manual": "Manual Query",
}

TAB_NAMES = ["Search", "Ablation", "Learning Diary", "Memory Snapshot", "Research Notes"]


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


def _estimate_seconds(methods: list[str], topk: int, search_depth: int) -> int:
    base = max(2, int(search_depth / 25))
    extra = 0
    if "rewrite" in methods:
        extra += 6
    if "rerank" in methods:
        extra += max(8, int(topk / 2))
    return base + extra


def _resolve_query_record(dataset_key: str, source_key: str) -> dict | None:
    if source_key == "manual":
        manual_query = st.session_state.get("manual_query_input", "").strip()
        manual_gt = st.session_state.get("manual_gt_video_id", "").strip()
        if not manual_query:
            return None
        return {"qid": "manual", "query": manual_query, "gt_video_id": manual_gt or None}

    if source_key == "qid":
        qid = st.session_state.get("benchmark_qid", 0)
        return get_query_record(dataset_key, qid)

    query_record = st.session_state.get("selected_query_record")
    if query_record:
        return query_record
    seed = _safe_int(st.session_state.get("random_seed", 0), 0)
    query_record = get_random_query(dataset_key, seed=seed)
    st.session_state["selected_query_record"] = query_record
    return query_record


def _show_query_block(query_record: dict | None) -> None:
    st.subheader("Current Query")
    if not query_record:
        st.info("Choose a query source and click Search.")
        return
    st.write(query_record.get("query", ""))
    st.caption(f"qid={query_record.get('qid', 'n/a')} | gt_video_id={query_record.get('gt_video_id', 'n/a')}")


def _show_result_card(result: dict, idx: int) -> None:
    st.markdown(f"#### Result {idx}")
    left, right = st.columns([1.6, 1.0])
    with left:
        st.write(f"video_id: `{result.get('video_id', '')}`")
        st.write(f"segment_id: `{result.get('segment_id', '')}`")
        retrieval = _safe_float(result.get("retrieval_score"))
        if result.get("llm_score") is not None:
            st.write(f"retrieval_score={retrieval:.4f} | llm_score={_safe_float(result.get('llm_score')):.4f}")
        else:
            st.write(f"retrieval_score={retrieval:.4f}")
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
            st.warning("Video file not found.")


def _show_single_method_result(result: dict) -> None:
    row1 = st.columns(4)
    row1[0].metric("Method", _method_label(str(result.get("method", ""))))
    row1[1].metric("Returned", len(result.get("results", [])))
    row1[2].metric("GT Rank (Retrieval@200)", result.get("retrieval_gt_rank") or "N/A")
    row1[3].metric("GT Rank (Displayed)", result.get("final_gt_rank") or "N/A")

    row2 = st.columns(4)
    row2[0].metric("LLM Ready", "Yes" if result.get("llm_available") else "No")
    row2[1].metric("Rewrite Used", "Yes" if (result.get("rewrite_meta") or {}).get("used_rewrite") else "No")
    row2[2].metric("GT Video", result.get("gt_video_id") or "unknown")
    row2[3].metric("Estimated Time", f"{_safe_int(result.get('estimated_seconds', 0))}s")

    ambiguity = result.get("ambiguity") or {}
    if ambiguity:
        with st.expander("Ambiguity Analysis"):
            st.json(ambiguity)

    rewrite_meta = result.get("rewrite_meta") or {}
    if rewrite_meta:
        with st.expander("Rewrite Details"):
            st.json(rewrite_meta)

    results = result.get("results", [])
    if not results:
        st.warning("No results returned.")
        return
    for idx, item in enumerate(results, start=1):
        _show_result_card(item, idx)


def _show_search_panel() -> None:
    results = st.session_state.get("last_search_results") or []
    if not results:
        st.info("Run a search from the sidebar to see retrieved videos, GT rank, and method comparison.")
        return
    st.subheader("Search Results")
    if len(results) == 1:
        _show_single_method_result(results[0])
        return
    tabs = st.tabs([_method_label(str(r.get("method", ""))) for r in results])
    for tab, result in zip(tabs, results):
        with tab:
            _show_single_method_result(result)


def _show_ablation_panel() -> None:
    st.subheader("Ablation Board")
    rows = build_summary_table()
    if not rows:
        st.info("No summary files found yet.")
        return
    st.dataframe(rows, use_container_width=True)


def _show_diary_panel(snapshot: dict) -> None:
    st.subheader("Learning Diary")
    diary_rows = snapshot.get("learning_diary") or []
    if not diary_rows:
        st.info("No learning diary entries found.")
        return
    st.caption(f"Total learning events: {len(diary_rows)}")
    for row in reversed(diary_rows[-20:]):
        title = str(row.get("title") or row.get("stage") or row.get("time") or "Learning Event")
        with st.expander(title):
            st.json(row)


def _show_memory_panel(snapshot: dict) -> None:
    st.subheader("Memory Snapshot")
    cols = st.columns(4)
    cols[0].metric("Policy Hints", len(snapshot.get("policy_hints") or []))
    cols[1].metric("Semantic Memory", len(snapshot.get("semantic_memory") or []))
    cols[2].metric("Prototype Memory", len(snapshot.get("prototype_memory") or []))
    cols[3].metric("Learning Events", len(snapshot.get("learning_diary") or []))


def _show_notes_panel(snapshot: dict) -> None:
    st.subheader("Research Notes")
    notes = snapshot.get("research_notes") or ""
    if not notes:
        st.info("No research notes found.")
        return
    st.text(notes)


def main() -> None:
    st.set_page_config(page_title="Video Retrieval Demo", layout="wide")
    st.title("Video Retrieval Demo")
    st.caption("Interactive search console for baseline, rewrite, and rerank retrieval.")
    st.write("Frontend loaded successfully.")

    datasets = list_datasets()
    dataset_labels = {meta["label"]: key for key, meta in datasets.items()}

    with st.sidebar:
        st.header("Search Controls")
        dataset_label = st.selectbox("Dataset", list(dataset_labels.keys()))
        dataset_key = dataset_labels[dataset_label]

        query_source_label = st.radio("Query source", list(QUERY_SOURCE_OPTIONS.values()))
        source_key = {v: k for k, v in QUERY_SOURCE_OPTIONS.items()}[query_source_label]

        methods = list_available_methods()
        method_keys = [m["key"] for m in methods]
        selected_methods = st.multiselect("Search methods", method_keys, default=["baseline"], format_func=_method_label)

        topk = st.slider("Top-k results", min_value=3, max_value=20, value=5)
        search_depth = st.slider("Search depth", min_value=20, max_value=200, value=50, step=10)

        if source_key == "random":
            st.number_input("Random seed", min_value=0, max_value=100000, key="random_seed")
            if st.button("随机生成测试集 Query", use_container_width=True):
                seed = _safe_int(st.session_state.get("random_seed", 0), 0)
                st.session_state["selected_query_record"] = get_random_query(dataset_key, seed=seed)

        if source_key == "qid":
            st.number_input("Benchmark QID", min_value=0, value=0, step=1, key="benchmark_qid")

        if source_key == "manual":
            st.text_input("Manual GT video id (optional)", key="manual_gt_video_id")

        query_record = _resolve_query_record(dataset_key, source_key)
        default_query = str(query_record.get("query", "")) if query_record else ""
        if source_key == "manual":
            st.text_area("Search query", value=default_query, height=120, key="manual_query_input")
        else:
            st.text_area("Search query", value=default_query, height=120, disabled=True)

        estimated = _estimate_seconds(selected_methods, topk, search_depth)
        st.info(f"预计检索时间：约 {estimated} 秒")

        if st.button("Search", type="primary", use_container_width=True):
            query_record = _resolve_query_record(dataset_key, source_key)
            if not query_record or not str(query_record.get("query", "")).strip():
                st.warning("Please provide a query before searching.")
            elif not selected_methods:
                st.warning("Please select at least one search method.")
            else:
                collected = []
                for method_key in selected_methods:
                    collected.append(search_demo(dataset_key=dataset_key, query_text=str(query_record.get("query", "")), method=method_key, topk=topk, gt_video_id=query_record.get("gt_video_id"), search_depth=search_depth))
                st.session_state["active_query_record"] = query_record
                st.session_state["last_search_results"] = collected

    active_query = st.session_state.get("active_query_record") or _resolve_query_record(dataset_key, source_key)
    _show_query_block(active_query)

    snapshot = load_learning_snapshot()
    search_tab, ablation_tab, diary_tab, memory_tab, notes_tab = st.tabs(TAB_NAMES)
    with search_tab:
        _show_search_panel()
    with ablation_tab:
        _show_ablation_panel()
    with diary_tab:
        _show_diary_panel(snapshot)
    with memory_tab:
        _show_memory_panel(snapshot)
    with notes_tab:
        _show_notes_panel(snapshot)


main()
