# repo-checkup

> 实验项目，不维护。目的是亲手走一遍「AI 原生、但由人把控」的 GitHub 开发全流程。

命令行工具：给本地 Git 仓库做「工程规范体检」，逐项给出 通过/警告/失败 和一句建议，最后给出总分。

## 项目结构

```
src/repo_checkup/
  cli.py          命令行参数、输出格式、退出码
  core.py         插件接口：Status / Result / Check / Context
  registry.py     自动发现 checks/ 下的检查项
  report.py       运行检查、计算总分、渲染 text / json
  checks/         每个检查项一个文件，自动注册
tests/
  conftest.py     隔离本机 git 配置；make_repo / git 夹具
  checks/         每个检查项一个测试文件
.github/          CI 工作流、PR 模板
.claude/settings.json   项目级权限（allow / ask / deny）
```

## 常用命令

```bash
uv sync                      # 安装依赖（含开发依赖）
uv run ruff format .         # 格式化
uv run ruff check .          # 静态检查
uv run pytest                # 测试
uv run repo-checkup [路径]    # 运行；另有 --format json、--list
```

## 新增一个检查项

1. 新建 `src/repo_checkup/checks/<name>.py`，在里面定义一个 `Check` 子类，写好 `id`（kebab-case，全局唯一）、`title`、`order`（用 issue 里分配好的数字）和 `run(ctx) -> Result`。
2. 新建 `tests/checks/test_<name>.py`，用 `make_repo` 夹具现场建真实仓库来测，PASS / WARN / FAIL 每个分支都要覆盖。
3. **不改任何共享文件**（core.py、registry.py、report.py、cli.py、conftest.py、README 等）。缺什么工具函数，就写在自己的模块或测试文件里。如果确实要改共享文件，先停下来说明原因。
4. Context 提供的能力：`ctx.root`、`ctx.git(*args)`、`ctx.tracked_files()`、`ctx.find_file(*names)`。
5. 输出给用户看的文字（message / suggestion）用英文，只用 ASCII 符号。

## 工作流规则（所有会话都要遵守）

### 方案与提交
- 较大的改动先出方案，等我批准后再写代码。方案按「一步对应一个提交」来拆。
- 每完成一个能单独验证的小步骤就提交一次，一个提交只做一件事。
- 提交前，`uv run ruff format --check .`、`uv run ruff check .`、`uv run pytest` 必须全部通过。
- 提交信息用 Conventional Commits 前缀加中文说明，例如 `feat: 新增 license 检查`。中文提交信息用 heredoc 或 `git commit -F <文件>` 传入。
- 不许为了让测试通过而修改测试的期望值。确实需要改的话，先停下来向我说明原因。

### 分支与 PR（GitHub flow）
- main 受保护，只能通过 PR 合并。功能都在独立分支上开发：worktree 会话直接用自动建的 `claude/*` 分支；其他情况用 `<type>/<issue号>-<简短描述>`，例如 `feat/1-license`。
- 每个 PR 只解决一个 issue，描述里写 `Closes #N`，并按 `.github/pull_request_template.md` 填写：为什么改、改了什么、怎么验证的（贴测试结果）、有哪些风险，以及「工作流记录」。
- 开 PR 后，运行 `/code-review <PR号> --comment` 把 AI 审查意见贴到 PR 上留痕。然后按意见修改、推送，并在 PR 上逐条回复处理情况。

### 处理一个 issue 的标准流程
1. 用 `gh issue view N` 读需求和验收标准。
2. 出方案（一步对应一个提交），等我批准。
3. 确认当前在功能分支上，不是 main。
4. 每一步：写代码和测试 → 跑 format / check / pytest → 提交。
5. `git push -u origin <分支>`，然后 `gh pr create`（按模板写，包括工作流记录）。
6. `/code-review <PR号> --comment` → 按意见修改并推送 → 在 PR 上回复。
7. 等我来合并。你不合并。

### 授权
- 可以直接做：推送功能分支、创建 PR、在 PR 上回复评论、创建 issue 和 label。
- 先问我：创建远程仓库、修改仓库设置（包括分支保护）、打 tag、发 Release。
- 永远由我来做：合并 PR。
- 你不碰任何令牌和密码。需要登录或配置密钥的步骤，告诉我怎么做，由我自己完成。

### 环境
- Windows 环境下，命令一律用 Bash 工具，不用 PowerShell（公司的终端安全软件会对 AI 运行 PowerShell 告警；`.claude/settings.json` 里也已经禁用了 PowerShell）。
- Python 3.12，一律通过 uv 管理，禁止 conda / Anaconda。运行时零依赖，新增任何依赖（`uv add`）之前都要先问我。
- 仓库是公开的：不出现公司名称、内部路径、业务数据。

### 语言
- 代码里的标识符、注释，以及工具的输出，用英文。
- README、issue、PR 描述、提交说明，以及回复我的话，用中文。

### 学习模式
我在学习全流程。在一个会话里第一次进入某个新环节时（建分支、提交、开 PR、CI、分支保护、代码审查、合并、发版等），先用一两句中文告诉我：这一步在全流程里起什么作用，我该在这里把控什么。

### 工作流记录
每个 PR 描述里都要填「工作流记录」：
- 人工介入：我在这个任务里纠正或打回了几次，各是因为什么
- 返工：哪些步骤做了不止一遍，原因是什么
- 顺利的地方：哪些环节几乎不用我管
- 对流程的建议：这次暴露出 CLAUDE.md 或流程哪里该改

只写通用的观察，不写公司内部信息。
