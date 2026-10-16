# Shell Utilities 🛠️

A robust collection of advanced, modular shell functions engineered to optimize environment synchronization, automate recursive script bootstrapping, and handle batch file interoperability smoothly across Linux environments.

---

## 📌 General Philosophy

In DevOps and local terminal environments, engineers face two recurring friction points:

1. **The `.bashrc` Clutter Problem:** Manually adding shortcuts, scripts, or multiple `source` lines creates maintenance nightmares and performance degradation over time.
2. **Platform Constraints & Code Portability:** Security configurations on modern platforms (like cloud environments or enterprise firewalls) frequently block the raw transfer or upload of executable `.sh` files, requiring rapid text extraction for Large Language Models (LLMs) or visual review.

This repository resolves these problems with zero external dependencies, emphasizing **idempotency** (running a tool multiple times without changing the result beyond the first application), **fail-safe defenses**, and strict cross-platform compatibility.

---

## 🚀 Deep-Dive Tool Documentation

### 1. `add2bash` (v0.5)

`add2bash` acts as a smart configuration injector and local environment manager for your main shell settings file (`~/.bashrc`). It features a dual-execution architectural path determined dynamically by user input.

```
                [Executed add2bash]
                        |
            /-----------------------\
     (Has Arguments)         (No Arguments)
           |                       |
   Inject Raw Custom       Generate Recursive
   Text to ~/.bashrc       Central 'load_all.sh'
                                   |
                           Verify .scriptignore
                                   |
                           Inject Entrypoint 
                             into ~/.bashrc

```

#### 🔹 Operational Frameworks

* **Mode A: Raw Text/Alias Appendment (Arguments Passed):** When executed with strings (e.g., `add2bash "alias k='kubectl'"`), the utility acts as a verified appender. It abstracts raw echo injections, showing a clean text preview and preventing malformed strings from ruining your environmental profile.
* **Mode B: Recursive Central Loader Bootstrapping (No Arguments):** When run standalone inside a directory containing shell scripts, it automatically compiles an isolated, executable script called `load_all.sh`. It then updates your system's `~/.bashrc` to source only this specific loader file exactly once.

#### 🔹 Technical Implementation Details

* **Deterministic Tracking & Idempotency:** The utility computes a dynamic target header tag signature: `# [add2bash] Central Loader for <Target_Path>`. Before running any write process, it runs a quiet structural lookup utilizing `grep -Fq`. If the sequence is found, it terminates early to avoid duplicate initialization paths.
* **Dynamic Sourcing Tree (`load_all.sh`):** The output module is pre-coded to query real-time execution locations dynamically via `readlink -f` combined with `$BASH_SOURCE` context mapping. It discovers all `.sh` extensions downward through a memory-safe `find` execution using null-byte line terminations (`-print0`) to avoid token-splitting issues on spaced filenames.
* **Advanced Cross-Platform `.scriptignore` Parser:** The generated loader reads matching ignore files line-by-line (`IFS= read -r line`). It strips raw Windows carriage returns (`\r`) automatically using `tr -d` and eliminates trailing shell whitespaces via `xargs`. This ensures your rules work flawlessly even if patterns are composed or edited on Windows platforms (CRLF line-ending format).
* **Infinite Execution-Loop Hardening:** Inside its runtime compilation shell loop, `add2bash` maps the filename variable against its own system runtime identity array (`$BASH_SOURCE`). If a match occurs, or if files lack explicit readable permissions (`! -r`), it triggers a shortcut `continue` instruction, ensuring the loader never tries to context-source itself recursively.
* **Interactive Approvals:** Destructive actions or files containing changes intended for target setup arrays are strictly halted beforehand by an internal validation function (`confirm_action`), waiting for a positive `[y/Y]` manual user interaction.

---

### 2. `sh2txt` (v0.1)

