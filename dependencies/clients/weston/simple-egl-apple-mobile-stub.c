/*
 * Apple mobile (iOS / iPadOS / visionOS) does not provide a Wayland-EGL winsys.
 * Upstream weston-simple-egl uses wl_egl_window + EGL_PLATFORM_WAYLAND_KHR,
 * which cannot initialize against Wawona's iland GBM/ANGLE stack and aborts
 * the host process (assert / wl_egl_window_destroy BAD_ACCESS).
 *
 * Nested GL validation on these targets is kmscube via WWNIlandPresenter.
 * Keep the simple_egl_main symbol for link compatibility; return nonzero so
 * the host can surface launch-failed without SIGABRT.
 */
#include <stdio.h>

int simple_egl_main(int argc, char **argv) {
  (void)argc;
  (void)argv;
  fprintf(stderr,
          "weston-simple-egl: Wayland-EGL unsupported on Apple mobile "
          "(use kmscube for nested GL)\n");
  return 127;
}
