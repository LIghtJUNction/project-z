# zobs

A small Project Z recording studio, with a native **zgpui** interface and
structured **CLI and MCP** automation.

zobs describes a scene, validates an output plan, supervises the media processes
and reports actual encoded-frame progress. FFmpeg handles codecs and containers;
wlroots Wayland capture uses wf-recorder. The control process does not copy the
video stream. A dependency-free `no_std` library supplies checked geometry,
rational frame scheduling and an allocation-free RGBA compositor. Recording
composition currently runs in FFmpeg; the core compositor is a separate library
primitive.

## Install

```sh
cargo install zobs --locked
zobs
```

Rust 1.100 or newer is required. See
[GitHub Releases](https://github.com/LIghtJUNction/zobs/releases) for published
versions and their native executables.
Install FFmpeg separately for recording or streaming. On Linux, the native
window also needs X11/XWayland, OpenGL, FreeType and fontconfig. Building it on
Debian/Ubuntu needs `build-essential pkg-config libx11-dev libgl1-mesa-dev
libfreetype-dev libfontconfig-dev`. wlroots Wayland desktop capture additionally
needs `wf-recorder` and permission to use the compositor's screencopy protocol.

For servers and headless automation:

```sh
cargo install zobs --locked --no-default-features --features std
zobs doctor
```

## Record something real

Record a five-second test pattern with audio:

```sh
zobs record --test --audio sine --output demo.mkv --duration 5
ffprobe -v error -show_streams demo.mkv
```

Record the desktop, stopping cleanly with Ctrl-C:

```sh
zobs record --output recording.mkv
```

`record` stays in the foreground, prints JSON status and returns a nonzero exit
code if the media job fails. Existing files are protected unless overwrite is
explicitly enabled. Prefer MKV for recordings that may be interrupted.

Use a scene file for multiple sources:

```sh
zobs record --config examples/picture-in-picture.json --output scene.mkv --duration 10
```

The sample combines generated video, an overlay and generated audio. Replace
the inputs with a local video file, camera or supported screen source. Each
input has an explicit position and size; crop, aspect-preserving scaling and
audio volume are available in the JSON model.

## Built for agents

Inspect a plan before running it:

```sh
zobs schema
zobs call output.plan '{"output":{"path":"demo.mkv","duration_secs":5}}'
zobs call encoder.probe '{"name":"libx264"}'
zobs mcp
```

MCP client configuration:

```json
{
  "mcpServers": {
    "zobs": { "command": "zobs", "args": ["mcp"] }
  }
}
```

The MCP session owns its scene and media jobs. Use `output.start` followed by
`output.status` or `output.stop` in that session. Closing stdin or sending a
normal termination signal finalizes and reaps its jobs. Independent zobs
processes have independent sessions; a fresh CLI invocation does not attach to
an existing GUI. `zobs call output.start` waits for its own output to finish.

Responses contain a `schema_version`, stable job ID, state, actual frame count,
media timestamp, output size and bounded logs. A newly spawned encoder remains
`starting` until it produces frames. Missing frame progress is visible as
`stalled` and eventually `failed`. `studio.capabilities` reports capture
discovery and compiled encoders; `encoder.probe` performs a bounded one-frame
trial encode. A successful probe verifies that encoder, device and frame size;
capture and sustained recording still need their own acceptance tests.

Streaming accepts an explicit RTMP/RTMPS URL. To keep a stream key out of shell
history, put it in an environment variable and use `zobs stream --url-env
ZOBS_STREAM_URL`. Plans and application logs redact stream credentials. The
encoder still receives its destination as an operating-system process argument;
use an appropriate local account boundary on multi-user machines.

## Media and interface support

| Capability | Current implementation |
| --- | --- |
| Native studio | zgpui; one editable active scene, source editors, output settings, device discovery and activity |
| Canvas | Static source-layout diagram; no decoded or live video preview |
| Generated/file sources | Test pattern, color, local video, looping files |
| Desktop capture | Linux X11 and wlroots Wayland through wf-recorder; Windows GDI/macOS AVFoundation plans through CLI/API |
| Camera | V4L2, DirectShow or AVFoundation plans, depending on platform and installed FFmpeg |
| Composition | API: up to 32 sources with crop/scale/overlay. GUI: up to 4 source editors with position and size |
| Audio | API: up to 8 generated/file/PulseAudio/ALSA inputs with resampling, volume, mix and limiter. GUI: off, test tone or default PulseAudio input |
| Encoding | API: H.264 software, NVENC, QSV, VAAPI, AMF or VideoToolbox, subject to runtime support; the GUI exposes a subset |
| Outputs | MKV, MP4, MOV, FLV, MPEG-TS and RTMP/RTMPS. API: simultaneous file and stream with one encode. GUI: one recording or stream at a time |
| AI control | Bounded stdio MCP, JSON CLI, schema catalogue, side-effect-free plans and explicit probe |

The wlroots capture path supports one full-canvas desktop source with no crop
or overlays, optional single PulseAudio input at unity volume, and x264/NVENC.
It requires a compositor exposing the screencopy protocol; general GNOME/KDE
portal capture is not implemented. The Linux GUI itself uses X11/XWayland.
See [operating details](docs/OPERATIONS.md) for interface and backend limits.

Windows/macOS capture and camera paths have not completed physical-device
runtime acceptance. Native build success, encoder discovery and actual capture
verification are tracked separately. Live scene switching, browser/game-source
plugins, transitions, replay buffer and virtual camera are outside this version.

## Performance

The design keeps the control plane small: bounded histories, event-driven GUI
redraw, reused MCP buffers, and direct pipes between capture and encoding.
Recording and streaming can share encoded packets. Capture, conversion and
encoding can still allocate or copy buffers inside their backends; this design
does not establish an end-to-end zero-copy pipeline.

The goal is lower CPU, memory and latency for matched workloads. Performance
claims must include FFmpeg and capture children, output quality, preview state
and matching encoder settings. See [performance methodology](docs/PERFORMANCE.md)
and the process-tree benchmark scripts. The supplied Linux comparison uses an
isolated Xvfb software-rendered display: idle compares both GUIs, while recording
compares the zobs CLI process tree against OBS with its preview disabled. It
also supports `--display-mode existing` to open its benchmark windows on the
caller's X11/XWayland display while keeping independent OBS configuration and
recording only the generated file. Neither mode establishes an overall
performance advantage over OBS. The core microbenchmark measures its own
primitives separately.

## Build and verify

```sh
cargo test --lib --bins --tests
cargo test --no-default-features --lib
cargo test --no-default-features --features std --lib --bins --tests
cargo test --test studio -- --ignored --test-threads=1
cargo test --test protocol -- --ignored --test-threads=1
cargo clippy --all-targets -- -D warnings
cargo bench --no-default-features --bench core
```

The ignored integration tests require real FFmpeg/ffprobe and use generated
media plus a loopback RTMP receiver. They do not contact a streaming service.
The optional `linux-software` feature selects zgpui's CPU window renderer.

## Release with one action

Open **Actions → Bump and release → Run workflow** and select `patch`, `minor`
or `major`. The workflow updates Cargo.toml and Cargo.lock together, validates
Linux/macOS/Windows builds, runs Linux media gates, publishes crates.io, tags
the verified source and uploads native release archives. `none` publishes the
current version or retries that version. Repository maintainers configure a
`CARGO_REGISTRY_TOKEN` secret once.

zobs is part of [Project Z](https://github.com/LIghtJUNction/project-z). Public
dependency changes follow its propagation and snapshot checks. Source is MIT;
installed FFmpeg/wf-recorder and native system libraries keep their own licenses.