`sh2txt` is a quick batch utility designed to locate executable `.sh` files in a workspace and safely copy them into `.txt` extension replicas. This simplifies sharing script content with LLMs, pasting script blocks inside documentation repositories, or moving code through firewalls that flag `.sh` binaries.

#### 🔹 Operational Frameworks

* Automatically evaluates input directives. If a targeted path parameter is missing (`$1`), it targets the current working directory (`.`).
* Iterates sequentially through match targets without triggering breaking execution syntax errors.

#### 🔹 Technical Implementation Details

* **Zero Match Error Safeguard:** Standard directory loops fail or display system warnings if shell wildcards come up empty. `sh2txt` uses structural evaluation bounds (`[ -f "$f" ] || continue`) to safely bypass processing if no `.sh` files exist in the folder.
* **Native String Parameter Expansion:** Instead of spawning system overhead processes like `sed` or `awk` to change the filename extension, the code handles renames using native shell parameter expansion: `${f%.sh}.txt`. This isolates the trailing suffix, cleanly transforming `script.sh` into `script.txt`.
* **Built-in Scalability (Recursive Blueprint):** The tool includes a pre-built, alternative architecture commented out in the code. By toggling the comments, users can replace the single-tier directory loop with an advanced, multi-tier recursive engine powered by `find -exec sh -c 'for f; do cp -- "$f" "${f%.sh}.txt"; done' sh {} +`. This processes deeply nested scripts within an optimized subshell execution pattern.

---

## 🛠️ Quick Start & Integration Operations

### Step 1: Clone and Stage the Utilities

Download the script files into your chosen automation or local development path:

```bash
mkdir -p ~/scripts && cd ~/scripts 
git clone https://github.com/Kilobyte4621/shellutilities.git
cd shellutilities

```

### Step 2: Immediate Interventions (On-The-Fly Sourcing)

Because these utilities are written as lightweight shell functions rather than standalone binaries, they must be sourced directly into your active session environment to be registered:

```bash
source add2bash.sh
source sh2txt.sh

```

---

## 💡 Real-World Use Case Scenarios

### Scenario A: Bootstrapping a Recursive Config Toolkit

Imagine you have a custom toolkit folder located at `~/scripts/` containing multiple separate shell files (`aliases.sh`, `docker-helpers.sh`, `git-hacks.sh`). These scripts can be organized into subfolders, mixed structures, or completely different cloned git repositories. Because `load_all.sh` runs recursively down your directory tree, everything gets gathered dynamically.

Instead of manual indexing inside your main profile, execute `add2bash` directly:

```bash
# 1. Navigate to your custom automation directory
cd ~/scripts/

# 2. Fire up the automatic generator
add2bash

```

If you skipped **Step 2** of the Quick Start and want to trigger the utility without executing it across your global profile yet, simply source the function container on the fly before running the generator:

```bash
# Alternate 2: Source the container directly to call the function instantly
source ~/scripts/shellutilities/add2bash.sh && add2bash

```

**What Happens Behind the Scenes:**

1. `add2bash` recognizes that no extra text arguments were passed.
2. It compiles a highly stable `load_all.sh` utility within that directory.
3. It prints a clear preview of the changes it wants to make to your `~/.bashrc`.
4. Once you approve the prompt (`y`), it adds a safe, single-line configuration hook.

If you want to temporarily disable a script (like `experimental.sh`), simply add it to a local exclusion list:

```bash
echo "experimental.sh" >> .scriptignore

```

The next time you open a terminal window, `load_all.sh` will skip that script entirely.

### Scenario B: Batch Preparing Scripts for LLM Prompt Analysis

When you need an AI tool to audit or refactor a group of scripts inside a project directory, use `sh2txt` to quickly generate text-friendly copies:

```bash
# Convert all .sh files inside a specific project folder
sh2txt ~/projects/legacy-automation/

```

This leaves your primary executable scripts untouched while creating matching `.txt` files right next to them, ready to be grouped or attached to your prompt window.

