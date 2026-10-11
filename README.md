# lifelog-coach

读取你的 Markdown 生活日志，让 AI 判断趋势、揪出破防目标，并给出下一步行动。

没有 App、没有数据库、没有云端同步。只有你的笔记和一条命令。

```
你的 Markdown 日志  ->  AI 评判  ->  趋势 / 红线 / 下一步
```

## 为什么做它

我用纯 Markdown 记录生活 —— 睡眠、训练、饮食、开销、时间、工作。
每天我都想要一双“第二双眼”：趋势是变好还是变差、哪个目标没达成、
以及明天最该做的那一件事。这个工具做的就是这件事。

## 快速开始

前置：Python 3.10+ 与 Node 18+。

```bash
git clone https://github.com/2953077361/lifelog-coach.git
cd lifelog-coach

npm install      # 下载前端依赖
cp .env.example .env   # 编辑 .env 填入 OPENAI_API_KEY
python run.py    # 一键启动，浏览器会自动打开 http://127.0.0.1:8777
```

`python run.py` 会自动处理全部准备工作，已完成的步骤会自动跳过：

```
创建虚拟环境 .venv -> 安装 Python 依赖 -> npm install -> 构建前端 -> 启动服务
```

常用参数：

```bash
python run.py --port 9000     # 换端口
python run.py --rebuild       # 强制重新构建前端
python run.py --no-open       # 不自动打开浏览器
python run.py --no-venv       # 直接用当前 Python，不切虚拟环境
```

只想用命令行、不启动界面的话，装好依赖后：`pip install -e .` 然后 `lifelog judge ...`。

## 配置

兼容任意 OpenAI-compatible 接口，默认使用 DeepSeek。

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY
```

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | 必填 |
| `OPENAI_BASE_URL` | `https://api.deepseek.com` | 任意 OpenAI 兼容接口 |
| `OPENAI_MODEL` | `deepseek-chat` | 模型名称 |

## 使用

```bash
# 评判单日（或一组文件）
lifelog judge 2026/2026-10.md

# 总结某一周
lifelog review 2026/ --week 10-05..10-11

# 把结果写入文件而不是打印到 stdout
lifelog judge 2026/2026-10.md -o judge.md
```

日志按带日期的标题解析，例如 `## 2026-10-10 (Sat)`。
`--week MM-DD..MM-DD` 只保留落在区间内的段落。

## Web 界面

自带一个本地 Web UI（Vue 3 + FastAPI，只监听 127.0.0.1）。入口就是上面的 `python run.py`，
也可以用命令行等价方式启动：

```bash
lifelog serve                 # http://127.0.0.1:8777
lifelog serve --port 9000
```

功能：

- 浏览本地目录树，勾选一个或多个 `.md` 日志/目录
- 切换 **单日评判 judge** / **周复盘 review**（支持 `MM-DD..MM-DD` 区间）
- 结果以 Markdown 渲染展示，支持复制、下载 `.md`、查看送模型的原文
- 历史记录留存于 `~/.lifelog-coach/history.json`（无数据库，可单条删除/清空）

前端开发态（改代码热更新，需同时开着后端）：

```bash
npm run dev                   # http://127.0.0.1:5173，/api 代理到 8777
```

## 开发

```bash
uv pip install -e ".[dev]"
uv run pytest
```

### 目录结构

| 路径 | 说明 |
| --- | --- |
| `src/lifelog_coach/cli.py` | 命令行入口：`judge` / `review` / `serve` |
| `src/lifelog_coach/reader.py` | 解析 Markdown 日志、按日期切分与筛选 |
| `src/lifelog_coach/server.py` | 本地 Web 服务与 REST API |
| `src/lifelog_coach/history.py` | 评判历史的 JSON 持久化 |
| `web/` | Vue 3 + Vite 前端工程 |

## 路线图

- v0.2 —— 给 agent 加上 *tools*：读取多份日志、计算 7 日均值，再做评判
- v0.3 —— 可配置的 metrics schema（让用户自己决定评判哪些指标）

## License

MIT
