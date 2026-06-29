{
  description = "wwn-weston: Wawona's Weston ports (toytoolkit + demo clients, nested compositor, weston-simple-shm) cross-compiled in-process for Apple platforms and Android, plus the iland DRM/GL compositor path.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    rust-overlay.inputs.nixpkgs.follows = "nixpkgs";
    wwn-toolchain.url = "github:Wawona/wwn-toolchain";
    wwn-toolchain.inputs.nixpkgs.follows = "nixpkgs";
    wwn-toolchain.inputs.rust-overlay.follows = "rust-overlay";
    wwn-iland.url = "github:Wawona/wwn-iland";
    wwn-iland.inputs.nixpkgs.follows = "nixpkgs";
    wwn-iland.inputs.wwn-toolchain.follows = "wwn-toolchain";
    wwn-kmscube.url = "github:Wawona/wwn-kmscube";
    wwn-kmscube.inputs.nixpkgs.follows = "nixpkgs";
    wwn-kmscube.inputs.wwn-toolchain.follows = "wwn-toolchain";
    wwn-kmscube.inputs.wwn-iland.follows = "wwn-iland";
  };

  outputs = { self, nixpkgs, rust-overlay, wwn-toolchain, wwn-iland, wwn-kmscube, ... }:
    let
      darwinSystems = [ "x86_64-darwin" "aarch64-darwin" ];
      linuxSystems = [ "x86_64-linux" "aarch64-linux" ];
      allSystems = darwinSystems ++ linuxSystems;
      forAll = nixpkgs.lib.genAttrs allSystems;
      inherit (wwn-toolchain.lib) withPlatformVariants baseRegistry mkToolchains;

      pkgsFor = system: import nixpkgs {
        inherit system;
        overlays = [ (import rust-overlay) ];
        config = { allowUnfree = true; allowUnsupportedSystem = true; android_sdk.accept_license = true; };
      };

      westonDir = ./dependencies/clients/weston;
      shmDir = ./dependencies/libs/weston-simple-shm;
    in
    {
      registryFragment = {
        weston = withPlatformVariants {
          android = westonDir + "/android.nix";
          wearos = westonDir + "/wearos.nix";
          ios = westonDir + "/ios.nix";
          tvos = westonDir + "/tvos.nix";
          ipados = westonDir + "/ios.nix";
          visionos = westonDir + "/visionos.nix";
          watchos = westonDir + "/watchos.nix";
          macos = westonDir + "/macos.nix";
        };
        weston-compositor = withPlatformVariants {
          android = westonDir + "/compositor-android.nix";
          ios = westonDir + "/compositor-ios.nix";
          tvos = westonDir + "/compositor-tvos.nix";
          ipados = westonDir + "/compositor-ios.nix";
          visionos = westonDir + "/compositor-visionos.nix";
          watchos = westonDir + "/compositor-watchos.nix";
          macos = null;
        };
        weston-compositor-drm = withPlatformVariants {
          android = westonDir + "/compositor-android-drm.nix";
          ios = westonDir + "/compositor-ios-drm.nix";
          tvos = null;
          ipados = westonDir + "/compositor-ios-drm.nix";
          visionos = null;
          watchos = null;
          macos = null;
        };
        weston-simple-shm = withPlatformVariants {
          android = shmDir + "/android.nix";
          ios = shmDir + "/ios.nix";
          tvos = shmDir + "/tvos.nix";
          ipados = shmDir + "/ios.nix";
          visionos = shmDir + "/visionos.nix";
          watchos = shmDir + "/watchos.nix";
          macos = shmDir + "/macos.nix";
        };
      };

      packages = forAll (system:
        let
          pkgs = pkgsFor system;
          tc = mkToolchains {
            inherit pkgs;
            registry = baseRegistry // wwn-iland.registryFragment // wwn-kmscube.registryFragment // self.registryFragment;
            extraArgs = { ilandSrc = wwn-iland; };
          };
          isDarwin = builtins.elem system darwinSystems;
        in
        (if isDarwin then {
          weston-ios = tc.buildForIOS "weston" { };
          weston-macos = tc.buildForMacOS "weston" { };
          weston-compositor-ios = tc.buildForIOS "weston-compositor" { };
          weston-simple-shm-ios = tc.buildForIOS "weston-simple-shm" { };
        } else { }));

      formatter = forAll (system: (pkgsFor system).nixfmt-rfc-style);
    };
}
