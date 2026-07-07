#!/usr/bin/env python3
"""Patch weston clients/window.c for in-process host compositor on Android."""

from __future__ import annotations

import sys
from pathlib import Path


def patch_includes(text: str) -> str:
    anchor = '#include <wayland-client.h>'
    block = anchor + """
#if defined(__ANDROID__)
#include <sched.h>
#include "wwn-mobile-clients.h"
#define WWN_DISPLAY_LOG(...) ((void)0)
#define wl_display_roundtrip(display) wwn_mobile_display_roundtrip(display)
#define wl_display_dispatch(display) wwn_mobile_display_dispatch(display)
#endif"""
    if "wwn-mobile-clients.h" in text:
        return text
    if anchor not in text:
        raise SystemExit("window.c wayland-client include missing")
    return text.replace(anchor, block, 1)


def patch_roundtrip(text: str) -> str:
    old = """\tif (wl_display_roundtrip(d->display) < 0) {
\t\tfprintf(stderr, "Failed to process Wayland connection: %s\\n",
\t\t\tstrerror(errno));
\t\tdisplay_destroy(d);
\t\treturn NULL;
\t}"""
    new = """\tif (wwn_mobile_display_roundtrip(d->display) < 0) {
\t\tfprintf(stderr, "Failed to process Wayland connection: %s\\n",
\t\t\tstrerror(errno));
\t\tdisplay_destroy(d);
\t\treturn NULL;
\t}"""
    if "wwn_mobile_display_roundtrip(d->display)" in text:
        return text
    if old not in text:
        raise SystemExit("window.c display_create roundtrip anchor missing")
    return text.replace(old, new, 1)


def patch_display_run_epoll(text: str) -> str:
    old = """\t\tcount = epoll_wait(display->epoll_fd,
\t\t\t\t   ep, ARRAY_LENGTH(ep), -1);"""
    new = """#if defined(__ANDROID__)
\t\t/* Timed wait yields to host compositor render thread (same process). */
\t\tcount = epoll_wait(display->epoll_fd,
\t\t\t\t   ep, ARRAY_LENGTH(ep), 1);
\t\tif (count == 0) {
\t\t\twwn_ios_pump_host_compositor();
\t\t\tsched_yield();
\t\t\tcontinue;
\t\t}
\t\twwn_ios_pump_host_compositor();
#else
\t\tcount = epoll_wait(display->epoll_fd,
\t\t\t\t   ep, ARRAY_LENGTH(ep), -1);
#endif"""
    if "wwn_ios_pump_host_compositor();" in text:
        return text
    if old not in text:
        raise SystemExit("window.c display_run epoll anchor missing")
    return text.replace(old, new, 1)


def main() -> None:
    path = Path(sys.argv[1])
    text = path.read_text()
    text = patch_includes(text)
    text = patch_roundtrip(text)
    text = patch_display_run_epoll(text)
    path.write_text(text)


if __name__ == "__main__":
    main()
