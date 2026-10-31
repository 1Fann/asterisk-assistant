# Asterisk Assistant 1.2.5

启用自动检查后，助手约每秒查看已知服务进程是否还在。若确认原 Asterisk 引擎已经退出，且手机空闲、后台运行已获授权、应用签名及运行文件均通过核验，助手会尝试恢复。手动停止、关闭监控、正在通话或无法确认通话状态时，保护条件继续生效。完整的网络与 SIP 检查仍按原设置执行。

修复了两类容易漏掉的故障：引擎恰在一次完整检查期间退出，以及引擎在前一次故障的重试等待中恢复后再次退出。更新时，正在执行的检查可以完成；交接旧监护进程不再长时间占用业务检查锁。反复故障仍有退避，避免连续重启。

更新使用原签名，保留已有部署、账号和后台权限设置。首次安装或换机仍需自行配置和授权。重启后能否免手动解锁取决于设备凭据和首次解锁状态。本版本不保证所有故障都能在固定秒数内恢复，也没有通过自动拨打真实电话来验证。

The monitor watches the verified engine at one-second intervals and retains an observed process loss across a full check or lock contention. A replacement worker observes the engine before it announces its own PID. Recovery checks the existing consent and manual-stop settings, current call state, signing identity and the actual deployed runtime files. An update lets an active check finish and releases its check lock before waiting for old monitor owners to retire. Persistent faults back off; the configured full SIP checks remain in place.

The APK retains the existing production signing identity. No account data or signing material is included. See VALIDATION.md for the conditions and limits of device measurements.
