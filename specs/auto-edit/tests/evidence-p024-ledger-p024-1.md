# evidence-p024 — P024-1 账本投影材料（PLAN-024 T-05——work 期备料，活账本落账=merge 期项）

> 纪律：work 不碰活账本（015-023 九连先例——023 T-05 在录）。本档=
> P024-1 外科插入材料+临时副本彩排回执；merge 期按本材料对 `.autoos/
> specs.json` reviews 段执行插入（25→26）+roundtrip 守卫。

## 插入位

`sections[id=reviews].items` 尾部（现 25 项，末项=P023-1）——追加第
26 项。

## P024-1 条目材料（落地实况已回填（merge 期 2026-10-02））

```json
{
  "id": "P024-1",
  "section": "reviews",
  "status": "stable",
  "title": "PLAN-024 — M4-07 收口件 merge 收据（work handoff pass@r1 ab67b5a[rebase 全等映射 ff-landed 0d35b5d]：帧两行重判 FAIL 维持〔725 中位 110→1-4ms ~30× 生效+P95 95-112ms/scroll 6.7-8.8fps 维持红——段外 ~108ms=S5 域 layout/shaping/draw 归因，auto-lang 余题回执〕+open_1gb 用户裁 (b) 登记收口〔供⑮ 文件后援分页 rope want 入供料档 §10——ledger-blocked-with-plan〕+NP++ 未装 Q-3 默认（列完整性非判定门 tag 不等待）+终检表十行（6 PASS+2 FAIL+n/a+(b) 登记收口）+tag 素材备档〔023 已录口径：帧两行不阻 tag——merge 期五检查点后打点〕）",
  "file": "docs/plans/archived/024-m4-closeout.md",
  "related": ["PLAN-024"],
  "superseded_by": null,
  "content": "- merge 五检查点（r1）：prepared=review 基线 main@266b227/工作树 plan-024-dev@0d35b5d〔base 957686f；五笔 db58f20→6fe7ba6/7ccb584→ca7774e/312ae85→ec5bb29/a2727ec→86c4d54/ab67b5a→0d35b5d——range-diff 5 对全=安全重写证明〕；landed=ff-only 零合并提交+main tip=0d35b5d〔18 文件 397+14-；main 烟测三绿=check 门 2579≥1588+canonical 四 SD 锚点+账本可解析〕；ledger_refreshed=本条 P024-1 外科插入 25→26〔roundtrip 守卫=json.loads 新旧深等〔他五段+reviews 前缀 25 项零扰动〕+插入项逐字回读——015-023 九连先例〕；work 判定面=N=4 帧谱（frame-20261002-141456/141537/141553/141631——141522 无效跑弃用如实）+anchors --verify 10 行+render --check 双绿+范围断言（.at 零 diff+组双树 clean）；archived/cleaned=随归档/清理检查点后续落账。"
}
```

## 彩排回执（临时副本——活文件零触碰）

命令：tempfile 复制 `.autoos/specs.json` → 追加上述条目 → roundtrip
守卫 → 插入项逐字回读。预期：25→26、他五段+前缀 25 项深等、
`P024-1` 回读 True。实录见 commit 附言（本档随 T-05 提交）。
