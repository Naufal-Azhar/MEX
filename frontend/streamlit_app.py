"""Streamlit prototype UI for the F1 Technical Regulation Expert System."""

from __future__ import annotations

import json
import os
import sys
from html import escape
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import SAMPLE_FACTS_PATH, STORAGE_DIR, load_settings  # noqa: E402
from app.expert_system.knowledge_base import KnowledgeBase  # noqa: E402
from app.expert_system.service import ComplianceService  # noqa: E402
from app.learning.ask_service import AskService  # noqa: E402
from app.learning.service import TelemetryLearningService  # noqa: E402
from app.llm.fact_extractor import get_extractor  # noqa: E402
from app.race_data.alignment import align_laps  # noqa: E402
from app.rag.retriever import Retriever  # noqa: E402
from app.schemas.fact_specs import FACT_SPECS  # noqa: E402
from app.schemas.facts import FactInput  # noqa: E402
from app.schemas.learning import AskRequest  # noqa: E402
from app.telemetry.plots import save_comparison_plot  # noqa: E402

st.set_page_config(page_title="F1 / Technical Workbench", page_icon="◼", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{(Path(__file__).parent / 'theme.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

STATUS_LABEL = {
    "SATISFIED": "MEMENUHI KETENTUAN",
    "VIOLATED": "TIDAK MEMENUHI KETENTUAN",
    "INSUFFICIENT_DATA": "DATA BELUM CUKUP",
    "NOT_APPLICABLE": "TIDAK BERLAKU",
    "UNSUPPORTED": "DI LUAR CAKUPAN",
    "ERROR": "KESALAHAN SISTEM",
}
STATUS_STYLE = {
    "SATISFIED": st.success,
    "VIOLATED": st.error,
    "INSUFFICIENT_DATA": st.warning,
    "NOT_APPLICABLE": st.info,
    "UNSUPPORTED": st.warning,
    "ERROR": st.error,
}


@st.cache_resource
def get_kb() -> KnowledgeBase:
    return KnowledgeBase.from_file()


@st.cache_resource
def get_service() -> ComplianceService:
    return ComplianceService(get_kb())


@st.cache_resource
def get_retriever() -> Retriever:
    return Retriever.load_or_build()


@st.cache_resource
def get_learning_service() -> TelemetryLearningService:
    return TelemetryLearningService.default()


@st.cache_resource
def get_ask_service() -> AskService:
    return AskService.default()


def load_sample_facts() -> dict:
    data = json.loads(SAMPLE_FACTS_PATH.read_text(encoding="utf-8"))
    return {item["name"]: item["value"] for item in data["facts"]}


def api_request(base_url: str, path: str, payload: dict) -> dict | list:
    import httpx

    response = httpx.post(f"{base_url.rstrip('/')}{path}", json=payload, timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()


def api_get(base_url: str, path: str) -> dict | list:
    import httpx

    response = httpx.get(f"{base_url.rstrip('/')}{path}", timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()


def status_badge(status: str) -> None:
    STATUS_STYLE.get(status, st.info)(f"**{status} — {STATUS_LABEL.get(status, status)}**")


def update_fact_widgets(facts: dict) -> None:
    """Keep visible widgets aligned when sample or extracted facts change."""
    for key in list(st.session_state):
        if not key.startswith("fact_"):
            continue
        name = next((fact for fact in FACT_SPECS if key.endswith(f"_{fact}")), None)
        if name is None:
            continue
        value = facts.get(name, "")
        spec = FACT_SPECS[name]
        if spec["kind"] == "boolean":
            st.session_state[key] = "Ya" if value is True else "Tidak" if value is False else "(tidak diisi)"
        elif spec["kind"] == "number":
            st.session_state[key] = "" if value == "" else str(value)
        else:
            st.session_state[key] = value if value in spec.get("allowed", []) else "(tidak diisi)"


def facts_to_payload(facts: dict) -> list[dict]:
    payload = []
    for name, value in facts.items():
        if value is None or value == "":
            continue
        spec = FACT_SPECS.get(name, {})
        payload.append({"name": name, "value": value, "unit": spec.get("unit")})
    return payload


def render_report(report: dict) -> None:
    status_badge(report["status"])
    if report.get("validation_warning"):
        st.warning(report["validation_warning"])
    st.markdown(report["explanation"])
    if report.get("source"):
        source = report["source"]
        st.caption(
            f"Sumber: {source['document']} — Article {source['article']} "
            f"(halaman {source['page']}), Issue {source['issue']}"
        )
        st.info(f'"{source["quote"]}"')

    if report.get("diagnostics"):
        import pandas as pd

        st.subheader("Diagnostik")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Kode": item["code"],
                        "Pesan": item["message"],
                        "Aturan": item.get("rule_id") or "-",
                    }
                    for item in report["diagnostics"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if report.get("conflicts"):
        import pandas as pd

        st.subheader("Konflik fakta")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Fakta": item["name"],
                        "Nilai lama": f"{item['existing_value']} {item.get('existing_unit') or ''}",
                        "Nilai baru": f"{item['new_value']} {item.get('new_unit') or ''}",
                    }
                    for item in report["conflicts"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if report.get("applicability_conditions"):
        import pandas as pd

        st.subheader("Konteks penerapan aturan")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Konteks": condition["expression"],
                        "Status": condition["status"],
                        "Nilai": condition.get("left_value"),
                    }
                    for condition in report["applicability_conditions"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if report.get("conditions"):
        import pandas as pd

        st.subheader("Kondisi yang diperiksa")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Syarat": condition["expression"],
                        "Status": condition["status"],
                        "Nilai": condition.get("left_value"),
                        "Pembanding": condition.get("right_value"),
                        "Catatan": condition.get("detail") or "",
                    }
                    for condition in report["conditions"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if report.get("missing_facts"):
        import pandas as pd

        st.subheader("Fakta yang masih diperlukan")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Fakta": item["fact"],
                        "Satuan": item.get("expected_unit"),
                        "Alasan": item["reason"],
                        "Artikel": item.get("source_article"),
                    }
                    for item in report["missing_facts"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if report.get("citations"):
        import pandas as pd

        st.subheader("Sitasi sumber")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Artikel": item["article"],
                        "Halaman": item.get("page"),
                        "Terverifikasi": "ya" if item.get("verified") else "tidak",
                        "Kutipan": item["quote"],
                    }
                    for item in report["citations"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if report.get("rules_evaluated"):
        import pandas as pd

        st.subheader("Aturan yang dievaluasi")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Rule": item["rule_id"],
                        "Goal": item["goal"],
                        "Status aturan": item.get("rule_status"),
                        "Berlaku": item.get("applicable"),
                        "Hasil": item["status"],
                        "Nilai": item.get("conclusion_value"),
                    }
                    for item in report["rules_evaluated"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if report.get("proof_trace"):
        st.subheader("Jejak Backward Chaining")
        st.code(render_trace_text_from_dict(report["proof_trace"]), language="text")
        with st.expander("Trace lengkap (JSON)"):
            st.json(report["proof_trace"])

    with st.expander("Fakta yang digunakan"):
        st.json(report.get("facts_used", {}))
    with st.expander("Keterbatasan sistem"):
        for limitation in report.get("limitations", []):
            st.markdown(f"- {limitation}")

    st.download_button(
        "Unduh hasil sebagai JSON",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name=f"{report.get('goal_id', 'result')}.json",
        mime="application/json",
        key=f"download_{report.get('goal_id', 'result')}",
    )


def render_trace_text_from_dict(node: dict, indent: int = 0) -> str:
    pad = "  " * indent
    line = f"{pad}- [{node['status']}] {node['goal']}"
    if node.get("rule_id"):
        line += f" via {node['rule_id']}"
    if node.get("value") is not None:
        line += f" = {node['value']}"
    lines = [line]
    if node.get("expression"):
        lines.append(f"{pad}  hitung: {node['expression']}")
    for condition in node.get("conditions", []):
        lines.append(f"{pad}  syarat: [{condition['status']}] {condition['expression']}")
    for note in node.get("notes", []):
        lines.append(f"{pad}  catatan: {note}")
    for child in node.get("children", []):
        lines.append(render_trace_text_from_dict(child, indent + 1))
    return "\n".join(lines)


def fact_input_widgets(goal: str, requirements: list[dict], defaults: dict) -> dict:
    values: dict = {}
    columns = st.columns(2)
    for index, requirement in enumerate(requirements):
        name = requirement["name"]
        spec = FACT_SPECS.get(name, {})
        column = columns[index % 2]
        key = f"fact_{goal}_{name}"
        current = defaults.get(name, "")
        with column:
            if spec.get("kind") == "number":
                unit = spec.get("unit") or ""
                text = st.text_input(f"{name} ({unit})", value="" if current == "" else str(current), key=key)
                values[name] = text
            elif spec.get("kind") == "boolean":
                options = ["(tidak diisi)", "Ya", "Tidak"]
                if isinstance(current, bool):
                    options_index = 1 if current else 2
                else:
                    options_index = 0
                choice = st.selectbox(name, options, index=options_index, key=key)
                values[name] = {"Ya": True, "Tidak": False}.get(choice, "")
            else:
                allowed = spec.get("allowed", [])
                options = ["(tidak diisi)"] + allowed
                index = options.index(current) if current in options else 0
                values[name] = st.selectbox(name, options, index=index, key=key)
                if values[name] == "(tidak diisi)":
                    values[name] = ""
    return values


def normalize_values(values: dict) -> dict:
    result = {}
    for name, value in values.items():
        if value == "" or value is None:
            continue
        if isinstance(value, str):
            try:
                numeric = value.strip().replace(",", ".")
                result[name] = float(numeric) if "." in numeric else int(numeric)
                continue
            except ValueError:
                pass
        result[name] = value
    return result


def _run_telemetry_analysis(mode: str, api_url: str, learning: TelemetryLearningService, payload: dict) -> dict:
    if mode == "FastAPI":
        return api_request(api_url, "/v1/telemetry/analyze", payload)
    segment = None
    if payload.get("segment_start_m") is not None and payload.get("segment_end_m") is not None:
        segment = (payload["segment_start_m"], payload["segment_end_m"])
    report = learning.analyze(
        payload["lap_a_id"],
        payload["lap_b_id"],
        segment=segment,
        question=payload.get("question"),
        level=payload.get("level", "beginner"),
    )
    return report.model_dump(mode="json")


def _run_ask(mode: str, api_url: str, ask_service: AskService, payload: dict) -> dict:
    if mode == "FastAPI":
        return api_request(api_url, "/v1/ask", payload)
    return ask_service.ask(AskRequest(**payload)).model_dump(mode="json")


def render_telemetry_plot(learning: TelemetryLearningService, lap_a: str, lap_b: str) -> None:
    if lap_a not in learning.telemetry.laps or lap_b not in learning.telemetry.laps:
        return
    aligned = align_laps(learning.telemetry.laps[lap_a], learning.telemetry.laps[lap_b])
    path = STORAGE_DIR / "plots" / f"{lap_a}_vs_{lap_b}.png"
    save_comparison_plot(aligned, path, f"{lap_a} vs {lap_b}", lap_a, lap_b)
    st.image(str(path), caption="Speed / throttle / brake terhadap jarak. Area merah = gap data.")


def render_telemetry_report(report: dict, learning: TelemetryLearningService) -> None:
    import pandas as pd

    st.subheader("Status gerbang bukti")
    data_gate = report.get("data_gate", {})
    knowledge_gate = report.get("knowledge_gate", {})
    gate_col_a, gate_col_b, gate_col_c = st.columns(3)
    with gate_col_a:
        st.metric("Data gate", "PASS" if data_gate.get("passed") else "FAIL")
    with gate_col_b:
        st.metric("Knowledge gate", "PASS" if knowledge_gate.get("passed") else "FAIL")
    with gate_col_c:
        st.metric("Interpretasi", report.get("engineering_interpretation_status", "-"))
    if data_gate.get("missing"):
        st.error("Data kurang: " + "; ".join(data_gate["missing"]))
    if knowledge_gate.get("missing"):
        st.error("Bukti tidak terlacak: " + "; ".join(knowledge_gate["missing"]))

    st.subheader("Kualitas data")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Lap": lap_id,
                    "Sampel": quality["sample_count"],
                    "Durasi (s)": quality["duration_s"],
                    "Jarak (m)": quality["distance_m"],
                    "Median dt (s)": quality["median_dt_s"],
                    "Gap maks (s)": quality["max_gap_s"],
                    "Gap > batas": len(quality.get("gaps", [])),
                }
                for lap_id, quality in report.get("quality", {}).items()
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    speed_delta = report.get("speed_delta")
    if speed_delta:
        cols = st.columns(4)
        cols[0].metric("Delta rata-rata", f"{speed_delta['mean_km_h']:.2f} km/h")
        cols[1].metric("Delta min", f"{speed_delta['min_km_h']:.2f} km/h")
        cols[2].metric("Delta maks", f"{speed_delta['max_km_h']:.2f} km/h")
        cols[3].metric("Coverage", f"{speed_delta['coverage_ratio']:.3f}")

    st.subheader("Fakta terukur")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Fakta": fact["name"],
                    "Nilai": fact["value"],
                    "Satuan": fact.get("unit"),
                    "Status": fact["status"],
                    "Detail": fact.get("detail") or "",
                }
                for fact in report.get("observed_facts", [])
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Temuan berbasis aturan")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Rule": finding["rule_id"],
                    "Goal": finding["goal"],
                    "Status": finding["status"],
                    "Status aturan": finding["rule_status"],
                }
                for finding in report.get("findings", [])
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    comparisons = report.get("brake_onset_comparisons", [])
    if comparisons:
        st.subheader("Perbandingan brake onset")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Onset A (m)": item["onset_a"]["distance_m"],
                        "Onset B (m)": item["onset_b"]["distance_m"],
                        "Delta B-A (m)": item["delta_m"],
                        "Dalam uncertainty": "ya" if item["within_alignment_uncertainty"] else "tidak",
                    }
                    for item in comparisons
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    render_telemetry_plot(learning, report["lap_a"]["lap_id"], report["lap_b"]["lap_id"])

    with st.expander("Data yang kurang"):
        for item in report.get("missing_data", []):
            st.markdown(f"- {item}")
    with st.expander("Keterbatasan"):
        for item in report.get("limitations", []):
            st.markdown(f"- {item}")
    with st.expander("Trace inferensi (JSON)"):
        st.json(report.get("trace", []))

    st.download_button(
        "Unduh analisis sebagai JSON",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name=f"{report.get('analysis_id', 'analysis')}.json",
        mime="application/json",
        key=f"download_{report.get('analysis_id', 'analysis')}",
    )


def render_race_analysis(learning: TelemetryLearningService, mode: str, api_url: str) -> None:
    st.markdown('<div class="workbench-eyebrow">MEX-AI / RACE ANALYSIS</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="workbench-title">Race Analysis<span style="color:#7f8792">.</span></h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="workbench-lede">Bandingkan dua lap dari sesi yang sama. Fakta terukur dipisahkan dari interpretasi, '
        'dan data yang tidak tersedia tidak diubah menjadi kesimpulan.</p><div class="workbench-rule"></div>',
        unsafe_allow_html=True,
    )
    st.warning("Fixture publik 2025 Abu Dhabi Qualifying. Hasil bersifat deskriptif, bukan penilaian pembalap.")

    try:
        if mode == "FastAPI":
            races = api_get(api_url, "/v1/races")
            session_id = races[0]["session_id"]
            laps = api_get(api_url, f"/v1/races/{session_id}/laps")
        else:
            laps = learning.telemetry.available_laps()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Gagal memuat daftar lap: {exc}")
        return

    labels = {
        lap["lap_id"]: f"{lap['driver']} lap {lap['lap_number']} — {lap['lap_time_s']:.3f}s"
        for lap in laps
    }
    options = list(labels)
    col_a, col_b = st.columns(2)
    with col_a:
        lap_a = st.selectbox("Lap A", options, index=0, format_func=lambda item: labels[item])
    with col_b:
        lap_b = st.selectbox("Lap B", options, index=1 if len(options) > 1 else 0, format_func=lambda item: labels[item])

    use_segment = st.checkbox("Batasi ke segmen jarak")
    segment_start = segment_end = None
    if use_segment:
        seg_a, seg_b = st.columns(2)
        segment_start = seg_a.number_input("Mulai (m)", min_value=0.0, value=300.0, step=50.0)
        segment_end = seg_b.number_input("Selesai (m)", min_value=1.0, value=600.0, step=50.0)
    question = st.text_input("Pertanyaan (opsional)", placeholder="Apa perbedaan fase pengereman?")

    if st.button("Analisis lap", type="primary", disabled=lap_a == lap_b):
        payload = {"lap_a_id": lap_a, "lap_b_id": lap_b, "question": question or None}
        if use_segment:
            payload["segment_start_m"] = float(segment_start)
            payload["segment_end_m"] = float(segment_end)
        try:
            st.session_state["telemetry_report"] = _run_telemetry_analysis(mode, api_url, learning, payload)
        except Exception as exc:  # noqa: BLE001
            st.session_state.pop("telemetry_report", None)
            st.error(f"Analisis gagal: {exc}")

    report = st.session_state.get("telemetry_report")
    if report:
        st.divider()
        render_telemetry_report(report, learning)


def render_answer(answer: dict) -> None:
    import pandas as pd

    status = answer.get("generation_status")
    if status == "unavailable":
        st.warning(
            "LLM tidak aktif. Jawaban ini disusun deterministik dari fakta terukur dan kutipan; "
            "ini bukan generasi bahasa oleh model."
        )
    elif status in ("rejected", "error"):
        st.error(f"Generasi ditolak atau gagal ({status}); fallback deterministik ditampilkan.")

    st.caption(f"Tipe pertanyaan: {answer.get('question_type')} · Level: {answer.get('level')}")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Fakta terukur")
        if answer.get("observed_facts"):
            for item in answer["observed_facts"]:
                st.markdown(f"- {item}")
        else:
            st.caption("Tidak ada fakta terukur.")
    with col_b:
        st.subheader("Temuan berbasis aturan")
        if answer.get("rule_based_findings"):
            for item in answer["rule_based_findings"]:
                st.markdown(f"- {item}")
        else:
            st.caption("Tidak ada temuan.")

    st.subheader("Materi teori")
    if answer.get("theory"):
        for item in answer["theory"]:
            with st.expander(item[:90] + ("..." if len(item) > 90 else "")):
                st.write(item)
    else:
        st.caption("Tidak ada materi teori yang diambil.")

    if answer.get("citation_refs"):
        st.subheader("Sitasi")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": item["ref_id"],
                        "Dokumen": item["document_id"],
                        "Bagian": item.get("article"),
                        "Terverifikasi": "ya" if item.get("verified") else "tidak",
                        "Dukungan semantik": "ya" if item.get("semantic_support_verified") else "belum diaudit",
                    }
                    for item in answer["citation_refs"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if answer.get("potential_explanations"):
        st.subheader("Faktor alternatif (bukan kausal)")
        for item in answer["potential_explanations"]:
            st.markdown(f"- {item}")

    with st.expander("Data yang kurang"):
        for item in answer.get("missing_data", []):
            st.markdown(f"- {item}")
    with st.expander("Keterbatasan"):
        for item in answer.get("limitations", []):
            st.markdown(f"- {item}")
    if answer.get("suggested_learning_questions"):
        st.subheader("Pertanyaan lanjutan")
        for item in answer["suggested_learning_questions"]:
            st.markdown(f"- {item}")

    st.download_button(
        "Unduh jawaban sebagai JSON",
        data=json.dumps(answer, indent=2, ensure_ascii=False),
        file_name="grounded_answer.json",
        mime="application/json",
    )


def render_engineering_tutor(ask_service: AskService, learning: TelemetryLearningService, mode: str, api_url: str) -> None:
    st.markdown('<div class="workbench-eyebrow">MEX-AI / ENGINEERING TUTOR</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="workbench-title">Engineering Tutor<span style="color:#7f8792">.</span></h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="workbench-lede">Tanya konsep teknik atau kaitkan pertanyaan dengan dua lap. '
        'Jawaban memisahkan fakta, interpretasi, sitasi, dan keterbatasan.</p><div class="workbench-rule"></div>',
        unsafe_allow_html=True,
    )

    level = st.radio("Level penjelasan", ["beginner", "engineering"], horizontal=True)
    use_laps = st.checkbox("Gunakan konteks dua lap")
    lap_a = lap_b = None
    if use_laps:
        laps = learning.telemetry.available_laps()
        labels = {lap["lap_id"]: f"{lap['driver']} lap {lap['lap_number']}" for lap in laps}
        col_a, col_b = st.columns(2)
        lap_a = col_a.selectbox("Lap A", list(labels), format_func=lambda item: labels[item])
        lap_b = col_b.selectbox("Lap B", list(labels), index=1, format_func=lambda item: labels[item])

    question = st.text_area(
        "Pertanyaan",
        placeholder="Mengapa titik pengereman bisa berbeda? Apa arti brake onset?",
        height=100,
    )
    if st.button("Tanya", type="primary", disabled=not question.strip()):
        payload = {"question": question, "level": level}
        if use_laps and lap_a and lap_b:
            payload["lap_a_id"] = lap_a
            payload["lap_b_id"] = lap_b
        try:
            st.session_state["ask_answer"] = _run_ask(mode, api_url, ask_service, payload)
        except Exception as exc:  # noqa: BLE001
            st.session_state.pop("ask_answer", None)
            st.error(f"Pertanyaan gagal: {exc}")

    if st.session_state.get("ask_answer"):
        st.divider()
        render_answer(st.session_state["ask_answer"])


def main() -> None:
    settings = load_settings()
    service = get_service()
    kb = service.kb

    default_api_mode = os.getenv("UI_BACKEND", "local").strip().lower() in ("api", "fastapi")
    default_api_url = os.getenv("API_URL", "http://127.0.0.1:8000")

    with st.sidebar:
        st.markdown('<div class="workbench-eyebrow">MEX-AI / WORKSPACE</div>', unsafe_allow_html=True)
        st.header("Kontrol sistem")
        module = st.radio("Modul", ["Race Analysis", "Engineering Tutor", "Regulation Lab"], index=2)
        st.caption(f"{kb.regulation} · Issue {kb.regulation_issue}")
        mode = st.radio("Backend", ["In-process", "FastAPI"], index=1 if default_api_mode else 0)
        api_url = st.text_input("API URL", value=default_api_url, disabled=mode == "In-process")
        if module == "Regulation Lab":
            st.divider()
            st.metric("Aturan ditinjau", len(kb.reviewed_rules()))
            st.metric("Aturan aktif", len(kb.active_rules()))
            st.metric(
                "Goal pemeriksaan",
                len([g for g in kb.goals() if any(r.conclusion.kind == "boolean" for r in kb.rules_for_goal(g))]),
            )
            st.caption("Ekstraksi teks: parser deterministik")
            if st.button("Muat contoh fakta", use_container_width=True):
                st.session_state["facts"] = load_sample_facts()
                update_fact_widgets(st.session_state["facts"])
                st.session_state["extraction_used"] = False
                st.toast("Contoh fakta dimuat ke formulir.")
            if st.button("Kosongkan fakta", use_container_width=True):
                st.session_state["facts"] = {}
                update_fact_widgets({})
                st.session_state["extraction_used"] = False
                st.session_state.pop("last_report", None)
                st.toast("Fakta dan hasil pemeriksaan dikosongkan.")
        else:
            st.divider()
            st.caption("Data: fixture publik 2025 Abu Dhabi Qualifying (VER lap 14, NOR lap 16).")

    if module == "Race Analysis":
        render_race_analysis(get_learning_service(), mode, api_url)
        return
    if module == "Engineering Tutor":
        render_engineering_tutor(get_ask_service(), get_learning_service(), mode, api_url)
        return

    st.markdown('<div class="workbench-eyebrow">F1 / REGULATION LAB / 2026</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="workbench-title">Regulation Lab<span style="color:#7f8792">.</span></h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="workbench-lede">Periksa ketentuan teknis Formula 1 dengan fakta terstruktur, '
        'jejak inferensi, dan bukti yang dapat ditelusuri ke regulasi.</p><div class="workbench-rule"></div>',
        unsafe_allow_html=True,
    )
    if kb.demo_mode:
        st.warning(
            "Mode demo: aturan berstatus `reviewed`, belum disetujui manusia. "
            "Hasil tidak boleh dianggap sebagai validasi FIA."
        )

    goals = [g for g in kb.goals() if any(rule.conclusion.kind == "boolean" for rule in kb.rules_for_goal(g))]
    goal_meta = {g: kb.rules_for_goal(g)[0] for g in goals}

    tab_check, tab_rag, tab_rules, tab_about = st.tabs(
        ["01  Pemeriksaan", "02  Cari bukti", "03  Aturan & sumber", "04  Tentang"]
    )

    with tab_check:
        st.markdown('<div class="section-kicker">01 / COMPLIANCE ENGINE</div>', unsafe_allow_html=True)
        st.subheader("Pemeriksaan kepatuhan")
        st.caption("Pilih ketentuan, masukkan data kendaraan, lalu jalankan inferensi berbasis aturan.")
        left, right = st.columns([1, 1.55], gap="large")
        with left:
            selected_goal = st.selectbox(
                "Tujuan pemeriksaan",
                goals,
                format_func=lambda g: f"{goal_meta[g].name} — {goal_meta[g].source.article}",
            )
            st.markdown(
                '<div class="source-block"><strong>Rujukan / '
                + escape(goal_meta[selected_goal].source.article)
                + '</strong>' + escape(goal_meta[selected_goal].source.quote) + '</div>',
                unsafe_allow_html=True,
            )
            st.caption("Kutipan regulasi untuk tujuan pemeriksaan yang dipilih.")
            requirements = service.requirements(selected_goal)

        with right:
            st.subheader("01 / Ekstraksi dari teks")
            text = st.text_area(
                "Tuliskan spesifikasi (Bahasa Indonesia atau Inggris)",
                placeholder="Contoh: wheelbase 3350 mm, massa mobil 805 kg, sesi qualifying, tanpa heat hazard",
                height=110,
            )
            if st.button("Ekstrak fakta dari teks", disabled=not text.strip()):
                extractor = get_extractor(settings)
                result = extractor.extract(text)
                extracted = {item.name: item.value for item in result.facts}
                st.session_state.setdefault("facts", {}).update(extracted)
                update_fact_widgets(st.session_state["facts"])
                st.session_state["extraction_notes"] = result.notes
                st.session_state["extraction_used"] = bool(result.facts)
                if result.facts:
                    st.success(f"{len(result.facts)} fakta diekstrak. Periksa kembali sebelum pemeriksaan.")
                    st.dataframe(
                        [
                            {
                                "Fakta": item.name,
                                "Nilai": item.value,
                                "Satuan": item.unit,
                                "Keyakinan": item.confidence,
                                "Bukti": item.evidence,
                            }
                            for item in result.facts
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.warning("Tidak ada fakta yang dapat diekstrak.")
                if result.rejected:
                    st.error(f"Fakta ditolak: {result.rejected}")
            for note in st.session_state.get("extraction_notes", []):
                st.caption(f"• {note}")

            st.subheader("02 / Spesifikasi teknis")
            defaults = st.session_state.get("facts", {})
            with st.form(key=f"check_form_{selected_goal}"):
                values = fact_input_widgets(selected_goal, requirements, defaults)
                confirm_extracted = True
                if st.session_state.get("extraction_used"):
                    confirm_extracted = st.checkbox(
                        "Saya sudah memeriksa fakta hasil ekstraksi",
                        key=f"confirm_extracted_{selected_goal}",
                    )
                submitted = st.form_submit_button("Periksa kepatuhan", type="primary", use_container_width=True)
            if submitted:
                if not confirm_extracted:
                    st.error("Konfirmasi dulu fakta hasil ekstraksi sebelum menjalankan pemeriksaan.")
                else:
                    merged = {name: value for name, value in defaults.items() if name not in values}
                    merged.update(normalize_values(values))
                    st.session_state["facts"] = merged
                    payload = {"goal_id": selected_goal, "facts": facts_to_payload(merged)}
                    try:
                        if mode == "FastAPI":
                            report = api_request(api_url, "/v1/check", payload)
                        else:
                            items = [
                                FactInput(name=item["name"], value=item["value"], unit=item.get("unit"))
                                for item in payload["facts"]
                            ]
                            store = service.build_fact_store(items)
                            report = service.check(selected_goal, store).model_dump(mode="json")
                        st.session_state["last_report"] = report
                    except Exception as exc:  # noqa: BLE001 - show error to the user
                        st.session_state.pop("last_report", None)
                        st.error(f"Pemeriksaan gagal: {exc}")

        if st.session_state.get("last_report"):
            st.divider()
            render_report(st.session_state["last_report"])

    with tab_rag:
        st.markdown('<div class="section-kicker">02 / DOCUMENT RETRIEVAL</div>', unsafe_allow_html=True)
        st.subheader("Ambil potongan regulasi yang relevan")
        query = st.text_input("Pertanyaan / kata kunci", value="maximum wheelbase 3400 mm")
        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            top_k = st.slider("Jumlah hasil", 1, 10, 5)
        with col_b:
            article_filter = st.text_input("Filter artikel (opsional)", value="")
        with col_c:
            st.caption("RAG hanya mengambil bukti. Keputusan kepatuhan tetap dibuat oleh mesin inferensi.")
        include_methodology = st.checkbox(
            "Sertakan jurnal metodologi (bukan sumber regulasi)",
            value=False,
        )
        if st.button("Cari di dokumen", type="primary", disabled=not query.strip()):
            try:
                if mode == "FastAPI":
                    hits = api_request(
                        api_url,
                        "/v1/search",
                        {
                            "query": query,
                            "top_k": top_k,
                            "article": article_filter or None,
                            "include_methodology": include_methodology,
                        },
                    )
                else:
                    hits = [
                        hit.model_dump()
                        for hit in get_retriever().search(
                            query,
                            top_k=top_k,
                            article=article_filter or None,
                            include_methodology=include_methodology,
                        )
                    ]
                st.session_state["search_hits"] = hits
            except Exception as exc:  # noqa: BLE001
                st.session_state.pop("search_hits", None)
                st.error(f"Retrieval gagal: {exc}")
        if "search_hits" in st.session_state:
            hits = st.session_state["search_hits"]
            if not hits:
                st.warning("Tidak ada hasil relevan.")
            else:
                st.caption(f"{len(hits)} potongan ditemukan · urut menurut relevansi")
            for rank, hit in enumerate(hits, start=1):
                with st.expander(
                    f"{rank:02d}  /  {hit['article'] or '-'}  /  halaman {hit['page']}  /  skor {hit['score']:.4f}"
                ):
                    st.write(hit["text"])
                    st.caption(
                        f"chunk: {hit['chunk_id']} · dokumen: {hit['document_id']} "
                        f"· tipe: {hit.get('document_type')}"
                    )

    with tab_rules:
        st.markdown('<div class="section-kicker">03 / RULE LIBRARY</div>', unsafe_allow_html=True)
        st.subheader("Aturan yang dapat dijalankan")
        st.caption(
            "Status `reviewed` berarti sumber sudah diperiksa otomatis, tetapi belum ada sign-off manusia. "
            "Aturan baru berstatus `active` setelah reviewer mengisi approval."
        )
        for rule in kb.runnable_rules():
            with st.expander(f"{rule.rule_id} — {rule.name} ({rule.status.value})"):
                st.markdown(
                    f"**Artikel:** {rule.source.article} (hlm. {rule.source.page}) · "
                    f"**Issue:** {rule.source.issue} · **Status:** {rule.status.value}"
                )
                st.info(rule.source.quote)
                st.markdown("**Kondisi:**")
                for condition in rule.conditions:
                    st.code(condition.render(), language="text")
                if rule.applies_if:
                    st.markdown("**Berlaku jika:**")
                    for condition in rule.applies_if:
                        st.code(condition.render(), language="text")
                if rule.validation:
                    st.json(rule.validation.model_dump())

    with tab_about:
        st.markdown('<div class="section-kicker">04 / SYSTEM NOTES</div>', unsafe_allow_html=True)
        st.subheader("Cakupan dan keterbatasan")
        st.markdown(
            "- Sistem memeriksa 5 ketentuan: C2.3.1, C2.3.3, C2.3.5, C4.1, dan C4.2 dari Section C Issue 21.\n"
            "- Status eksternal: SATISFIED, VIOLATED, INSUFFICIENT_DATA, NOT_APPLICABLE, UNSUPPORTED, ERROR.\n"
            "- Internal proof memakai TRUE/FALSE/UNKNOWN; UNKNOWN tidak pernah dianggap FALSE.\n"
            "- Semua aturan berstatus `reviewed` (demo-only) sampai ada sign-off manusia; belum ada aturan `active`.\n"
            "- RAG hanya mengambil bukti dan referensi halaman, bukan keputusan kepatuhan.\n"
            "- Jurnal metodologi dikecualikan dari pencarian kepatuhan secara default.\n"
            "- Nilai Nominal Tyre Mass tidak ditetapkan regulasi; nilainya harus diberikan sebagai fakta.\n"
            "- Hasil bukan pengganti pemeriksaan FIA technical delegate dan tidak mencakup seluruh Section C."
        )
        st.subheader("Alur")
        st.code(
            "Input fakta/teks -> (opsional) ekstraksi fakta -> Backward Chaining -> status + jejak + sitasi\n"
            "Pertanyaan RAG -> chunk Section C (artikel, halaman) -> bukti",
            language="text",
        )


if __name__ == "__main__":
    main()
