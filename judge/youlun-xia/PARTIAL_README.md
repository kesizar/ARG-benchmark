# 邮轮下篇本地适配：部分交付，非正式就绪

Python 3.11+；浏览器验收另需Python Playwright和Microsoft Edge。未调用模型API。基础运行时不包含在ZIP。

从独立评测包解压目录运行：

```
python judge/youlun-xia/serve.py --port 8821
```

浏览器打开 http://127.0.0.1:8821/index.html 。结束服务按Ctrl+C。重新开始按钮清空本局；新上下文同样从初始节点开始。服务根目录仅为tasks/youlun-xia，裁判在其外部。资源包可由具备MP4字节范围响应的静态服务器独立托管。

```
python judge/youlun-xia/test_local.py 8822
```

验收使用普通播放器进度条和选择按钮，覆盖六种终止视频的样本路线和重置；并不声称全片实时播放、原站等价或完整图UI覆盖。`evaluate.py`可由评测侧导入evaluate(state)，只计明确成功终局。

此版本缺上篇、完整可见线索充分性复核、正式推理检查点和共享harness任务配置；不得计入prepared/ready汇总。CONTENT_AUDIT.md保存结局分类和路线局限。两个ZIP名称均带partial以避免误认。
