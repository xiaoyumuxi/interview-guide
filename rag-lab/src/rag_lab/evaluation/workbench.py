from __future__ import annotations

import copy
import json
import logging
import threading
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from rag_lab.common.config import load_config
from rag_lab.evaluation.runner import BenchmarkRunner

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExperimentRecord:
  key: str
  experiment_id: str
  experiment_name: str
  strategy: str
  timestamp: str
  dataset_version: str
  embedding_model: str
  generation_model: str
  prompt: dict[str, Any]
  metrics: dict[str, float]
  raw_path: str

  def to_dict(self) -> dict[str, Any]:
    return {
      "key": self.key,
      "experiment_id": self.experiment_id,
      "experiment_name": self.experiment_name,
      "strategy": self.strategy,
      "timestamp": self.timestamp,
      "dataset_version": self.dataset_version,
      "embedding_model": self.embedding_model,
      "generation_model": self.generation_model,
      "prompt": self.prompt,
      "metrics": self.metrics,
      "raw_path": self.raw_path,
    }


def load_experiment_records(results_dir: Path) -> list[ExperimentRecord]:
  records: list[ExperimentRecord] = []
  for path in sorted(results_dir.glob("*.json"), reverse=True):
    try:
      report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
      LOGGER.warning("Skipping invalid report %s: %s", path, exc)
      continue
    experiment_id = str(report.get("experiment_id") or path.stem)
    experiment_name = str(report.get("config", {}).get("experiment", {}).get("name", ""))
    timestamp = str(report.get("timestamp", ""))
    dataset_version = str(report.get("dataset_version", ""))
    embedding_model = str(report.get("embedding_model", ""))
    for strategy, result in report.get("strategies", {}).items():
      retrieval_metrics = _numeric_metrics(result.get("metrics", {}).get("Overall", {}))
      generation = result.get("generation", {})
      generation_metrics = _numeric_metrics(generation.get("metrics", {}).get("Overall", {}))
      prompt = generation.get("prompt", {}) if isinstance(generation.get("prompt", {}), dict) else {}
      provider = generation.get("provider", {}) if isinstance(generation.get("provider", {}), dict) else {}
      metrics = {**retrieval_metrics, **generation_metrics}
      metrics.update(_cost_metrics(result))
      records.append(ExperimentRecord(
        key=f"{experiment_id}:{strategy}",
        experiment_id=experiment_id,
        experiment_name=experiment_name,
        strategy=str(strategy),
        timestamp=timestamp,
        dataset_version=dataset_version,
        embedding_model=embedding_model,
        generation_model=str(provider.get("model", "")),
        prompt=prompt,
        metrics=metrics,
        raw_path=str(path),
      ))
  return records


def compare_records(base: ExperimentRecord, candidate: ExperimentRecord) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for metric in sorted(set(base.metrics) | set(candidate.metrics)):
    base_value = base.metrics.get(metric)
    candidate_value = candidate.metrics.get(metric)
    delta = None if base_value is None or candidate_value is None else candidate_value - base_value
    delta_pct = None
    if delta is not None and base_value not in (None, 0.0):
      delta_pct = delta / abs(base_value) * 100
    rows.append({
      "metric": metric,
      "base": base_value,
      "candidate": candidate_value,
      "delta": delta,
      "delta_pct": delta_pct,
      "direction": _metric_direction(metric),
    })
  return rows


def run_workbench(
  *,
  project_root: Path,
  config_path: Path | None,
  host: str = "127.0.0.1",
  port: int = 8787,
  open_browser: bool = True,
) -> None:
  state = WorkbenchState(project_root=project_root, config_path=config_path)

  class Handler(WorkbenchRequestHandler):
    workbench_state = state

  server = ThreadingHTTPServer((host, port), Handler)
  url = f"http://{host}:{port}"
  LOGGER.info("RAG Lab Workbench listening on %s", url)
  if open_browser:
    threading.Timer(0.25, lambda: webbrowser.open(url)).start()
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    LOGGER.info("Stopping workbench")
  finally:
    server.server_close()


