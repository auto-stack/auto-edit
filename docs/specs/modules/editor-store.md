# EditorStore 契约（modules/editor-store）

> 来源：src/front/editor_store.at（527 行）头注与实现 + PLAN-003/005。
> 本册锁定状态语义与不变量；handler 清单以代码为准。

## 状态面（model）

- `tabs`：数组态，每 tab = `{key, title, path, dirty, src}`（Plan 420 P1）。
  `key` 唯一——code_editor registry 按它保存实例。
- 激活/派生标量（active/tab/tab_count/line/col/sel 等）：由 handler 就地
  重算，模板只读（VM view 不能调函数，Plan 402）。
- Console 面板数据、右键菜单坐标锚态、确认弹层开合态均在 store。

## tabs[i].src 数据语义（PLAN-005 收敛，硬契约）

**仅作初值/外部重置**：`last_external` 相等即 no-op（typed 输入不会被
stale 值踩掉）。**编辑态不回写**——cut/paste/undo/redo/ctx-cut 后的
编辑器全文回读已删（PLAN-005 A 段去镜像）；编辑器全文只在两个 save 位
读出（ActSave/QuitSaveClose；过渡形态，上游 delta/分块读供料后收口）。
**违例检测**：`tools/bench` 的"编辑路径全量读检测器"静态检查——新增
编辑路径回读即红（save 位白名单外）。

## 收口 helper（store handler 间经 store.Xxx() 互调，038/013 先例）

- `RemoveAt`——关闭 tab 的 remove + 索引修补 + 激活态重算（原
  CloseTab/ConfirmClose 各持一份，合一）。
- `SyncCursor`——line/col/sel 三元组读回（原 5 处重复，合一）。

## 数据面边界（PLAN-003 T-02）

全部 IO 经 `use back.api: ws_root, tree, read_text, write_text, exists,
env_str` 裸函数直调（merged=进程内 CALL；split/vue=HTTP）。front 内
**禁止** `fs.*`/`File.*`/`Env.get`/`fs.join`（vue 轨拦截面）；路径拼接
走本地字符串（`ws_dir + "/" + id`）。模块名 `fsys` 刻意避与内建 fs
对象同名（split 扁平化只吃整模块 use）。

## 生命周期约定

- `.Init` 名保留给根 widget 生命周期——store 侧初始化 handler 不得占用
  （现名 `LoadWorkspace`：fs.tree(AUTO_PROJECT_DIR, 4) + json.to_value
  装载真目录树；树节点 id 为相对路径）。
- 脏 tab 关闭与退出/关窗共用确认链（alert-dialog 模态，PLAN-530 族；
  菜单「退出」同入口）。
