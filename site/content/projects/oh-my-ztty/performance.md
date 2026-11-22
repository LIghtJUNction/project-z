# Performance

These measurements come from earlier releases and the configurations named in each section. They describe the costs observed in those runs; the current suite needs its own measurements.

Shell initialization, first completion and terminal memory are separate experiments. Each result includes its method and source record so you can inspect the scope or repeat the run.

## Framework startup

The zshard 0.1.2 experiment used an Intel Core i9-12900HX, Arch Linux and zsh 5.9.2. Each case has **31 interleaved launches after three warmups**. The times include process creation and initialization; prompt rendering is excluded for every case.

| Configuration | Median, ms | p95, ms | Idle PSS, KiB |
| --- | ---: | ---: | ---: |
| Plain zsh | 1.679 | 2.005 | 767 |
| zsh with audited completion | 12.291 | 15.236 | 2,308 |
| zshard, completion deferred | 4.106 | 5.114 | 1,161 |
| zshard, completion ready | 19.185 | 24.213 | 2,500 |
| Oh My Zsh, git + robbyrussell | 28.403 | 33.335 | 2,824 |

In this experiment, the Oh My Zsh initialization time was 6.92 times the deferred zshard time, or 1.48 times its completion-ready time.

The feature sets differ. The Oh My Zsh case uses its git plugin and robbyrussell theme without extra suggestion or highlighting plugins; it is pinned at commit `c0140703a53eb0d22be44f7bac318d0baacc927c`. These results do not establish a ranking of every shell or plugin combination.

[Framework method](https://github.com/LIghtJUNction/zshard/blob/v0.1.2/docs/performance.md) · [Individual samples](https://github.com/LIghtJUNction/zshard/blob/v0.1.2/docs/benchmarks/release-0.1.2.json)

## First completion

The first Tab took a median of **15.848 ms** with a warm completion dump. Creating a fresh dump took **147.310 ms**.

Deferring completion moves the work to when it is needed; it does not remove the work. The per-user installer prepares the audited dump before activating a release.

zshard 0.1.2 validates current completion files and native audit exclusions, including ownership changes and same-count file replacement. It retains native `compinit -i` auditing. That validation cost is included in the measurements.

[Cache design and compatibility](https://github.com/LIghtJUNction/zshard/blob/v0.1.2/docs/completion-cache.md)

## Complete suite startup

The suite 0.1.1 record includes a **40-sample interleaved experiment** of the full `omztty shell -i -c exit` path with the Ink preset:

| Configuration | Median, ms | p95, ms |
| --- | ---: | ---: |
| Complete preset shell | 10.914 | 13.057 |
| Minimum-feature vanilla zsh | 2.700 | 3.893 |

This includes the launcher and preset initialization. It excludes the prompt, first Tab, model calls and network activity. Do not combine this run with the independent framework experiment as though their times came from one controlled comparison.

## Live terminal memory

The same historical suite check opened one actual 100 × 28 cell window on an isolated Xvfb display, with a temporary HOME and Git checkout. It used the preset's 24 px padding and 13 pt font request. Fontconfig resolved JetBrainsMono Nerd Font in that environment.

No AI connection was active. Application memory excludes the X server and includes the resident ztty broker.

| Process | Before Tab, PSS KiB | After Tab, PSS KiB |
| --- | ---: | ---: |
| ztty broker and renderer | 10,425 | 10,425 |
| Preset zsh | 2,718 | 3,746 |
| Waiting launcher/client | 850 | 850 |
| Total | 13,993 (13.67 MiB) | 15,021 (14.67 MiB) |

PSS divides shared pages among the processes mapping them, reducing double counting in the total. These are samples at the stated idle points, not peak allocation or active AI-session figures. Font choices, plugins and other running applications can affect the result.

The measured integration archive is identified in the [raw suite record](https://github.com/LIghtJUNction/oh-my-ztty/blob/v0.1.1/docs/reports/linux-x86_64-suite.json). Formal GitHub release archives were built separately and have their own checksums.

A real first Tab left the installer-prepared completion dump's hash and modification time unchanged. See the [cache-reuse evidence](https://github.com/LIghtJUNction/oh-my-ztty/blob/v0.1.1/docs/reports/linux-x86_64-completion-cache.json).

## Native dotfile manager

The published zdot 0.1.1 executable is **53,848 bytes on x86_64** and **66,168 bytes on ARM64**. Both are static ELF files without libc or a dynamic interpreter.

zdot has no resident synchronization service. Explicit Git synchronization starts Git, whose resources are outside the native tool's own measurements.

The component's separate timing and memory experiment used a 53,776-byte local build. Its timings are not attributed to the exact published binary. [zdot method and evidence](https://github.com/LIghtJUNction/zdot/blob/v0.1.1/docs/performance.md)

## Reproduce a result

From a recursive source checkout:

```sh
python3 components/zshard/scripts/benchmark.py --samples 31 --output /tmp/zshard-benchmark.json
make -C components/zdot benchmark
```

The full-suite graphical check takes an archive and its checksum sidecar:

```sh
python3 scripts/verify_graphical.py dist/oh-my-ztty-0.1.1-linux-x86_64.tar.gz \
  --output /tmp/oh-my-ztty-evidence --samples 40
```

It requires Xvfb, xdotool, ImageMagick, zsh and the terminal's libraries. It creates an isolated home, display and broker socket, then cleans up the processes it owns.

A separate Xvfb/software-OpenGL terminal diagnostic is retained in the [full performance record](https://github.com/LIghtJUNction/oh-my-ztty/blob/main/docs/performance.md). It uses one launch per terminal and different padding units, so it is not a native GPU desktop ranking.
