# Asterisk Assistant 1.2.7

补齐 IPv6 自动续期任务自身的恢复。Wi-Fi 兼容循环每秒轻量核对续期任务的 PID 与启动时间，仅缺失时启动；Wi-Fi 设置仍每 15 秒应用，路由检查仍每 30 秒执行。独立健康守护也会补齐 Wi-Fi 兼容任务。任务仍由单实例锁保护；服务器手动停止或关闭兼容选项后，不主动恢复已停用的任务。

单次路由检查增加 20 秒时限和额外 2 秒强制退出期限，原始套接字增加 3 秒时限，避免一次卡住阻塞以后的续期。原有的路由有效期判断、账号配置和签名身份保留。

本地隔离测试覆盖任务丢失后的重新拉起、检查超时后的后续检查；这些测试模拟 Android 命令和时钟，不代表实机时延保证。最终 APK 安装并核对运行脚本后，三次受控终止新版续期任务，首次观测恢复分别为 **0.625、1.250、1.157 秒**，均通过后续稳定确认，PBX 进程号未变化。这是单台设备的任务恢复实测，包含观察开销，不是固定时限承诺；不替代实际路由续期、真实通话或整机重启验收。

Adds recovery for the IPv6 renewal worker itself. The Wi-Fi compatibility loop checks the renewal worker PID and start ticks once per second and launches only when missing. Wi-Fi settings retain their 15-second cadence and route checks retain their 30-second cadence. The independent health monitor also restores missing Wi-Fi compatibility workers. Manual stop and compatibility opt-out remain authoritative.

Each route check has a 20-second deadline with a further 2-second kill grace. The raw socket has a 3-second timeout, preventing a stuck attempt from blocking later renewal cycles. Existing route decisions, account configuration and production signing identity are retained.

Local isolated regressions cover a lost renewal worker and repeated check deadlines using mocked Android commands and scheduling. After installing the final APK and verifying its runtime scripts, three controlled kills of new-runtime renewal workers first observed recovery in **0.625, 1.250 and 1.157 seconds**. All replacements passed subsequent stability observation, with the PBX PID unchanged. These single-device worker-recovery measurements include observation overhead and are not fixed deadlines. They do not replace route-renewal, real-call or whole-device reboot acceptance.

APK 更新交接会按完整命令与启动时间识别旧 Wi-Fi 循环及其直接 sleep 子进程，释放旧版本遗留的锁后启动新代码，不重启 Asterisk。新增隔离回归覆盖身份缓存、PID 复用、旧循环退出、旧 sleep 持锁与无关进程排除。实际恢复耗时以设备测试为准。

APK replacement retires only snapshotted Wi-Fi loops and their direct sleep children after verifying full arguments and process start ticks. This releases inherited locks from older versions before starting the new loops without restarting Asterisk. Isolated regressions cover identity caching, PID reuse, old-loop retirement, old sleep ownership and unrelated-process exclusion. Recovery timing remains subject to device acceptance.

2026-11-01 最终版本实机补测：单次 PBX 业务进程退出后首次观测本地就绪 **2.97 秒**，随后稳定确认至少 3 秒。一次整机重启从发出请求开始计时，包含系统启动：系统完成 **37.53 秒**、用户自动解锁 **37.84 秒**、PBX 网关注册 **54.66 秒**、电话网关完整本地就绪 **62.00 秒**、全套服务齐备 **62.06 秒**，**66.08 秒**完成稳定确认。观察者未输入解锁或主动启动界面／服务；设备 `deviceSecure=false`，不代表设置安全密码后的首次解锁前恢复能力。这些单台设备、各一次、包含查询开销的观测不是时限保证，也不证明公网可达、实际呼叫或双向通话音频。

Final-version device follow-up on 2026-11-01: one PBX business-process kill first reached local readiness in **2.97 seconds**, followed by at least three seconds of stable observation. One whole-device reboot was timed from the request, including operating-system startup: boot completed at **37.53 seconds**, automatic user unlock at **37.84 seconds**, PBX gateway registration at **54.66 seconds**, full local gateway readiness at **62.00 seconds**, all services ready at **62.06 seconds**, and stability confirmed at **66.08 seconds**. The observer issued no unlock or Activity/service-start commands. The device reported `deviceSecure=false`, so this does not establish recovery before the first credential unlock on a securely locked device. These single-device, single-trial observations include query overhead and are not timing guarantees; they do not prove public-network reachability, a real completed call or two-way call audio.
