/*
 * Standalone weston_log()/weston_log_set_handler() for the in-process client
 * toytoolkit build (android.nix / ios.nix). mobile-weston-host-clients.c and
 * wwn-weston-log.c extern-declare these expecting the *real* libweston
 * implementation (libweston/log.c) to provide them - true when this file is
 * staged into a full libweston build (macos.nix), but there is no such build
 * on the client-only mobile toytoolkit path.
 *
 * Do NOT "fix" this by linking libweston-compositor-13.a instead: doing so
 * also resolves android_jni.c's `weston_compositor_main` weak symbol (the
 * separate, opt-in "Nested Compositors Support" feature) and boots an
 * unrelated, not-Android-ready nested-compositor path that hangs the app.
 */

#include <stdarg.h>
#include <stdio.h>

typedef int (*wwn_weston_log_func_t)(const char *fmt, va_list ap);

static wwn_weston_log_func_t g_wwn_log_handler;
static wwn_weston_log_func_t g_wwn_log_continue_handler;

void
weston_log_set_handler(wwn_weston_log_func_t log, wwn_weston_log_func_t cont)
{
	g_wwn_log_handler = log;
	g_wwn_log_continue_handler = cont;
}

int
weston_log(const char *fmt, ...)
{
	va_list ap;
	int ret;

	va_start(ap, fmt);
	ret = g_wwn_log_handler ? g_wwn_log_handler(fmt, ap)
				: vfprintf(stderr, fmt, ap);
	va_end(ap);
	return ret;
}

int
weston_log_continue(const char *fmt, ...)
{
	va_list ap;
	int ret;

	va_start(ap, fmt);
	ret = g_wwn_log_continue_handler ? g_wwn_log_continue_handler(fmt, ap)
					  : vfprintf(stderr, fmt, ap);
	va_end(ap);
	return ret;
}
