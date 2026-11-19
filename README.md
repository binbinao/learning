# Learning Notes

把「学一门新手艺」这件事标准化：每份材料都按同一套结构生成。

- 学习台阶（L1 能说清 → L4 能判断）
- 20 小时时间预算
- 只用三份资源
- 概念地图（核心假设差异）
- 自测题 + 解析
- 一页速查
- 费曼复述脚本
- 失效条件（这份材料什么时候不该用）

由 Hermes 技能 `learn-anything` 生成，`/learn <主题>` 触发。

构建：`python3 build.py`（读 `topics/*.md`，输出 `<slug>/index.html` 与首页）
