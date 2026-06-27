# wwn-weston

Wawona's [Weston](https://gitlab.freedesktop.org/wayland/weston) ports, cross-compiled
**in-process** as static archives for Apple platforms (iOS/iPadOS/tvOS/watchOS/visionOS)
and Android, plus the nested compositor and the iland DRM/GL path:

- `weston` - real toytoolkit (`clients/window.c`) + demo/terminal clients (`libweston-13.a`, `libweston-terminal.a`, ...), each `main` renamed to `<name>_main` for in-process driving by Wawona.
- `weston-compositor` - nested wayland/headless compositor (`libweston-compositor-13.a`, entry `weston_compositor_main`).
- `weston-compositor-drm` - the iland DRM/KMS compositor variant (consumes `wwn-iland` udev/gbm shims).
- `weston-simple-shm` - the minimal SHM demo client archive.

Patch-overlay model: pristine Weston 13.0.0 is fetched and patched at build time
(`terminal-patches/`, `verify-weston-ios-patches.py`). Built with
[wwn-toolchain](https://github.com/Wawona/wwn-toolchain); the GL/DRM path uses
[wwn-iland](https://github.com/Wawona/wwn-iland).

## Use

```nix
inputs.wwn-weston.url = "github:Wawona/wwn-weston";

registry = wwn-toolchain.lib.baseRegistry
  // wwn-iland.registryFragment
  // wwn-weston.registryFragment;
extraArgs = { ilandSrc = wwn-iland; };   # compositor copies iland udev/gbm shims
```

## Standalone build

```sh
nix build .#weston-ios
nix build .#weston-compositor-ios
nix build .#weston-simple-shm-ios
nix build .#weston-macos
```

## License

MIT for the Wawona Nix packaging / patches (see `LICENSE`). Weston itself is MIT;
its source is fetched from upstream at build time.
