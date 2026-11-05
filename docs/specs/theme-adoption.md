# 主题接入（theme-adoption）— 038-minesweeper / auto-minesweeper

> 来源：auto-os/PLAN-060（桌面游戏三产品正式主题接入，主合同）。
> 消费形态与宿主策略定义见 OS `docs/specs/shell/host-theme-policy-and-delivery.md`；
> 批次登记见 OS `docs/specs/apps/product-theme-batch-060.md`。本页只记本产品
> 的实际表面与合法固定值，不重复宿主机制。

## 接入形态（2026-11-05，PLAN-060 T-03）

- `vendor/themes`：UI 管理渠道固定版本快照（themes 0.2.0，内容 digest
  `9fa07742dc68aa5377ae06cb2d966386002063f184c515b6c5dddf8a6bef838e`，per-file
  sha256 与源包逐文件校验同律；不可二次编辑、非第二权威源）。
- pac.at：本产品历来无 `theme:` 键（follow 语义原样）；新增
  `dep themes { path: "vendor/themes" }`；不声明 accent（原无）。
- app.at：`use themes.themes: Auto` + `design { theme: "Auto",
  mode: if .dark_mode … }`；App 级 `dark_mode` 位（Plan 458 契约变量名），
  种子链 AUTO_UI_THEME > os-config > 系统主题。
- 根卡（根 col）由半透明 `bg-zinc-900/40` 改为**不透明 `bg-card`**——
  fit 窗口下避免运行态底色透出；像素 oracle 目标=card token
  （Auto #ffffff/#0f0f12；Solarized #eee8d5/#073642）。

## 公共 role 映射（zinc 硬编码 → token）

| 原 legacy 值 | 现映射 | 面 |
|---|---|---|
| `bg-zinc-700 hover/active …border-zinc-600 text-zinc-100`（未揭格） | `bg-secondary hover:bg-secondary/80 active:bg-secondary/60 border-border text-secondary-foreground` | 格子 |
| `bg-zinc-900 border-zinc-800(/80)`（已揭格/雷格底） | `bg-background border-border/80` | 格子 |
| `bg-zinc-800/700`（表情按钮） | `bg-secondary hover:bg-secondary/80 border-border` | 按钮 |
| `bg-zinc-900 border-zinc-800`（难度容器） | `bg-secondary/60 border-border` | 面板 |
| `text-zinc-400 hover…bg-zinc-800`（难度未选） | `text-muted-foreground hover:text-foreground hover:bg-secondary/80` | 按钮 |
| `bg-zinc-700 text-white border-zinc-600/50`（难度选中） | `bg-primary text-primary-foreground border-primary/50` | 选中 |
| `bg-zinc-900/40 border-zinc-800/60`（根卡） | `bg-card border-border`（改不透明） | 根面 |

## 合法固定值（内容身份豁免，不随主题）

- **雷盘数字 1-8 色阶**（blue/emerald/rose/purple/amber/cyan/zinc/pink，
  inline `color:#…` + Tailwind `text-*` 双路）：规则身份（VM 视图构建器不可
  调函数，双路 string 前计算——chord/flood 两路径同值）。
- **💣/🚩/🙂/😵 语义与雷格红**（`bg-rose-950 border-rose-500`、flag
  `text-rose-400`）：游戏状态身份。
- **LCD 仪表暗底** `bg-zinc-950 border-zinc-800` + 计数 `text-rose-400`/
  计时 `text-amber-400`：仪表身份（经典 LED 面板），类比 tetris 井域豁免。
- 胜/负横幅 `text-emerald-400`/`text-rose-500`：状态身份。

## 验证入口

- 本批定向反控：`tests/test_060_theme.py`（leg A 显式暗 / leg B 显式亮 /
  leg C Solarized-dark 跟随 / leg D 中级切换后活跃局中换肤业务守恒+活体
  翻转实测生效 / leg E 重开追最新；oracle=card token 像素占比 ≥5%；
  `AUTO_BIN=<auto>` python tests/test_060_theme.py，证据在
  `D:/autostack/plan-artifacts/plan-060/auto-os/minesweeper`）。
- 原门分母（不动）：`python tests/desktop_mcp.py`（VM 轨真窗口交互）、
  `python tests/rust_smoke.py`（`auto build -r rust` 后编译 exe MCP 驱动）。
