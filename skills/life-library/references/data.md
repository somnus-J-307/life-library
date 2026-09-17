# 数据与操作

库目录中 `library.json` 是事实来源，`evidence/` 保存复制的附件，`index.html` 为重新生成的私密本地总览，`resume.md` 只含允许用于简历的草稿，`snapshots/` 保存冻结版本。整个目录可复制备份，换机器只需 Python 3。不要将整个目录公开。

`init` 生成空库。由助手读取 JSON 后在本地编辑；不要用下例虚构数据填充用户真实库。顶层格式：

```json
{
  "schema_version": 1,
  "profile": {"name": "", "major": "", "entry_year": null, "graduation_year": null, "interests": [], "intention": "尚未确定"},
  "records": [], "jobs": [], "actions": [],
  "resume": {"direction": "", "summary": "", "bullets": []}
}
```

记录格式（ID 用 UUID；以下仅为字段示例）：

```json
{
  "id": "record-uuid", "title": "用户给出的经历标题", "kind": "奖项",
  "occurred": "2025", "recorded_at": "2026-09-18T12:00:00+08:00",
  "raw": "原话", "usage": "private", "tags": [],
  "facts": [{"id": "fact-uuid", "text": "整理出的事实", "status": "reported", "evidence_ids": []}],
  "pending": ["证书待补"], "evidence": [], "corrections": []
}
```

时间可为 YYYY、YYYY-MM、YYYY-MM-DD 或 null。`corrections` 追加 `{at, reason, previous}` 留下更正说明；不要改写 raw。证据项由 attach 生成 `{id, path, sha256, original_name, added_at}`。网络来源可以追加 `{id, url, accessed_at, type}`，只允许 https/http。

岗位项：`{id, title, company, source_url, captured_at, verified_at, status, graduation_requirement, education_requirement, hc, requirements: []}`。hc 仅填来源明确公布的人数，否则 null；状态原文保留。历史条目不覆盖，用新 ID 追加快照。

行动项：`{title, basis, gap, task, effort, deliverable, acceptance, status}`。basis 写来源岗位 ID 或「探索假设」；effort 明确是估算。

简历条目：`{text, fact_ids: []}`。每条至少引用一个允许用于简历且状态不为 uncertain 的事实；summary 也只写有证据支持的概括，不含额外事实、数字或头衔。

```text
python scripts/library.py attach --root <库目录> --record <记录ID> --file <原文件>
python scripts/library.py check --root <库目录>
python scripts/library.py render --root <库目录>
python scripts/library.py snapshot --root <库目录> --label <公司-岗位-版本>
```

snapshot 创建唯一目录，保存 resume.md、仅涉及当前简历的来源 JSON 和所引用附件，不覆盖旧版本，也不代表已提交申请。页面不使用网络服务或 localStorage；页面筛选不会修改原始数据，编辑数据后需 render。私密原话仅在本地总览显示；公开分享仅选简历产物。
