[ "$(getprop ro.product.device)" = chopin ] && [ "$(getprop ro.build.version.sdk)" = 33 ] || abort 'Requires the tested Redmi Note 10 Pro (chopin), Android 13.'
[ -n "$(pm path com.android.wifi.resources)" ] || abort 'Wi-Fi resources unavailable.'
set_perm_recursive "$MODPATH/system" 0 0 0755 0644
