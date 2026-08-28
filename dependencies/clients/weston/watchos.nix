# watchOS: enable simple-egl when CPU ANGLE is linked (WWN_WATCH_SWIFTSHADER).
args:
import ./ios.nix (args // { enableGlClients = true; })
