# Performance evaluation

## Design and claim boundaries

Video cost comes from capture, pixel conversion/composition, encoding and
output. Control and UI overhead adds to that cost. zobs keeps media bytes
outside the Rust control process, can share encoded packets between file and
stream outputs, and redraws its native UI when state changes. These properties
motivate measurement; they do not establish lower resource use for every
workload or an end-to-end zero-copy pipeline.

The dependency-free core provides a rational timestamp scheduler and an RGBA
compositor that accepts caller-owned buffers without per-frame allocation.
Recording composition currently uses FFmpeg, rather than that core primitive.
`cargo bench --no-default-features --bench core` measures the core in isolation;
its result cannot establish desktop capture or encoding throughput.

## What the supplied comparison measures

The Linux scripts use installed native OBS, zobs, FFmpeg and ffprobe. Each run
creates fresh XDG configuration/data/cache/state/runtime directories and an OBS
profile with only bundled plugins. The test never reads the user's OBS profiles,
captures the user's desktop, opens a microphone or contacts a streaming service.
The generated file and output recordings remain within the test work directory.

The two implemented cases have different scopes:

| Case | zobs process tree | OBS process tree | Meaning |
| --- | --- | --- | --- |
| `idle` | Native GUI with its static scene-layout diagram, no capture/encoder job | Native GUI with an empty scene and preview disabled | Cost of these idle application windows |
| `recording` | Foreground CLI and FFmpeg children; no zobs GUI | Native GUI with preview disabled, decoding and recording the generated file | This automation-versus-desktop software-encoding workload |

The recording case is not an equal-GUI comparison. Neither case measures live
preview, desktop capture, hardware encoding, a complete OBS feature set, or
Windows/macOS behavior. A smaller idle process cannot establish a faster
encoder, and recording CPU ratios do not isolate GUI overhead from differences
in the media pipelines.

### Display modes

The default `--display-mode isolated` starts a private 1920×1080 Xvfb display
and sets `LIBGL_ALWAYS_SOFTWARE=1`. This provides a repeatable software-rendered
environment. OBS still performs its scene rendering and composition, which
can become expensive under a software renderer even with preview disabled.
This mode does not characterize a normal hardware-accelerated desktop.

`--display-mode existing` uses the caller's `DISPLAY` and preserves the caller's
renderer environment. It opens the benchmark's own windows on that display,
without starting or stopping a display server. Independent XDG directories,
bundled-plugin policy and generated-file inputs remain in effect: the recording
still contains only the generated fixture. Cleanup signals only the process
group launched for the run. Existing windows are excluded from startup checks
and are never controlled or closed.

Every run records its display mode, whether the harness forced software
rendering, and the effective `LIBGL_ALWAYS_SOFTWARE` setting. OBS OpenGL/renderer
log lines are retained when present. An existing display or a GPU name in a log
does not by itself verify acceleration; inspect the actual renderer and report
the observed environment. GPU utilization, GPU memory and hardware-encoder
performance are not measured by these scripts.

### Recording conditions and validity

Both applications loop the same generated lossless 1920×1080, 60 FPS file and
write Matroska with H.264/x264. Configuration requests `veryfast`, `zerolatency`,
four encoder threads, no B-frames, a 120-frame maximum keyframe interval,
6000 kbit/s target and maximum bitrate, a 12000 kbit VBV buffer, and no filler.
The script checks the x264 options embedded in the resulting bitstream instead
of trusting similarly named settings alone.

Both outputs include a silent AAC track configured for 192 kbit/s, 48 kHz and
stereo. OBS generates its silent output track with no audio input; zobs supplies
a generated tone with zero volume. Validation checks the actual codec, sample
rate, channel count and decoded silence. Silence may encode below the configured
bitrate. This tests comparable output audio, not identical audio-source code or
real microphone/mixing performance.

Output validation includes decoded frame count, frame timestamps, actual video
timeline, frame coverage, finalized container duration, codec/pixel format,
x264 options and a nonblank frame sample. Coverage must be at least 99.5% of the
frames expected from the actual timeline, and the timeline must cover warmup
plus measurement within 0.25 seconds. Decode errors or incomplete output make
the run invalid. These checks do not measure perceptual quality equivalence;
aligned source/output comparisons such as SSIM or VMAF require separate work.

OBS logs also provide output/drawn frame counts, recording start/stop times and
rendering/encoding lag. Any reported lagged or skipped frames disqualify that
run from the zero-drop 60 FPS comparison. The report retains resource samples
and failure details, but `recording_comparability.eligible=false` must never be
presented as a valid same-workload speedup. If OBS misses its target, report that
failure and its actual delivery rate, then resolve renderer or machine-load
constraints before drawing a general conclusion.

At the end of an OBS run, the harness sends SIGINT only to the original OBS
root process, after checking its PID, start time and session/group identity.
This lets OBS finish its muxer child instead of interrupting the muxer before
the container closes. It waits up to five seconds, then retains the same
owned-process-group SIGKILL fallback and root reaping. The generic sampler
defaults to group SIGINT; `--sigint-scope root` selects the supervisor-first
behavior. The report records the chosen scope and whether forced cleanup was
needed. Container completeness, recording-stop logs and frame-delivery gates
remain mandatory in either mode.

