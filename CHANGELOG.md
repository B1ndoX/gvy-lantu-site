# 开发与发布日志

## 2026-11-27 · 恢复平台支持的统一Node版本

- 私有EdgeOne日志确认本项目部署dp3cpfw9xp18在切换24.22.1阶段失败，未开始项目安装/构建；原生产15fe9ab5850b7e130ee346105765203893ed61cd继续服务。平台当前预装列表最高24.18.0。
- 用户已授权三站统一恢复支持版本，配套将.node-version、.nvmrc、package/锁文件根engines和EdgeOne改为准确24.18.0/npm11.16.0。保留canonical守卫、CI版本文件入口、锁文件安装及各项目职责；依赖解析、业务数据、界面与游戏包保持原样。
- 本条为发布前候选记录，真实测试/PR/云端验收结果以项目上下文和后续日志为准。失败来源：https://console.cloud.tencent.com/edgeone/makers/zone-3ro4hcf3zn6d/makers-ibdsgnxgkanf/deployment/dp3cpfw9xp18；证据目录：/Users/bindox/Documents/Codex/Previews/sites-node24-supported-20261127。


## 2026-11-27 · 三站统一Node24.22.1（本地验证完成，发布待验收）

- 与舰队官网、蓝图、维科洛同批锁定准确Node24.22.1；.node-version、.nvmrc、package/锁文件根engines、EdgeOne与CI共用守卫。未改依赖解析版本、业务数据或调度。
- 本项目本地门禁与桌面/390px关键操作通过；官网233/45/351与11浏览器项，蓝图179 Python/70 Node（有重叠），维科洛183/Schema/审计均有独立日志。三站本地24.18与24.22.1生成的814份产物逐文件SHA相同。新云端日志仍待发布后核对，不能以相同产物证明云端Node。
- 使用新目录执行各站云端安装命令成功。旧24.18在候选守卫上被拒绝。依赖/游戏运行包保持，原文档整理/未知文件有备份，未清理现场。
- 用户已明确授权本轮三站统一发布及本机默认Node配套切换；按各自正常分支/PR、门禁和回退点操作。
- 本机证据：/Users/bindox/Documents/Codex/Previews/sites-node24-unify-20261127/；正式结果和当前状态以项目上下文为准。
