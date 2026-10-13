"""Optional container isolation. It stays off unless a task asks for it."""


def assert_isolation(cfg: dict) -> None:
    isolation = cfg.get("isolation") or {}
    if isolation.get("container"):
        raise RuntimeError("容器隔离默认关闭，当前只使用独立浏览器 context。请去掉 isolation.container 后再跑。")