class WorkbenchState:
  def __init__(self, *, project_root: Path, config_path: Path | None) -> None:
    self.root = project_root
    self.config_path = config_path
    self.run_lock = threading.Lock()

  def records(self) -> list[ExperimentRecord]:
    return load_experiment_records(self.root / "results/raw")

  def settings(self) -> dict[str, Any]:
    if self.config_path is None:
      return {
        "can_run": False,
        "message": "Launch with --config to enable prompt experiments.",
        "prompt": {},
        "strategies": [],
      }
    config = load_config(self.config_path)
    generation = config.get("generation", {})
    return {
      "can_run": bool(generation.get("provider")),
      "message": "" if generation.get("provider") else "Config has no generation.provider.",
      "config_path": str(self.config_path),
      "experiment_name": config.get("experiment", {}).get("name", ""),
      "prompt": generation.get("prompt", {}),
      "strategies": config.get("chunking", {}).get("strategies", []),
      "generation_model": generation.get("provider", {}).get("model", ""),
      "judge_enabled": bool(generation.get("judge", {}).get("enabled", False)),
    }

  def run_prompt_experiment(self, payload: dict[str, Any]) -> dict[str, Any]:
    if self.config_path is None:
      raise ValueError("Workbench was launched without --config")
    if not self.run_lock.acquire(blocking=False):
      raise RuntimeError("Another experiment is already running")
    try:
      config = copy.deepcopy(load_config(self.config_path))
      generation = config.setdefault("generation", {})
      if not generation.get("provider"):
        raise ValueError("Configured experiment has no generation.provider")
      generation["enabled"] = True
      prompt = generation.setdefault("prompt", {})
      prompt["id"] = str(payload.get("prompt_id") or prompt.get("id") or "workbench")
      prompt["version"] = str(payload.get("prompt_version") or prompt.get("version") or "draft")
      prompt["system"] = str(payload.get("system_prompt") or prompt.get("system") or "")
      prompt["template"] = str(payload.get("template") or prompt.get("template") or "")
      if "{question}" not in prompt["template"] or "{context}" not in prompt["template"]:
        raise ValueError("Prompt template must contain {question} and {context}")
      name = str(payload.get("experiment_name") or "workbench-prompt-experiment").strip()
      config.setdefault("experiment", {})["name"] = name
      strategy = str(payload.get("strategy") or "").strip()
      if strategy:
        available = config.get("chunking", {}).get("strategies", [])
        if strategy not in available:
          raise ValueError(f"Unknown strategy: {strategy}")
        config["chunking"]["strategies"] = [strategy]
      report = BenchmarkRunner(config, self.root).run()
      return {"experiment_id": report["experiment_id"], "strategies": list(report["strategies"])}
    finally:
      self.run_lock.release()


class WorkbenchRequestHandler(BaseHTTPRequestHandler):
  workbench_state: WorkbenchState

  def do_GET(self) -> None:  # noqa: N802
    path = urlparse(self.path).path
    if path == "/":
      self._html(WORKBENCH_HTML)
      return
    if path == "/api/experiments":
      self._json({"experiments": [record.to_dict() for record in self.workbench_state.records()]})
      return
    if path == "/api/settings":
      try:
        self._json(self.workbench_state.settings())
      except Exception as exc:  # noqa: BLE001
        self._json({"error": str(exc)}, status=500)
      return
    self._json({"error": "not found"}, status=404)

  def do_POST(self) -> None:  # noqa: N802
    path = urlparse(self.path).path
    if path != "/api/run":
      self._json({"error": "not found"}, status=404)
      return
    try:
      length = int(self.headers.get("Content-Length", "0"))
      payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
      result = self.workbench_state.run_prompt_experiment(payload)
      self._json(result)
    except ValueError as exc:
      self._json({"error": str(exc)}, status=400)
    except RuntimeError as exc:
      self._json({"error": str(exc)}, status=409)
    except Exception as exc:  # noqa: BLE001
      LOGGER.exception("Workbench experiment failed")
      self._json({"error": str(exc)}, status=500)

  def log_message(self, format: str, *args: Any) -> None:
    LOGGER.debug(format, *args)

  def _json(self, payload: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "application/json; charset=utf-8")
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)

  def _html(self, html: str) -> None:
    body = html.encode("utf-8")
    self.send_response(200)
    self.send_header("Content-Type", "text/html; charset=utf-8")
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)


def _numeric_metrics(values: dict[str, Any]) -> dict[str, float]:
  output: dict[str, float] = {}
  for key, value in values.items():
    if isinstance(value, bool):
      output[str(key)] = float(value)
    elif isinstance(value, (int, float)):
      output[str(key)] = float(value)
  return output


def _cost_metrics(result: dict[str, Any]) -> dict[str, float]:
  fields = (
    "chunk_count", "index_size_estimate_bytes", "embedding_seconds", "retrieval_seconds",
    "p50_retrieval_latency_ms", "p95_retrieval_latency_ms",
  )
  return {
    field: float(result[field])
    for field in fields
    if isinstance(result.get(field), (int, float))
  }


def _metric_direction(metric: str) -> str:
  lowered = metric.lower()
  if any(token in lowered for token in ("waste", "latency", "seconds", "negativeexposure", "index_size")):
    return "lower"
  return "higher"


