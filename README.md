# Vibe-Knowledge-Awards

<p align="center">
  <img src="https://img.shields.io/badge/type-Agent%20Skill-6E56CF" alt="type">
  <img src="https://img.shields.io/badge/render-Canvas%20%2B%20seek(t)-0A7CFF" alt="render">
  <img src="https://img.shields.io/badge/audio-numpy%20synth-1DB954" alt="audio">
  <img src="https://img.shields.io/badge/ratio-16%3A9%20%7C%201920%C3%971080-FF8A00" alt="ratio">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
</p>

<p align="center"><b>用代码把一个知识点逐帧画成抖音「Vibe 知识大赏」式的无旁白短片。</b></p>

<p align="center"><b>简体中文</b> · <a href="README-en.md">English</a></p>

---

## 这是什么

一个给 AI Agent 用的 **skill**:做抖音「Vibe 知识大赏」式的**无旁白知识短片**。

成片 2–5 分钟、16:9 横屏、**没有人声**——观众读底部一行字幕,同时看屏上把这句话**演出来**。整片不拍摄、不剪素材,而是**由代码逐帧画出**:Canvas + JavaScript 画每一帧 → Playwright 驱动本机浏览器逐帧截图 → ffmpeg 压成视频 → 再混上声音。

它不是模板套用:每一镜的画面都照分镜表现写,先给概念找一个外行认得的形象,句子里说到什么屏上就是什么、动词真的发生。完整的创作方法论和流程在 `SKILL.md` 与 `references/`。

## 安装到本地 Agent

> **Tips｜最省事的装法**:直接把本仓库地址发给能执行命令的 Agent(如 Claude Code),说一句"帮我把这个 skill 装到本地:https://github.com/CodeTeng/Vibe-Knowledge-Awards",它就能自动 clone、放进 skill 目录、装好依赖和字体。下面是手动步骤。

把本仓库放进 Agent 的 skill 目录,**文件夹名保持 `vibe-knowledge-awards`**(要与 `SKILL.md` 里的技能名一致,仓库名和这个文件夹名可以不同)。Claude Code 的常见位置是 `~/.claude/skills/vibe-knowledge-awards`。

```bash
git clone git@github.com:CodeTeng/Vibe-Knowledge-Awards.git vibe-knowledge-awards
# 放到你的 agent skill 目录,例如:
#   mv vibe-knowledge-awards ~/.claude/skills/

cd vibe-knowledge-awards
pip install -r requirements.txt     # playwright / numpy / scipy / Pillow
python -m playwright install        # 下浏览器驱动
python engine/get_fonts.py          # 下开源字体(SIL OFL,不随仓库分发)
```

还需要本机已安装 **Google Chrome** 和 **ffmpeg**(需带 H.264 编码,如 libx264)。渲染脚本打开的是本机 Chrome;字体按 SIL Open Font License 单独下载,所以先跑一次 `get_fonts.py`。

装好后,对 Agent 说一句"做一条 Vibe 知识大赏的视频,讲 XX",它会读 `SKILL.md` 自动走完整流程。

## 两种风格

题材决定风格,在分镜表之后定:

- **C 夜曲**:讲抽象、看不见的机制(数学、逻辑、信息、物理),拆成几个当场可演的小实验。深蓝黑底、大字、带刻度的仪器与画得像实物的东西,声音完全由代码合成。拿不准就选 C。
- **B 寓言**:讲心理 / 行为机制,从动物实验或生活场景讲到"你该怎么办"。每场一幅用代码画的扁平插画,有角色、有动作,配一首背景乐。最费工。

一条片只用一套风格。两套的色、字、版式、片名卡、声音规格都在 `references/worlds.md`。

## 怎么使用

### 交给 Agent(推荐)

把一份写好的文案,或一个选题,直接丢给装了本 skill 的 Agent。它会按 `SKILL.md` 的流程走:

1. **立题和事实表** —— 一句话论点 + 概念清单,核实年份/人名/数字的出处。
2. **找形象** —— 给每个概念找一个外行认得的东西来演(决定片子好坏的一步)。
3. **文案 + 分镜表** —— 一句字幕一行,写清每句屏上是什么、在干什么、配什么声。
4. **选风格** —— C 夜曲或 B 寓言。
5. **建工程、先做最难的一镜** —— 截静帧自查。
6. **前 30 秒样片** —— 先给你看 30 秒,确认后再铺全片。
7. **铺全片 → 配声音 → 终检交付**。

过程中它会在关键节点停下来给你看方案(找形象、分镜表、30 秒样片),确认后才往下走。

### 手动跑脚本

工程建在你自己的项目里,**不要建在 skill 目录内**。

```bash
# 1. 建工程(C 夜曲;B 寓言用 --world B;竖屏/方形加 --size 1080x1920;时长默认=自带 BGM,--secs 覆盖)
python scripts/new_film.py <工程目录> --world C

# 2. 边写 film.js 边自查画面
python engine/render.py <工程目录> --serve              # 浏览器实时预览
python engine/render.py <工程目录> --sheet 16           # 全片均匀 16 帧拼一张
python engine/render.py <工程目录> --density            # 动效密度自检:标出静止段

# 3. 渲染全片(无声)
python engine/render.py <工程目录>                      # → renders/raw.mp4
python engine/render.py <工程目录> --jobs 4             # 长片分 4 路并行

# 4. 声音 + 合片 + 封面(默认叠自带 BGM,BGM 放完视频即结尾)
python engine/audio.py  <工程目录> --beats              # 先量 BGM 的 BPM/小节头/段落(卡点用)
python engine/render.py <工程目录> --events             # 导出音效事件表
python engine/audio.py  <工程目录> --probe              # 合成声音 + 合片 → renders/final.mp4,并出音轨体检图
python engine/render.py <工程目录> --cover 18.5         # 抽一帧当封面 → renders/cover.jpg
```

引擎 API、命令细节、写法与坑见 `references/engine.md`;字幕/画法/找形象/分镜表见 `references/visualization.md`;声音编排见 `references/worlds.md`。

## 样片

TODO

## 许可

引擎、脚本和文档里的方法说明使用 MIT 许可,见 `LICENSE`。

`references/analysis.md`、`references/prompts.md`、`references/visualization.md` 里按参考片记下的字幕和画面设计,以及 `examples/stim_B`、`examples/info_C`,来自他人的短片,**版权属于原作者**,只供学习对照,不授权复制、发布或当作自己的作品使用。做新片请用 `python scripts/new_film.py` 建空骨架,照自己的分镜表现写。

## 致谢

本项目基于开源项目 **[HeyChengC/vibe-knowledge-film](https://github.com/HeyChengC/vibe-knowledge-film)** 改造而来,原项目以 MIT 许可开放。在此向原作者致谢。本仓库沿用 MIT 许可。
