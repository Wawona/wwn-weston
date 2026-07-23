# tvOS: shm/toytoolkit only — never ANGLE/GL (platform-targets matrix).
args: import ./ios.nix (args // { enableGlClients = false; })
