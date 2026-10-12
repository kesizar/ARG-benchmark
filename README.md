# ARG-benchmark

用 ARG 和其他解谜测试模型的多种能力。总的能力框架尚未定名。

当前题是《非自愿摄入 / INVOLUNTARY APPETITE》。模型在本机浏览器里调查这份镜像，不访问原站。

- `mirror/involuntary-appetite/`：游戏镜像
- `mirror/serve_game.py`：本地服务，`http://127.0.0.1:8766/live/index.html`
- `mirror/harness/`：配套 agent（浏览器操作、调查笔记、动作解析）

密钥放在仓库根目录的 `.env`。
