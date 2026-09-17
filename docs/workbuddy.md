# 在 WorkBuddy 中安装人生库

适用版本：人生库 v0.1.0-beta.2。文档核验日期：2026-09-18。

## 下载与导入

**[下载 WorkBuddy 专用 ZIP](https://github.com/somnus-J-307/life-library/releases/download/v0.1.0-beta.2/life-library-workbuddy.zip)**

1. 下载上面的 `life-library-workbuddy.zip`，不要选择源码 ZIP、通用安装包或 `.skill` 文件。
2. 打开 WorkBuddy 的「技能 / Skills」页面，选择「添加技能 → 上传技能」，选中该 ZIP。部分界面将技能入口收在「专家 · Skills · Connectors」中。
3. 按 WorkBuddy 实际导入流程检查来源与权限，完成后确认人生库处于启用状态。
4. 新建任务，选一个独立的个人资料文件夹，在对话中说：

   ```text
   使用人生库。资料保存在当前个人文件夹下的 life-library-data，
   不放进 Skill 安装目录，也不上传分享。
   先记一条：今天完成了一个课程实验，我负责数据处理，报告还没整理。
   ```

示例句子请替换为自己的真实经历。之后可以说「补证据」「看看当前简历」「结合我的专业看看下一步」。不需要运行 Codex 安装器，也不需要先装 asu。

WorkBuddy 的本地技能上传入口见[官方技能使用说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。开放平台另列出了技能元数据与资源结构，见[官方 Skill 开发规范](https://open.workbuddy.cn/en/docs/skill)。本包补齐了该规范中的中英文描述、版本和作者字段；ZIP 顶层直接包含 `SKILL.md` 及它依赖的资源，避免导入整仓库多余的目录层级。

## 运行条件与验收边界

- Python 3.10+，仅标准库。导入 ZIP 本身不要求手动运行 Python；归档、校验和生成页面时，WorkBuddy 需要能调用可用的 Python 运行环境。若环境缺失，先按助手诊断配置，不需要为本项目安装 pip 包。
- 支持本地文件读写和执行脚本的 WorkBuddy 桌面任务。不要默认移动端或仅聊天模式能执行相同流程。
- 已通过自动化检查：元数据必需字段、包内文件与源码对应、UTF-8 内容、解压后初始化、记录校验、页面生成、证据归档、版本留档及隐私规则。
- **尚未完成 WorkBuddy 桌面端导入与真实对话实测。** 官方格式适配和脚本通过不等于宿主端端到端验收，也不代表已上架官方技能市场。若有问题，请附客户端版本和脱敏错误信息到仓库 Issues。

只给任务所需的文件权限；不要为了导入 Skill 开放整个磁盘。数据目录、总览 HTML 和留档附件含个人内容，分享简历时单独选择核对过的简历文件。

## 下载信息接口

项目提供一个公开、无认证的静态 JSON 入口，供下载页面或安装辅助工具读取：

[downloads/workbuddy.json（原始 JSON）](https://raw.githubusercontent.com/somnus-J-307/life-library/main/downloads/workbuddy.json)

主要字段：`version`、`download_url`、`sha256`、`size_bytes`、`install_method`、`validation`。返回的是人生库发布信息，不是 WorkBuddy 官方 API；不会自动安装、申请权限或收集数据。

下载后可将 ZIP 的 SHA-256 与 JSON 中的值或 Release 的 `SHA256SUMS.txt` 对照。链接使用明确版本，旧版本不会被静默覆盖。国内网络如果无法访问 GitHub，可由可信渠道转发同一个 ZIP，并比对校验值；目前没有国内镜像，也不承诺国内下载加速。

## 常见问题

**导入后找不到人生库？** 检查是否启用；用名称「人生库」或标识 `life-library` 搜索，并重新开始任务。保留客户端版本和错误提示，勿用反复复制目录替代诊断。

**提示已经存在？** 使用 WorkBuddy 自身提供的更新或卸载后重装流程，先确认个人资料在独立目录。不要删除人生库数据目录来解决 Skill 重名。

**页面没有自动变化？** 页面是生成的本地视图。让助手更新数据后执行 render，再刷新预览。

**安装就能找到当前校招 HC 吗？** 不会。需要提供岗位资料，或明确要求助手联网核验官方招聘信息；没有真实来源就保留未知。