## Resource accounting and repeatability

`scripts/bench_process.py` samples the launched process and its descendants
every 100 ms by default. This includes FFmpeg and capture children. Reports
retain raw samples, average/peak RSS and PSS, and CPU time for the sampled
process identities. CPU expressed as cores means CPU seconds divided by elapsed
seconds: one fully occupied logical CPU is approximately one core.

RSS can count shared pages in more than one process; PSS apportions shared
pages. PSS is incomplete when a process cannot be read. A child that starts and
exits between samples can escape sampled CPU accounting, so the script also
retains separate `wait4` accounting with its stated scope. The display server,
desktop compositor and kernel/GPU memory sit outside the sampled application
trees. These measurement limits apply in both display modes. See the
[Linux `/proc` documentation](https://docs.kernel.org/filesystems/proc.html) for
the underlying process and memory counters.

The comparison alternates application order and records software versions,
generic hardware details, system load, available memory, swap and CPU/memory/IO
pressure before and after each run. These snapshots reveal background
contention; they do not remove it. Re-run on a quiet machine when heavy builds,
memory pressure or competing GPU work could explain a result.

For sustained performance claims, prewarm for 30 seconds, measure at least
120 seconds and repeat at least three times. The shorter commands below provide
targeted characterization and smoke validation; retain their actual durations
when reporting them. Always report invalid runs and variation across repeats.

## Reproduce

Build zobs and install native OBS, FFmpeg/ffprobe and, for the default mode,
Xvfb. The comparison requires Linux `/proc` and libX11. A Flatpak or shell
wrapper for OBS is rejected because it may bypass isolated XDG paths.

```sh
cargo build --release --locked
cargo bench --no-default-features --bench core

python3 scripts/compare_obs.py --zobs target/release/zobs \
  --mode idle --warmup 5 --duration 30 --repeat 3 \
  --output /tmp/zobs-idle.json --work-dir /tmp/zobs-idle-work

python3 scripts/compare_obs.py --zobs target/release/zobs \
  --mode recording --warmup 5 --duration 20 --repeat 3 \
  --output /tmp/zobs-recording.json --work-dir /tmp/zobs-recording-work
```

To run the same recording workload on an existing X11/XWayland display, execute
from a session with a valid `DISPLAY` and use:

```sh
python3 scripts/compare_obs.py --zobs target/release/zobs \
  --display-mode existing --mode recording --warmup 5 --duration 20 --repeat 3 \
  --output /tmp/zobs-existing-display.json --work-dir /tmp/zobs-existing-display-work
```

Each explicit `--work-dir` must be a new directory and retains generated media,
isolated configuration and logs. Omit it for automatic temporary-file cleanup;
the JSON report is still saved to `--output`. Exit code 2 means execution or
comparison validation failed; inspect the report before interpreting resources.
Use `--help` on either script for additional arguments. Keep raw media and
reports outside git, and publish only reviewed, non-sensitive evidence linked
to the tested source version.

## Evidence still needed for broader claims

These are additional acceptance workloads, not coverage supplied by the two
comparison cases above:

| Claim area | Required evidence |
| --- | --- |
| Hardware encoding | Same verified GPU/driver/encoder, matched settings and quality, CPU/GPU/memory use, frame delivery and latency |
| Desktop capture | Same actual display/source and permission path, matched preview state, captured-frame correctness and timing |
| Composition and audio mix | Matched multi-source scenes, transformations, real audio inputs, output quality and drop counts |
| File and RTMP together | Both outputs validated, throughput and latency measured, full sender/receiver accounting stated |
| Platform support | Native build plus physical-device capture/audio/encoding acceptance on each operating system |

Before publishing, review five questions: does the claim describe the implemented
capability; can another person reproduce the setup; does the effect repeat;
does the tested workload cover the claimed scope; and do the architecture and
measurement boundaries explain what remains unmeasured? Link each performance
statement to a valid report. A broad claim that zobs surpasses OBS in every
performance or memory scenario remains unestablished.

## Primary references

- [OBS backend design](https://docs.obsproject.com/backend-design): media pipeline and threading.
- [OBS launch parameters](https://obsproject.com/kb/launch-parameters): bundled-plugin and startup controls.
- [OBS x264 implementation](https://github.com/obsproject/obs-studio/blob/master/plugins/obs-x264/obs-x264.c): encoder-option mapping.
- [OBS hardware encoding](https://obsproject.com/kb/hardware-encoding): hardware encoder scope.
- [FFmpeg devices](https://ffmpeg.org/ffmpeg-devices.html): capture inputs and permissions.
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html): composition, mixing and quality metrics.
- [XDG ScreenCast portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html): general Wayland authorization path.
- [PipeWire DMA-BUF](https://docs.pipewire.org/devel/page_dma_buf.html): buffer format and synchronization requirements.
