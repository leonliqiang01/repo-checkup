# repo-checkup

> **实验项目，不维护。** 这个仓库是一次个人实验：用一个小工具，在 GitHub 上亲手把「AI 原生、但由人把控」的开发全流程走一遍。真正的产出是对流程的理解和一套可复用的项目模板，工具本身不会长期维护。

repo-checkup 是一个命令行工具，给本地 Git 仓库做「工程规范体检」：逐项检查，每一项给出 通过 / 警告 / 失败 和一句改进建议，最后给出总分。

## 用法

需要 [uv](https://docs.astral.sh/uv/) 和 git。

```bash
# 不安装，直接从 GitHub 运行
uvx --from git+https://github.com/leonliqiang01/repo-checkup repo-checkup [路径]

# 在本仓库里运行
uv run repo-checkup [路径]
```

- `路径` 默认是当前目录；它可以是仓库里的任意子目录，工具会检查整个仓库
- `--format json`：输出机器可读的 JSON
- `--list`：列出当前已实现的检查项
- `--version`：显示版本号

输出示例（对本仓库运行）：

```
repo-checkup 0.1.0.dev0  /path/to/repo-checkup

[PASS] readme  README.md has 42 lines of content

Score: 100/100  (pass 1, warn 0, fail 0)
```

### 退出码

| 退出码 | 含义 |
|---|---|
| 0 | 没有失败项（警告不算失败） |
| 1 | 至少有一项失败，适合在 CI 里用来拦截 |
| 2 | 用法错误：路径不存在、不是 git 仓库，或者找不到 git |

### 总分

通过记 1 分，警告记 0.5 分，失败记 0 分，按百分制折算后四舍五入。

## 检查项（v0.1 计划）

| id | 检查内容 |
|---|---|
| readme | 有 README，而且不是空壳 |
| license | 有 LICENSE |
| gitignore | 有 .gitignore，并覆盖 Python 常见项（.venv、`__pycache__` 等） |
| claude-md | 有 CLAUDE.md |
| tests | 有测试文件 |
| ci | `.github/workflows` 下有工作流 |
| commit-convention | 最近的提交信息符合 Conventional Commits |
| large-files | 没有跟踪大文件或压缩包（.zip / .rar / .7z） |
| version-copies | 没有 `xxx_v1`、`xxx_final`、`xxx副本` 这类「复制文件夹当版本管理」的目录 |

已经实现了哪些，以 `repo-checkup --list` 的输出为准。

## 开发

```bash
uv sync                  # 安装依赖
uv run ruff format .     # 格式化
uv run ruff check .      # 静态检查
uv run pytest            # 测试
```

- Python 3.12，src 布局，运行时零依赖（只用标准库，并通过 subprocess 调用 git）
- 检查项是插件式的：每个检查项是 `src/repo_checkup/checks/` 下的一个独立文件，配一个 `tests/checks/` 下的独立测试文件。新增检查项不需要改任何共享文件，框架会自动发现和注册
- 测试用 pytest 的 `tmp_path` 现场 `git init` 出真实仓库，不依赖网络
- 工作流规则（分支、提交、PR、代码审查）见 [CLAUDE.md](CLAUDE.md)

## 许可证

[MIT](LICENSE)
