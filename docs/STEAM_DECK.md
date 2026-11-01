# Steam Deck

The Windows package runs on the Deck under Proton, but the native Linux build is much faster there:
no Windows translation layer, and RADV directly. This page covers the Steam Deck AppImage, the
settings that suit the Deck, and how to add it to Steam.

## Get the AppImage

- From CI: the **Steam Deck AppImage** workflow (`.github/workflows/steamdeck.yml`) uploads
  `Uncharted-The-Nathan-Drake-Collection-x86_64.AppImage` as an artifact, and attaches it to tagged releases.
- Or build it: `nix-shell shell.nix --run "bash build.sh"`, `BB_FSR4_TIERS=1080 bash
  tools/fetch_fsr4_assets.sh`, then `nix-shell shell.nix --run "bash packaging/appimage.sh"`.
  Nix can run in Docker (`nixos/nix`) on distributions without it.

## Add it to Steam

1. In Desktop Mode, put the AppImage where it will stay and double-click it. The Uncharted
   launcher opens on the Game page: choose the folder of your dump.
2. On the Play page, **Add to Steam** (one entry for the collection, or one per game). Steam closes
   while the entries are written and opens again. Each entry starts the AppImage with `--play`, and
   comes with a Steam Deck controller layout (launcher/steamdeck: gamepad, gyro to mouse while the
   gyro button is held); a layout you saved for that entry yourself is kept.
3. Play from Gaming Mode. On a Steam Deck the launcher's defaults are the settings below; open the
   AppImage again in Desktop Mode to change anything. Moved the AppImage? Add to Steam again.

Steam Input reaches the game ("gamepad connected" in `last_run.log`). The AppImage's entry program
clears `LD_PRELOAD` and `LD_LIBRARY_PATH` first: Steam's overlay library needs the host
`libGL.so.1`, which the AppImage's own closure does not contain, and the AppImage would stop
before the game starts. The Steam overlay is therefore not shown; the quick access menu works.

## Settings

| Setting | Value | Why |
|---|---|---|
| `BB_GAME_RES` / `BB_WINDOW_SIZE` | `1280x800` | The Deck screen: full 16:10 view, no scaling. `1280x720` is ~2-5 FPS faster with bars. |
| `BB_VBLANK_HZ` | `120` | On a 60 Hz screen a frame that misses 16.7 ms waits until 33.3 ms; at 120 Hz it waits until 25 ms, so drops below 60 are much milder. |
| `BB_UPSCALER` | `off` | FSR 3 native AA at 720p cost ~5 FPS on the Deck GPU. |
| Live resolution | off (startup patch) | As in docs/CHANGES_2026-10-02.md: the live path drops the Deck to single digits. |

Lower render sizes help little: at 576p Uncharted 3 gained ~2 FPS over 720p.

## Measurements

Steam Deck (LCD, SteamOS 3.9.5), scripted runs (`BB_PAD_FILE`) from the same saves: 40 s standing,
25 s walking. FPS from `BB_FRAME_STATS`.

| | Proton, 0.3.8 Windows package, 720p | Native AppImage, 720p, 120 Hz | Native, 1280x800, 120 Hz |
|---|---|---|---|
| Uncharted 1 (jungle), standing / walking | 47 / 55 | 53 / 62 | – |
| Uncharted 2 (train cliff) | 35 | 68 | 63 |
| Uncharted 3 (museum), standing / walking | 45 / 55 | 51 / 62 | 49 / 61 |

For reference, the Windows package's defaults on the Deck (1080p, live resolution, FSR 3 native AA)
gave ~25 FPS in the Uncharted 1 scene. Uncharted 2 with the 0.3.10 Windows package under Proton:
40 FPS, so most of the native build's gain there is Proton's overhead, not newer code.
