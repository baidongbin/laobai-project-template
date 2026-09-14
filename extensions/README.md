# 按需扩展模板

这些文件不是要一次性复制进项目的完整目录。只有内容真实需要独立维护时才取用；默认不增加无用空文件。

文件使用 `.md.template` 后缀，避免与已经生效的项目文档混淆。复制时按下表落位、去掉 `.template` 后缀并重命名。模板正文中的相对链接按**目标位置**书写，直接在模板库中阅读时不保证跳转；交付检查已按目标位置进行。

## 目标路径

| 模板 | 复制后的项目路径 | 适用时机 |
|---|---|---|
| [roadmap](roadmap.md.template) | `docs/roadmap.md` | 当前状态、下一步与路线规划需要独立维护 |
| [spec](spec.md.template) | `docs/specs/<capability>.md` | 一项能力的规则需要独立维护 |
| [单文件任务](plan.md.template) | `docs/plans/active/<task>.md` | 需要跨会话执行与交接 |
| [任务目录主记录](plan/README.md.template) | `docs/plans/active/<task>/README.md` | 一份任务记录不足以容纳必要材料 |
| [任务局部设计](plan/design.md.template) | `docs/plans/active/<task>/design.md` | 该任务确有需要独立阅读的设计 |
| [任务验证记录](plan/verification.md.template) | `docs/plans/active/<task>/verification.md` | 证据较多；从主记录移动而非复制 |
| [版本入口](version/README.md.template) | `docs/versions/<version>/README.md` | 需要独立版本范围与交付记录 |
| [版本目标设计](version/design.md.template) | `docs/versions/<version>/design.md` | 本版本存在明显架构演进 |
| [发布架构快照](version/architecture-snapshot.md.template) | `docs/versions/<version>/architecture-snapshot.md` | 必须在当前工作区直接阅读历史架构 |
| [重要决策](decision.md.template) | `docs/decisions/<id>-<decision>.md` | 重要取舍需要跨任务追溯 |
| [部署说明](deployment.md.template) | `docs/deployment.md` | 有实际部署与回退流程 |
| [外部参考](reference.md.template) | `docs/references/<reference>.md` | 需要随项目保留的参考摘要与证据 |

大型项目同样从 Lite 或 Standard 开始，按需选择以下扩展；路径是示例，不要求建立 packages 或改变源码布局。

| 模板 | 示例目标路径 | 适用时机 |
|---|---|---|
| [模块级 AGENTS](large/module-AGENTS.md.template) | `packages/<module>/AGENTS.md` | 模块存在需要独立加载的特殊规则 |
| [领域架构](large/domain-architecture.md.template) | `docs/architecture/<domain>.md` | 领域详情需要独立阅读维护 |
| [环境与隔离](large/environment.md.template) | `docs/development/environment.md` | 多服务或并行环境说明需要独立维护 |

跨模块计划直接使用上面的单文件或目录式任务模板，填写其中“跨模块协作”章节，不创建第三种任务状态。扩展中的链接按示例深度书写，实际位置变化须重算路径。环境内容较少时合并进现有开发说明即可。选择及验收见 [大型项目指南](../guides/large-projects.md)。

任务设计、验证附件依赖同目录任务主记录；版本设计、快照依赖同目录版本入口。其他模板可以独立加入任一预设。

## 额外占位符

| 占位符 | 如何填写 |
|---|---|
| `{{TASK_ID}}` | 如 `001`；front matter 自动带 `PLAN-` 前缀，不再重复填写前缀 |
| `{{TASK_TITLE}}` | 本次改动名称，不是整个产品名称 |
| `{{CAPABILITY_ID}}` | 如 `IMPORT`，用于稳定文档与需求条款编号 |
| `{{CAPABILITY_NAME}}` | 能力名称 |
| `{{VERSION}}` | 项目实际版本标识，如 `v1.0`；不强制版本策略 |
| `{{BASELINE_REF}}` | 目标设计固定出发点的实际 tag 或完整提交标识 |
| `{{RELEASE_REF}}` | 发布快照对应的实际发布 tag 或提交标识 |
| `{{DECISION_ID}}` | 如 `001`；模板自动带 `ADR-` 前缀 |
| `{{DECISION_TITLE}}` | 决策主题 |
| `{{REFERENCE_TITLE}}` | 参考资料主题 |
| `{{MODULE_NAME}}` | 实际模块名称；不表示必须建立同名目录 |
| `{{DOMAIN_NAME}}` | 领域名称 |

`{{NAME}}` 只用于指南中的占位符语法示意，不要求真实项目定义名为 NAME 的变量。没有全局自动渲染器或全局 ID 分配器；创建前先核对项目已有编号。

## 关联方式

复制并填写后，必要时把模板中的宽泛“产品说明”替换为直接的规格与条款号，把“工程入口”替换为真实开发／测试文档的相应章节。

- Lite 的验证可直接链接项目根 README 的 `#verification`。
- Standard 的验证可直接链接 `docs/testing.md`。
- 相对路径从当前文件计算；不加入个人绝对路径。
- 可选文档尚未创建时，不加失效链接。创建后才在任务、版本或文档导航中登记相关入口。
- 新增版本不会自动创建架构快照；历史默认使用真实发布 tag 回溯。

## 任务结束与结构升级

开始执行前确认范围与授权；确认后的计划设为 `doc_status: active`，任务状态按实际情况维护。任务完成或取消后，从 `active/` 迁入同级 `archive/`，将主记录的文档状态改为 `archived`，保留 `done` 或 `cancelled`。有附件时一并归档附件并更新其文档状态；不保留第二份活动副本。

`active/` 与 `archive/` 深度一致，同层迁移通常不改变指向项目根文档的相对路径，但所有指向任务旧位置的入链都需要检查和修复。

单文件任务升级成目录式任务时，以原内容作为新的 README，保持同一任务 ID。不要再套一份空白主记录；指向外部文档的相对路径通常增加一层 `../`，所有入链也要更新。移动或删除旧文件前遵守项目已有授权与备份规则。

## 状态边界

状态定义与两档底座相同：文档是否有效、任务是否完成、版本是否发布和实际验证结果分开维护。只在正文被确认符合真实用途后把 `draft` 改为 `active`；草稿中的候选目标不是实施授权。

本目录不提供自动安装器，也不依赖任意个人 Skills 仓库。
