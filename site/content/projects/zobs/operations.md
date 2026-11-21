# Operating zobs

## A session owns its media jobs

GUI, foreground CLI and MCP each create a `Studio`. An MCP connection is the
natural persistent automation session. Output IDs are local to that session.
No implicit background daemon is started. A new CLI invocation cannot inspect
or stop jobs in an existing GUI or MCP process. Normal stop, stdin EOF and
handled termination signals request graceful finalization and reap the
encoder/capture processes. If a process does not exit within the bounded stop
period, forced termination can leave its output unfinished.

| Operation | Effect |
| --- | --- |
| `studio.status` | Current scene and bounded job summaries |
| `studio.capabilities` | Backend discovery and compiled encoder list |
| `encoder.probe` | Bounded one-frame synthetic trial encode for one selected encoder/device/size |
| `scene.get` | Read the validated scene |
| `scene.set` | Atomically replace the validated scene for future jobs |
| `output.plan` | Validate and return redacted literal process arguments |
| `output.start` | Start a supervised media job |
| `output.status` | Actual progress and bounded diagnostic tail for a job |
| `output.list` | Bounded job summaries |
| `output.stop` | Finalize and reap a job; repeat calls return its terminal state |
| `events.list` | Bounded event stream after a sequence cursor |

Run `zobs schema` for complete field definitions and `zobs --help` for CLI options.

## Plan, start, observe, stop

Send the following arguments to `output.plan`, then to `output.start`:

```json
{
  "scene": {"width": 1920, "height": 1080, "fps": 60, "sources": [{"id": "main", "kind": "test"}]},
  "output": {"path": "capture.mkv", "duration_secs": 10, "encoder": "libx264", "bitrate_kbps": 6000}
}
```

Poll `output.status` with `{"job_id":"<returned job ID>"}`. `starting` means no
encoded frame has arrived yet. `running` requires actual frame progress.
`stalled` means recent progress has stopped; a bounded media timeout eventually
fails an unresponsive job. Terminal states are `completed`, `stopped` and
`failed`. Inspect both state and logs, and verify the resulting file when it is
part of an acceptance gate.

The duration is media time, not a claim about wall-clock throughput. Realtime
input pacing is enabled by default. Set `output.realtime=false` explicitly for
an offline generated-source or file-transcode benchmark and report that choice.
It removes software pacing from those inputs; physical capture remains limited
by the capture device. Changing a scene affects future jobs; running jobs keep
the scene they started with.

## Resource limits

The API accepts at most 8 active jobs, retains at most 32 jobs and 128 events,
and bounds each job's log tail by both bytes and lines. Scenes accept at most
32 video and 8 audio sources. Video dimensions are even, up to 7680×4320, with
1–240 FPS. JSON/MCP input is limited to 128 KiB; protocol output is bounded.
These limits bound control memory. Codec, source and operating-system buffers
must also be included in resource measurements.

## Native desktop

The GUI starts with a test-pattern scene description and opens no capture or
encoder until Start is pressed. Choose an output path and a duration for a
finite recording. The center canvas is a static layout diagram: its source
rectangles and generated pattern describe arrangement, without displaying
decoded media frames. Frame counts, elapsed media time and output state come
from the actual media job.

The GUI provides a smaller editing surface than the JSON API:

| Control | GUI | JSON API through CLI/MCP |
| --- | --- | --- |
| Scenes and video | One active scene, up to 4 source editors, position and size | Up to 32 sources per scene, with crop and file-loop settings |
| Audio | Off, generated tone or default PulseAudio input | Up to 8 sources with explicit devices/files and volume |
| Output jobs | One recording or stream at a time | Up to 8 active jobs; a job may write a file and stream together |
| Encoder selection | x264, VAAPI, NVENC, QSV, VideoToolbox | Those encoders plus AMF; all require runtime support |
| Desktop selection | X11 or wlroots Wayland | Also platform-specific Windows/macOS plans |

The Devices tab reports backend discovery and encoders compiled into the
installed FFmpeg. Availability does not prove a device can record; run
`encoder.probe` for a limited encode check and then validate real output. The AI
tab exposes copyable commands and redacted state for the GUI's session.
Commands launched in another process create their own session. Blocking media
work runs on a worker thread, status polling is bounded, and the window redraws
on input or changed state. Closing it stops the jobs owned by that window.

## Capture backends and platform limits

On a supported wlroots Wayland session, desktop capture uses `wf-recorder`,
encodes once, and sends the Matroska stream directly to FFmpeg for remuxing and
output. This path accepts one full-canvas source at position zero, no crop or
overlays, x264 or NVENC, and at most one PulseAudio input at unity volume. The
GUI restricts its controls accordingly; invalid API combinations fail planning.

Wayland support requires the compositor's screencopy protocol. General GNOME/KDE
XDG ScreenCast portal/PipeWire capture is not implemented. X11 capture is a
separate backend, and a valid XWayland display alone does not expose the full
Wayland desktop. The Linux GUI also needs X11/XWayland for its own native window.

Windows GDI desktop and DirectShow camera plans, and macOS AVFoundation plans,
are implemented through FFmpeg but have not completed physical-device runtime
acceptance. macOS requires screen/camera permission and a valid AVFoundation
device index; Windows camera input requires a valid DirectShow device. CI
compilation validates source portability, while capture, permissions, audio and
hardware encoding need acceptance on each target machine. See
[FFmpeg's device documentation](https://ffmpeg.org/ffmpeg-devices.html) for the
underlying input formats.

## Stream keys and output files

Pass streaming credentials through an environment variable or the masked GUI
field. Application results redact them. An administrator or another process
with sufficient local access may still inspect encoder process arguments.
Do not store credential-bearing scene requests in the repository.

The default refuses to overwrite a recording. Set both `output.path` and
`output.url` through the API for simultaneous file and RTMP output; they share
one encoding pass, and a failing output is reported as a failed job. Abrupt
power loss or an uncatchable process kill can interrupt container finalization;
MKV is the preferred recording container for such cases.