WORKBENCH_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RAG Lab Evaluation Workbench</title>
<style>
:root{color-scheme:light dark;--bg:#0b0d10;--panel:#14181d;--panel2:#1b2027;--text:#edf2f7;--muted:#98a2b3;--line:#2a313a;--accent:#7dd3fc;--good:#86efac;--bad:#fca5a5;--warn:#fde68a}*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text)}main{max-width:1440px;margin:0 auto;padding:28px}h1{font-size:24px;margin:0 0 6px}h2{font-size:16px;margin:0 0 14px}.sub{color:var(--muted);margin:0 0 24px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:16px}.controls{display:grid;grid-template-columns:1fr 1fr auto;gap:12px;align-items:end}.field{display:flex;flex-direction:column;gap:6px}.field label{font-size:12px;color:var(--muted)}select,input,textarea,button{font:inherit;border-radius:9px;border:1px solid var(--line);background:var(--panel2);color:var(--text);padding:10px 12px}textarea{min-height:170px;resize:vertical;line-height:1.45}button{cursor:pointer;background:#e7f6fd;color:#07131a;font-weight:700}button:disabled{cursor:not-allowed;opacity:.45}.meta{display:flex;gap:14px;flex-wrap:wrap;color:var(--muted);font-size:12px;margin-top:10px}.metric-table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}.metric-table th,.metric-table td{text-align:right;border-bottom:1px solid var(--line);padding:9px 8px;font-size:13px}.metric-table th:first-child,.metric-table td:first-child{text-align:left;max-width:360px;word-break:break-word}.delta.good{color:var(--good)}.delta.bad{color:var(--bad)}.delta.neutral{color:var(--muted)}pre{white-space:pre-wrap;word-break:break-word;background:var(--panel2);border:1px solid var(--line);padding:12px;border-radius:10px;min-height:120px;margin:8px 0 0;font-size:12px}.prompt-head{display:flex;justify-content:space-between;gap:8px;color:var(--muted);font-size:12px}.run-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.run-actions{display:flex;gap:10px;align-items:center;margin-top:12px}.status{font-size:13px;color:var(--muted)}.status.error{color:var(--bad)}.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 8px;font-size:11px;color:var(--muted)}@media(max-width:900px){main{padding:16px}.grid,.controls,.run-grid{grid-template-columns:1fr}.controls{align-items:stretch}}
</style>
</head>
<body><main>
<h1>RAG Lab Evaluation Workbench</h1>
<p class="sub">对比历史实验，定位 Prompt / Chunk / 模型变化对检索质量、回答质量与耗时的影响。</p>
<section class="panel">
  <h2>实验 A/B</h2>
  <div class="controls">
    <div class="field"><label for="base">基线</label><select id="base"></select></div>
    <div class="field"><label for="candidate">候选</label><select id="candidate"></select></div>
    <button id="refresh" type="button">刷新记录</button>
  </div>
  <div id="meta" class="meta"></div>
</section>
<div class="grid">
  <section class="panel"><h2>指标变化</h2><div style="overflow:auto"><table class="metric-table"><thead><tr><th>Metric</th><th>Base</th><th>Candidate</th><th>Δ</th><th>Δ%</th></tr></thead><tbody id="metrics"></tbody></table></div></section>
  <section class="panel"><h2>Prompt Diff</h2><div class="grid"><div><div class="prompt-head"><span>Base</span><span id="basePromptMeta"></span></div><pre id="basePrompt">暂无 Prompt 记录</pre></div><div><div class="prompt-head"><span>Candidate</span><span id="candidatePromptMeta"></span></div><pre id="candidatePrompt">暂无 Prompt 记录</pre></div></div></section>
</div>
<section class="panel">
  <h2>Prompt 实验</h2>
  <div id="runHint" class="status">正在读取配置…</div>
  <div class="controls" style="margin-top:12px">
    <div class="field"><label for="experimentName">实验名称</label><input id="experimentName" value="workbench-prompt-experiment"></div>
    <div class="field"><label for="strategy">Chunk Strategy</label><select id="strategy"></select></div>
    <div class="field"><label for="promptVersion">Prompt Version</label><input id="promptVersion" value="draft-v1"></div>
  </div>
  <div class="run-grid" style="margin-top:12px">
    <div class="field"><label for="systemPrompt">System Prompt</label><textarea id="systemPrompt"></textarea></div>
    <div class="field"><label for="template">User Template（必须包含 {question} / {context}）</label><textarea id="template"></textarea></div>
  </div>
  <div class="run-actions"><button id="run" type="button" disabled>运行 Dev 实验</button><span id="runStatus" class="status"></span></div>
</section>
</main>
<script>
const $=id=>document.getElementById(id);let experiments=[];let settings={};
const fmt=v=>v===null||v===undefined?'—':Math.abs(v)>=1000?v.toFixed(1):Math.abs(v)>=1?v.toFixed(4):v.toFixed(6);
function label(e){return `${e.experiment_id} · ${e.strategy}${e.prompt?.version?' · '+e.prompt.version:''}`}
function selected(id){return experiments.find(e=>e.key===$(id).value)}
function promptText(e){if(!e?.prompt)return '';const p=e.prompt;return `${p.system||''}\n\n--- USER TEMPLATE ---\n${p.template||''}`.trim()}
function render(){const a=selected('base'),b=selected('candidate');if(!a||!b)return;const keys=[...new Set([...Object.keys(a.metrics),...Object.keys(b.metrics)])].sort();$('metrics').innerHTML='';for(const key of keys){const av=a.metrics[key],bv=b.metrics[key],delta=av==null||bv==null?null:bv-av;const dir=(/waste|latency|seconds|negativeexposure|index_size/i.test(key))?'lower':'higher';let cls='neutral';if(delta!==null&&Math.abs(delta)>1e-12)cls=((delta>0)===(dir==='higher'))?'good':'bad';const pct=delta!==null&&av?delta/Math.abs(av)*100:null;const tr=document.createElement('tr');tr.innerHTML=`<td>${key}</td><td>${fmt(av)}</td><td>${fmt(bv)}</td><td class="delta ${cls}">${delta===null?'—':(delta>=0?'+':'')+fmt(delta)}</td><td class="delta ${cls}">${pct===null?'—':(pct>=0?'+':'')+pct.toFixed(2)+'%'}</td>`;$('metrics').appendChild(tr)}$('meta').innerHTML=`<span class="pill">Base ${a.dataset_version}</span><span class="pill">Candidate ${b.dataset_version}</span><span>Embedding: ${b.embedding_model||'—'}</span><span>Generation: ${b.generation_model||'—'}</span>`;$('basePrompt').textContent=promptText(a)||'暂无 Prompt 记录';$('candidatePrompt').textContent=promptText(b)||'暂无 Prompt 记录';$('basePromptMeta').textContent=a.prompt?.sha256?`${a.prompt.id||''}/${a.prompt.version||''} · ${a.prompt.sha256.slice(0,10)}`:'';$('candidatePromptMeta').textContent=b.prompt?.sha256?`${b.prompt.id||''}/${b.prompt.version||''} · ${b.prompt.sha256.slice(0,10)}`:''}
async function load(){const r=await fetch('/api/experiments');experiments=(await r.json()).experiments||[];for(const id of ['base','candidate']){$(id).innerHTML='';experiments.forEach(e=>{const o=document.createElement('option');o.value=e.key;o.textContent=label(e);$(id).appendChild(o)})}if(experiments.length>1){$('candidate').selectedIndex=0;$('base').selectedIndex=1}render()}
async function loadSettings(){const r=await fetch('/api/settings');settings=await r.json();if(settings.error){$('runHint').textContent=settings.error;$('runHint').classList.add('error');return}$('runHint').textContent=settings.can_run?`使用 ${settings.generation_model||'configured model'}；当前 Judge ${settings.judge_enabled?'开启':'关闭'}。实验仍受 Test execution guard 保护。`:settings.message;$('run').disabled=!settings.can_run;$('systemPrompt').value=settings.prompt?.system||'';$('template').value=settings.prompt?.template||'';$('strategy').innerHTML='';(settings.strategies||[]).forEach(s=>{const o=document.createElement('option');o.value=s;o.textContent=s;$('strategy').appendChild(o)})}
$('base').addEventListener('change',render);$('candidate').addEventListener('change',render);$('refresh').addEventListener('click',load);$('run').addEventListener('click',async()=>{$('run').disabled=true;$('runStatus').textContent='实验执行中…';$('runStatus').classList.remove('error');try{const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({experiment_name:$('experimentName').value,strategy:$('strategy').value,prompt_version:$('promptVersion').value,prompt_id:'workbench',system_prompt:$('systemPrompt').value,template:$('template').value})});const data=await r.json();if(!r.ok)throw new Error(data.error||'run failed');$('runStatus').textContent=`完成：${data.experiment_id}`;await load();const match=experiments.find(e=>e.experiment_id===data.experiment_id);if(match){$('candidate').value=match.key;render()}}catch(e){$('runStatus').textContent=e.message;$('runStatus').classList.add('error')}finally{$('run').disabled=!settings.can_run}});load();loadSettings();
</script></body></html>'''
