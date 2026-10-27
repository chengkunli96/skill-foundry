# Skill Foundry

**Practical agent skills, forged through real projects.**

在真实项目中打磨出来的实用 Agent Skills。将反复确认有效的工作方式沉淀成可复用技能，通过 Git 维护，并按真实使用反馈持续更新。

## 当前技能

| Skill | 用途 | 调用 |
|---|---|---|
| [codebase-explainer](skills/codebase-explainer/SKILL.md) | 用主要功能和真实案例解释仓库，展示输入输出、数据流、可视化与文件变化 | `$codebase-explainer` |

## 目录

```text
skills/<skill-name>/
├── SKILL.md              指令与触发描述
├── agents/openai.yaml    可选的界面元数据
└── references/           按需读取的参考资料
scripts/check.py         校验 skills 与本地引用
scripts/install.py       安全创建调用软链接
tests/                   安装行为测试
.githooks/pre-commit     提交前运行校验与测试
```

## 安装与调用

```bash
git clone https://github.com/chengkunli96/skill-foundry.git
cd skill-foundry
python3 scripts/install.py --dry-run
python3 scripts/install.py
```

默认安装到用户级目录 `~/.agents/skills`，入口是指向仓库源文件的软链接。调用示例：

```text
使用 $codebase-explainer 帮我理解这个仓库：先讲用途和主要功能，再用真实案例展示输入输出。
```

若你的现有环境使用 `~/.codex/skills`，显式选择该目录：

```bash
python3 scripts/install.py codebase-explainer --target ~/.codex/skills
```

只选一个实际使用的发现目录，避免同名 skill 重复显示。Codex 支持 skill 目录软链接，检测到变更后可使用更新内容；若列表未刷新，重启应用。[官方说明](https://learn.chatgpt.com/docs/build-skills)

安装脚本遇到已有同名文件、不同目标的链接或内容不同的目录时会停止。若要将一份内容完全相同的目录迁移为软链接，可显式使用：

```bash
python3 scripts/install.py codebase-explainer --target ~/.codex/skills --adopt-identical
```

这会先将原目录移动到目标目录旁的 `skill-backups/skill-foundry/`，再建立链接。已有正确链接的重复安装不会改动文件。移动仓库位置后，需要检查并修复链接目标。

## 更新

使用仓库最新版本时运行 `git pull --ff-only`；软链接会读取更新后的源文件。自行维护 skill 时，直接修改 `skills/<skill-name>/`，无需重新复制。新增 skill 后重新运行安装脚本。

## 添加和维护 skill

1. 在 `skills/` 下新建同名目录，编写含 `name`、`description` 的 `SKILL.md`。
2. 将需要按需读取的资料放入 `references/`，确有需要再增加脚本或素材。
3. 校验后通过安装脚本链接到本机使用的目录。
4. 根据实际使用反馈修改源文件，检查差异后提交 Git。

```bash
python3 -m pip install -r requirements-dev.txt
make check
git diff
git add skills/ README.md
git commit -m "Refine codebase explanation workflow"
```

克隆后运行 `git config core.hooksPath .githooks`，可让后续提交自动执行 `make check`。自动检查覆盖格式、引用和安装行为，技能内容是否清楚、有用仍需通过真实任务验证。

本仓库只收录明确维护的个人技能。密钥、密码、环境文件、会话日志和真实业务数据保留在仓库外。

## License

[MIT](LICENSE) © 2026 Chengkun Li
