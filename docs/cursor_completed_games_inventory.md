# Cursor 已完成游戏清单（Codex 去重用）

- 范围：仅 `configs/verify_from_source.json`（共 **182** 条），不是全表 748。
- 生成路径：本机 `D:\HuaweiMoveData\Users\17669\Desktop\ARG-benchmark`
- 完成度分布：{'has ending + required route gates': 95, 'ending-only (no separate gates)': 87}

## 图例
- **has ending + required route gates**：有结局且 routes 引用了必过 checkpoint
- **has ending + only optional gates**：有结局，gates 均为 optional
- **ending-only**：有结局、无单独 gates
- **incomplete / parse error**：缺 ending 或 judge 损坏

## 一览

| task_id | game_name | completion_status | config | judge |
|---|---|---|---|---|
| `anyu-bainian` | 暗语百年：序幕 | has ending + required route gates | `anyu-bainian.json` | `judge.json` |
| `fan-an` | 替另一个自己翻案 | ending-only (no separate gates) | `fan-an.json` | `judge.json` |
| `yexing-lingyuan` | 夜行 · 零元单 | has ending + required route gates | `yexing-lingyuan.json` | `judge.json` |
| `daojishi-48` | 倒计时48小时 | has ending + required route gates | `daojishi-48.json` | `judge.json` |
| `huicheng-317` | 317 · 回程 | ending-only (no separate gates) | `huicheng-317.json` | `judge.json` |
| `jiangyan-diannao` | 江燕电脑 | has ending + required route gates | `jiangyan-diannao.json` | `judge.json` |
| `haihe-shiguang` | 海河-拾光 | has ending + required route gates | `haihe-shiguang.json` | `judge.json` |
| `anma-dangan` | 暗码档案室 | has ending + required route gates | `anma-dangan.json` | `judge.json` |
| `wuyu-guichu` | 雾屿归处 | ending-only (no separate gates) | `wuyu-guichu.json` | `judge.json` |
| `duoluoleisi` | 多洛雷斯魔法学院 | ending-only (no separate gates) | `duoluoleisi.json` | `judge.json` |
| `jiangyan-yiyuan` | 江燕医院 | ending-only (no separate gates) | `jiangyan-yiyuan.json` | `judge.json` |
| `liefeng-guang` | 裂缝里的光 | has ending + required route gates | `liefeng-guang.json` | `judge.json` |
| `dianti-1` | 逃离电梯 第一章 | ending-only (no separate gates) | `dianti-1.json` | `judge.json` |
| `chaoxi-2` | 潮汐倒数 · 贰 | has ending + required route gates | `chaoxi-2.json` | `judge.json` |
| `linghao-0` | 0号线 | has ending + required route gates | `linghao-0.json` | `judge.json` |
| `baiwan-xiyun` | 百万美金西运记 | has ending + required route gates | `baiwan-xiyun.json` | `judge.json` |
| `wantu-yiwu` | 晚途遗物 | has ending + required route gates | `wantu-yiwu.json` | `judge.json` |
| `dianti-2` | 逃离电梯 第二章 | ending-only (no separate gates) | `dianti-2.json` | `judge.json` |
| `yiliu-gongzuozhan` | 遗留工作站 | has ending + required route gates | `yiliu-gongzuozhan.json` | `judge.json` |
| `dachu-wang` | 大厨王 | ending-only (no separate gates) | `dachu-wang.json` | `judge.json` |
| `feiqi-yiyuan` | 废弃的医院 | has ending + required route gates | `feiqi-yiyuan.json` | `judge.json` |
| `dongchuan-jiwei` | 东川市纪检委事件 | has ending + required route gates | `dongchuan-jiwei.json` | `judge.json` |
| `dongchuan-jingshen` | 东川市精神卫生中心 | has ending + required route gates | `dongchuan-jingshen.json` | `judge.json` |
| `emeng` | 噩梦 | has ending + required route gates | `emeng.json` | `judge.json` |
| `teddy` | 泰迪熊 | has ending + required route gates | `teddy.json` | `judge.json` |
| `shiluo-xinhao` | 失落的信号 | has ending + required route gates | `shiluo-xinhao.json` | `judge.json` |
| `haihe-zhaoxiang` | 海河照相馆 | ending-only (no separate gates) | `haihe-zhaoxiang.json` | `judge.json` |
| `wuye-pinlv` | 午夜频率 | has ending + required route gates | `wuye-pinlv.json` | `judge.json` |
| `xunhu-2000` | 寻呼2000 | has ending + required route gates | `xunhu-2000.json` | `judge.json` |
| `zhongding-arale` | 仲町阿拉蕾解谜社 | ending-only (no separate gates) | `zhongding-arale.json` | `judge.json` |
| `chixin` | 迟信 | ending-only (no separate gates) | `chixin.json` | `judge.json` |
| `lu-1024` | 20221024 | has ending + required route gates | `lu-1024.json` | `judge.json` |
| `mingde-tianjing` | 明德中学·天井密室 | ending-only (no separate gates) | `mingde-tianjing.json` | `judge.json` |
| `longyan-demo` | 龙岩往事 | has ending + required route gates | `longyan-demo.json` | `judge.json` |
| `jiangyan-app` | 江燕 | has ending + required route gates | `jiangyan-app.json` | `judge.json` |
| `kongzuo` | 空座 | ending-only (no separate gates) | `kongzuo.json` | `judge.json` |
| `wuluo-cun` | 雾落村·槐香引 | has ending + required route gates | `wuluo-cun.json` | `judge.json` |
| `fengchuan-sakiko` | 丰川祥子解谜社 | ending-only (no separate gates) | `fengchuan-sakiko.json` | `judge.json` |
| `qian-anon` | 与时柒的七日 | ending-only (no separate gates) | `qian-anon.json` | `judge.json` |
| `linxiao-an` | 林晓失踪案 | has ending + required route gates | `linxiao-an.json` | `judge.json` |
| `weituichu-xiatian` | 未退出的夏天 | has ending + required route gates | `weituichu-xiatian.json` | `judge.json` |
| `room-404` | 404号房间 | has ending + required route gates | `room-404.json` | `judge.json` |
| `sunken-city` | 沉没之城 | has ending + required route gates | `sunken-city.json` | `judge.json` |
| `tide-archive` | 潮声档案 | has ending + required route gates | `tide-archive.json` | `judge.json` |
| `rust-river` | 锈河镇 | has ending + required route gates | `rust-river.json` | `judge.json` |
| `shisanlou-xia` | 十三楼之下 | has ending + required route gates | `shisanlou-xia.json` | `judge.json` |
| `xunhu-1996` | 寻呼1996：案外之声 | has ending + required route gates | `xunhu-1996.json` | `judge.json` |
| `weiwancheng-diaoyan` | 未完成的调研 | has ending + required route gates | `weiwancheng-diaoyan.json` | `judge.json` |
| `yucai-gaozhong` | 东川市育才高级中学 | ending-only (no separate gates) | `yucai-gaozhong.json` | `judge.json` |
| `wuye-huisheng` | 午夜电台：回声计划 | has ending + required route gates | `wuye-huisheng.json` | `judge.json` |
| `yezhu-qun` | 业主群 | has ending + required route gates | `yezhu-qun.json` | `judge.json` |
| `hushan-xiangcheng` | IDS 拆字工坊 | ending-only (no separate gates) | `hushan-xiangcheng.json` | `judge.json` |
| `liushi-fenzhong` | 60分钟 再死一次 | ending-only (no separate gates) | `liushi-fenzhong.json` | `judge.json` |
| `fengzhi-juanyi` | 冯止疑案 | has ending + required route gates | `fengzhi-juanyi.json` | `judge.json` |
| `yongan-yiyuan` | 永安市中心医院 | has ending + required route gates | `yongan-yiyuan.json` | `judge.json` |
| `huguang-xinwen` | 弧光镇晚间新闻 | has ending + required route gates | `huguang-xinwen.json` | `judge.json` |
| `lumen-guiyi` | LUMEN · 归一 | has ending + required route gates | `lumen-guiyi.json` | `judge.json` |
| `weijian-shijian` | 东川市卫健委事件 | has ending + required route gates | `weijian-shijian.json` | `judge.json` |
| `sherlock-21` | 福尔摩斯在21世纪 | has ending + required route gates | `sherlock-21.json` | `judge.json` |
| `yinxin-jituan` | 东川银信集团 | has ending + required route gates | `yinxin-jituan.json` | `judge.json` |
| `guijia-zhinan` | 归家指南 | has ending + required route gates | `guijia-zhinan.json` | `judge.json` |
| `dongchuan-yizhong` | 东川第一中学 | has ending + required route gates | `dongchuan-yizhong.json` | `judge.json` |
| `ditie-moban` | 地铁末班车 | ending-only (no separate gates) | `ditie-moban.json` | `judge.json` |
| `xingdu-shuangzi` | 星都双子 | has ending + required route gates | `xingdu-shuangzi.json` | `judge.json` |
| `guaidan-shiyanshi` | 怪诞实验室 | ending-only (no separate gates) | `guaidan-shiyanshi.json` | `judge.json` |
| `guining-luguan` | 归宁旅馆 | ending-only (no separate gates) | `guining-luguan.json` | `judge.json` |
| `k7-dangan` | K7 数位典藏：第47次记录 | ending-only (no separate gates) | `k7-dangan.json` | `judge.json` |
| `niannian-buwang` | 念念不忘 | ending-only (no separate gates) | `niannian-buwang.json` | `judge.json` |
| `protocol-errormind` | protocol-errormind | has ending + required route gates | `protocol-errormind.json` | `judge.json` |
| `mark-pinocchio` | 马克·皮诺丘博物馆 | has ending + required route gates | `mark-pinocchio.json` | `judge.json` |
| `meiyou-cuo` | 可我真的没有错啊 | ending-only (no separate gates) | `meiyou-cuo.json` | `judge.json` |
| `mingri-huibo` | 明日回拨 | has ending + required route gates | `mingri-huibo.json` | `judge.json` |
| `ringo-liwu` | Ringo，生日礼物搞丢了 | has ending + required route gates | `ringo-liwu.json` | `judge.json` |
| `meishuo-zaijian` | 没说再见 | has ending + required route gates | `meishuo-zaijian.json` | `judge.json` |
| `elev-9` | ELEV 9 | ending-only (no separate gates) | `elev-9.json` | `judge.json` |
| `jiu-diannao` | 童年的旧电脑 | has ending + required route gates | `jiu-diannao.json` | `judge.json` |
| `fushou-yangkang` | 福寿养康 | has ending + required route gates | `fushou-yangkang.json` | `judge.json` |
| `denghui-8` | 第八届灯会 | has ending + required route gates | `denghui-8.json` | `judge.json` |
| `shenjia-yichan` | 沈家遗产 | has ending + required route gates | `shenjia-yichan.json` | `judge.json` |
| `disan-zhongxue` | 第三中学 | ending-only (no separate gates) | `disan-zhongxue.json` | `judge.json` |
| `neibu-diaocha` | 内部调查 | has ending + required route gates | `neibu-diaocha.json` | `judge.json` |
| `guimi-qiyun` | 闺蜜正在偷走你气运 | ending-only (no separate gates) | `guimi-qiyun.json` | `judge.json` |
| `dengta-jihua` | 灯塔 | has ending + required route gates | `dengta-jihua.json` | `judge.json` |
| `wanwu-youling` | 万物有灵 | has ending + required route gates | `wanwu-youling.json` | `judge.json` |
| `wuren-yingda` | 无人应答 | has ending + required route gates | `wuren-yingda.json` | `judge.json` |
| `jiankong-shishui` | 监控里是谁 | has ending + required route gates | `jiankong-shishui.json` | `judge.json` |
| `suqian-zhongxue` | 宿千中学 | ending-only (no separate gates) | `suqian-zhongxue.json` | `judge.json` |
| `tjq-shouhu` | TJQ-pleh亲情守护活动 | ending-only (no separate gates) | `tjq-shouhu.json` | `judge.json` |
| `dongchuan-yangguang` | 东川市阳光花园 | has ending + required route gates | `dongchuan-yangguang.json` | `judge.json` |
| `xinhao-jintou` | 信号尽头 | ending-only (no separate gates) | `xinhao-jintou.json` | `judge.json` |
| `xin-zhijia` | 心之家 | ending-only (no separate gates) | `xin-zhijia.json` | `judge.json` |
| `hongye-dianchang` | 逃离宏业电子厂 | ending-only (no separate gates) | `hongye-dianchang.json` | `judge.json` |
| `sanri-jijing` | 三日静寂 | has ending + required route gates | `sanri-jijing.json` | `judge.json` |
| `ditie-qiangzuo` | 地铁抢座大作战 | ending-only (no separate gates) | `ditie-qiangzuo.json` | `judge.json` |
| `dianying-qizhi` | 测测你的电影气质 | has ending + required route gates | `dianying-qizhi.json` | `judge.json` |
| `yiqi-xingxing` | 一起去看星星吧！ | has ending + required route gates | `yiqi-xingxing.json` | `judge.json` |
| `shancha` | 山茶 | ending-only (no separate gates) | `shancha.json` | `judge.json` |
| `sijiao-youxi` | 四角游戏 | has ending + required route gates | `sijiao-youxi.json` | `judge.json` |
| `wanwu-gongsheng` | 万物共生 | ending-only (no separate gates) | `wanwu-gongsheng.json` | `judge.json` |
| `jingqu` | 静区 QUIET ZONE // KX-0941 | has ending + required route gates | `jingqu.json` | `judge.json` |
| `liuxingyu` | 流星雨的约定 | has ending + required route gates | `liuxingyu.json` | `judge.json` |
| `feixian` | DEADLINE/废线 | ending-only (no separate gates) | `feixian.json` | `judge.json` |
| `huangyuan` | 荒原 | has ending + required route gates | `huangyuan.json` | `judge.json` |
| `mottai` | 地铁末班车 | ending-only (no separate gates) | `mottai.json` | `judge.json` |
| `zuori-jiuguan` | 东川市育才高级中学 | ending-only (no separate gates) | `zuori-jiuguan.json` | `judge.json` |
| `lanwan-jiaoyu` | 东川银信集团 | ending-only (no separate gates) | `lanwan-jiaoyu.json` | `judge.json` |
| `taoli-dianti` | 逃离电梯 | ending-only (no separate gates) | `taoli-dianti.json` | `judge.json` |
| `anwen-bainian` | 暗语百年 | ending-only (no separate gates) | `anwen-bainian.json` | `judge.json` |
| `zhangye-guangbo` | 第三中学内网 | ending-only (no separate gates) | `zhangye-guangbo.json` | `judge.json` |
| `bucunzai-ren` | 万物有灵 | ending-only (no separate gates) | `bucunzai-ren.json` | `judge.json` |
| `mofa-tuzi` | 福寿养康 | ending-only (no separate gates) | `mofa-tuzi.json` | `judge.json` |
| `haima-yanjiusuo` | 海马生命科学研究所 | ending-only (no separate gates) | `haima-yanjiusuo.json` | `judge.json` |
| `zhaoyu-xuzhang` | 昭瑜古镇 · 序章 | has ending + required route gates | `zhaoyu-xuzhang.json` | `judge.json` |
| `wuhai-zhiwu` | 无害之物 | has ending + required route gates | `wuhai-zhiwu.json` | `judge.json` |
| `suishi-kanfang` | 随时看房 | ending-only (no separate gates) | `suishi-kanfang.json` | `judge.json` |
| `zhengming-renlei` | 证明你不是人类 | ending-only (no separate gates) | `zhengming-renlei.json` | `judge.json` |
| `jiushi-wangxie` | 旧时王谢堂前燕 | ending-only (no separate gates) | `jiushi-wangxie.json` | `judge.json` |
| `tizui` | 替罪 | ending-only (no separate gates) | `tizui.json` | `judge.json` |
| `guijia` | 诡嫁 | ending-only (no separate gates) | `guijia.json` | `judge.json` |
| `hogwarts-escape` | The Hogwarts Escape | has ending + required route gates | `hogwarts-escape.json` | `judge.json` |
| `feibiyao-jiyi` | 非必要记忆 | ending-only (no separate gates) | `feibiyao-jiyi.json` | `judge.json` |
| `chenzhou-kezhan` | 沉舟客栈 | has ending + required route gates | `chenzhou-kezhan.json` | `judge.json` |
| `moli-dangan` | 茉莉与旧档案 | ending-only (no separate gates) | `moli-dangan.json` | `judge.json` |
| `shengnuofeike` | 圣诺菲克图书馆 | ending-only (no separate gates) | `shengnuofeike.json` | `judge.json` |
| `shisan-lou` | 十三楼 | ending-only (no separate gates) | `shisan-lou.json` | `judge.json` |
| `shengwu` | 圣物 | ending-only (no separate gates) | `shengwu.json` | `judge.json` |
| `yaolingshan` | 摇铃山缆车事故 | has ending + required route gates | `yaolingshan.json` | `judge.json` |
| `xiaoshi-hangxian` | 消失的航线 II：C-17-09 | has ending + required route gates | `xiaoshi-hangxian.json` | `judge.json` |
| `echo-sousuo` | ECHO | ending-only (no separate gates) | `echo-sousuo.json` | `judge.json` |
| `xuexiao-zaotang` | 学校澡堂的水声 | ending-only (no separate gates) | `xuexiao-zaotang.json` | `judge.json` |
| `jingmian` | 镜面 MIRROR | ending-only (no separate gates) | `jingmian.json` | `judge.json` |
| `kongguan` | 多维实体：空棺（又名多维尸体·空棺） | ending-only (no separate gates) | `kongguan.json` | `judge.json` |
| `fengxun` | 奉讯v1.2 | has ending + required route gates | `fengxun.json` | `judge.json` |
| `qianmianhu` | 千面湖景区 | ending-only (no separate gates) | `qianmianhu.json` | `judge.json` |
| `xinshiji` | 新世纪乐园失踪案 | has ending + required route gates | `xinshiji.json` | `judge.json` |
| `jinbu-shizong` | 进步网失踪案 | has ending + required route gates | `jinbu-shizong.json` | `judge.json` |
| `yiai-weiming` | 以爱为名 | ending-only (no separate gates) | `yiai-weiming.json` | `judge.json` |
| `nuhai-henji` | 女孩们的痕迹 | ending-only (no separate gates) | `nuhai-henji.json` | `judge.json` |
| `baichuan-wangshi` | 白川往事 | ending-only (no separate gates) | `baichuan-wangshi.json` | `judge.json` |
| `mom` | Mom | ending-only (no separate gates) | `mom.json` | `judge.json` |
| `baiyu-liudeng` | 白榆儿童疗养院 · 资料返院登记 | ending-only (no separate gates) | `baiyu-liudeng.json` | `judge.json` |
| `gongchengshi-qianbei` | 工程师前辈失踪案 | ending-only (no separate gates) | `gongchengshi-qianbei.json` | `judge.json` |
| `shiguang-wenrou` | 时光的温柔 | has ending + required route gates | `shiguang-wenrou.json` | `judge.json` |
| `laopengyou` | 老朋友之死 | has ending + required route gates | `laopengyou.json` | `judge.json` |
| `wuren-renling` | 无人认领 | ending-only (no separate gates) | `wuren-renling.json` | `judge.json` |
| `zuihou-zaixian` | 最后在线 | has ending + required route gates | `zuihou-zaixian.json` | `judge.json` |
| `changming-lvguan` | 长明旅馆·夜班守则 | has ending + required route gates | `changming-lvguan.json` | `judge.json` |
| `huanhun-zhi` | 还魂纸 · Demo | ending-only (no separate gates) | `huanhun-zhi.json` | `judge.json` |
| `huangdeng-huisuo` | 黄灯网络会所 | ending-only (no separate gates) | `huangdeng-huisuo.json` | `judge.json` |
| `wuren-li-an` | 无人立案 | has ending + required route gates | `wuren-li-an.json` | `judge.json` |
| `fangjian-404-yingzi` | 404——不存在的房间 | ending-only (no separate gates) | `fangjian-404-yingzi.json` | `judge.json` |
| `linzhixia-liuyan` | 林知夏的旧留言板 | has ending + required route gates | `linzhixia-liuyan.json` | `judge.json` |
| `tjq-pleh` | TJQ-pleh腕带问卷 | ending-only (no separate gates) | `tjq-pleh.json` | `judge.json` |
| `huaping-guniang` | 花瓶姑娘怪谈 | has ending + required route gates | `huaping-guniang.json` | `judge.json` |
| `hengda-kuaipao` | 恒大快跑 | ending-only (no separate gates) | `hengda-kuaipao.json` | `judge.json` |
| `beiying-hunsha` | 背影婚纱照 | has ending + required route gates | `beiying-hunsha.json` | `judge.json` |
| `fengbo-ting` | 风波亭 | has ending + required route gates | `fengbo-ting.json` | `judge.json` |
| `gaozhong-shizong-er` | 高中生旅行失踪案二 | has ending + required route gates | `gaozhong-shizong-er.json` | `judge.json` |
| `gaozhong-shizong` | 高中生旅行失踪案 | has ending + required route gates | `gaozhong-shizong.json` | `judge.json` |
| `shiyuan` | 始源 | ending-only (no separate gates) | `shiyuan.json` | `judge.json` |
| `tiexue-poxiao` | 铁血破晓 | ending-only (no separate gates) | `tiexue-poxiao.json` | `judge.json` |
| `yicun-shanhe` | 一寸山河一寸血 | ending-only (no separate gates) | `yicun-shanhe.json` | `judge.json` |
| `yongjia-huixing` | 永嘉彗星 | ending-only (no separate gates) | `yongjia-huixing.json` | `judge.json` |
| `suijing` | 碎镜 | has ending + required route gates | `suijing.json` | `judge.json` |
| `yian-juanzong` | 疑案卷宗 | has ending + required route gates | `yian-juanzong.json` | `judge.json` |
| `wuxing-xuming` | 五行续命坛 | ending-only (no separate gates) | `wuxing-xuming.json` | `judge.json` |
| `qingmiao-zhongxue` | 青苗中学 | ending-only (no separate gates) | `qingmiao-zhongxue.json` | `judge.json` |
| `jirou-youhuo` | 肌肉的诱惑 | has ending + required route gates | `jirou-youhuo.json` | `judge.json` |
| `qingchuan-linren` | 青川邻人网 | has ending + required route gates | `qingchuan-linren.json` | `judge.json` |
| `zhongzhuan-17` | 17号中转站 | ending-only (no separate gates) | `zhongzhuan-17.json` | `judge.json` |
| `daye-shisi` | 大业十四年 | has ending + required route gates | `daye-shisi.json` | `judge.json` |
| `jiangyan-xuexiao` | 江燕学校 | ending-only (no separate gates) | `jiangyan-xuexiao.json` | `judge.json` |
| `qingchun-huayu` | 青春花语 | ending-only (no separate gates) | `qingchun-huayu.json` | `judge.json` |
| `songgui-chumen` | 送鬼出门 | ending-only (no separate gates) | `songgui-chumen.json` | `judge.json` |
| `shaiziwu` | 骰子屋 | ending-only (no separate gates) | `shaiziwu.json` | `judge.json` |
| `xianghuo-taofeng` | 香火与讨封 | ending-only (no separate gates) | `xianghuo-taofeng.json` | `judge.json` |
| `yanhuo` | 验火 | ending-only (no separate gates) | `yanhuo.json` | `judge.json` |
| `yeliang-yinyi` | 夜晾阴衣 | ending-only (no separate gates) | `yeliang-yinyi.json` | `judge.json` |
| `ziye-shidian` | 子夜十点 | ending-only (no separate gates) | `ziye-shidian.json` | `judge.json` |
| `huanhun-yishi` | 404换魂仪式 | has ending + required route gates | `huanhun-yishi.json` | `judge.json` |
| `qiheng-qingjia` | 谁替我请假 | has ending + required route gates | `qiheng-qingjia.json` | `judge.json` |
| `xiaoman-douzuo` | 小满豆作 | has ending + required route gates | `xiaoman-douzuo.json` | `judge.json` |

完整字段见同目录 CSV。