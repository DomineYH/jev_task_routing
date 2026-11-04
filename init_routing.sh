#!/usr/bin/env bash
# init_routing.sh — install and verify jev_task_routing in the current project.
#
# Run from the project root:
#   bash init_routing.sh                      # auto-detect harness
#   bash init_routing.sh --harness claude     # force CLAUDE.md
#   bash init_routing.sh --harness agents     # force AGENTS.md (codex / agy / opencode / others)
#   bash init_routing.sh --harness both
#   bash init_routing.sh --ping               # also smoke-test the Jev endpoint (needs TYPESAFE_API_KEY)
#   bash init_routing.sh --source /path/or/url --ref main --no-auth-check
#
# Exit codes: 0 ok · 1 verification failed · 2 not a git repo · 3 git auth · 4 download · 5 missing dependency

set -euo pipefail

REPO_URL="https://github.com/DomineYH/jev_task_routing.git"
REF=""
HARNESS=""
PING=0
AUTH_CHECK=1
DEST=".routing"
POLICY_FILES=(jev_task_routing.json jev_task_routing.schema.json models.json models.schema.json resolve_models.py ROUTING_POLICY.md verify_routing.py AGENTS_ROUTING.md repo_checks.example.json hooks/jev_order9_guard.py hooks/hooks.example.json)
HOOK_SCOPE="user"
HOOK_SCOPE_SET=0
UNINSTALL_HOOKS=0
MARK_START="<!-- jev-routing:start"
MARK_END="<!-- jev-routing:end -->"

c_red=$'\033[31m'; c_grn=$'\033[32m'; c_yel=$'\033[33m'; c_dim=$'\033[2m'; c_off=$'\033[0m'
info()  { printf '%s==>%s %s\n' "$c_grn" "$c_off" "$*"; }
warn()  { printf '%s[WARN]%s %s\n' "$c_yel" "$c_off" "$*"; }
die()   { local code=$1; shift; printf '%s[ERROR]%s %s\n' "$c_red" "$c_off" "$*" >&2; exit "$code"; }

usage() {
  cat <<'EOF'
init_routing.sh — install and verify jev_task_routing in the current project.

Run from the project root:
  bash init_routing.sh                      # auto-detect harness
  bash init_routing.sh --harness claude     # force CLAUDE.md
  bash init_routing.sh --harness agents     # force AGENTS.md (codex / agy / opencode / others)
  bash init_routing.sh --harness both
  bash init_routing.sh --ping               # also smoke-test the Jev endpoint (needs TYPESAFE_API_KEY)
  bash init_routing.sh --source /path/or/url --ref main --no-auth-check
  bash init_routing.sh --hooks user|project|local|none   # Claude Code ORDER-9 guard hook scope (default: user)
  bash init_routing.sh --uninstall-hooks                  # remove the guard from all three scopes

Exit codes: 0 ok · 1 verification failed · 2 not a git repo · 3 git auth · 4 download · 5 missing dependency
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)   REPO_URL="$2"; shift 2 ;;
    --ref)      REF="$2"; shift 2 ;;
    --harness)  HARNESS="$2"; shift 2 ;;
    --ping)     PING=1; shift ;;
    --no-auth-check) AUTH_CHECK=0; shift ;;
    --hooks)    HOOK_SCOPE="$2"; HOOK_SCOPE_SET=1; shift 2 ;;
    --uninstall-hooks) UNINSTALL_HOOKS=1; shift ;;
    -h|--help)  usage ;;
    *) die 1 "unknown option: $1 (see --help)" ;;
  esac
done

PROJECT="$(pwd -P)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ---------------------------------------------------------------- 0. dependencies
info "0/6 Checking dependencies"
for bin in git python3; do
  command -v "$bin" >/dev/null 2>&1 || die 5 "'$bin' is required but not found in PATH"
done
PYV="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die 5 "python3 >= 3.8 required (found $PYV)"
printf '%s    git %s · python %s%s\n' "$c_dim" "$(git --version | awk '{print $3}')" "$PYV" "$c_off"

# ---------------------------------------------------------------- 1. git repo + auth
info "1/6 Checking git repository and authentication"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  cat >&2 <<EOF
${c_red}This directory is not a git repository.${c_off}
Run the following first, then re-run this script:

    git init
    git add -A && git commit -m "initial commit"
EOF
  exit 2
fi
ROOT="$(git rev-parse --show-toplevel)"
[[ "$ROOT" == "$PROJECT" ]] || warn "running in a subdirectory; installing into repository root: $ROOT"
PROJECT="$ROOT"; cd "$PROJECT"

IS_LOCAL_SOURCE=0
[[ -d "$REPO_URL" || "$REPO_URL" == file://* ]] && IS_LOCAL_SOURCE=1

if [[ $AUTH_CHECK -eq 1 && $IS_LOCAL_SOURCE -eq 0 ]]; then
  if ! GIT_TERMINAL_PROMPT=0 git ls-remote --exit-code "$REPO_URL" HEAD >/dev/null 2>&1; then
    printf '%sCannot reach %s with the current git credentials.%s\n' "$c_red" "$REPO_URL" "$c_off" >&2
    if command -v gh >/dev/null 2>&1; then
      if gh auth status >/dev/null 2>&1; then
        cat >&2 <<'EOF'
gh is logged in but git is not using its credentials. Run:

    gh auth setup-git

EOF
      else
        cat >&2 <<'EOF'
Authenticate GitHub CLI and connect it to git, then re-run:

    gh auth login
    gh auth setup-git

EOF
      fi
    else
      cat >&2 <<'EOF'
Set up git authentication for GitHub, then re-run. Either:

    # HTTPS with a credential helper (stores a personal access token)
    git config --global credential.helper store   # or: osxkeychain / manager
    git ls-remote https://github.com/DomineYH/jev_task_routing.git   # enter token when prompted

    # or SSH
    ssh-keygen -t ed25519 && cat ~/.ssh/id_ed25519.pub   # add to GitHub → Settings → SSH keys
    bash init_routing.sh --source git@github.com:DomineYH/jev_task_routing.git

(If the repository is public and this still fails, check your network/proxy.)
EOF
    fi
    exit 3
  fi
  printf '%s    remote reachable: %s%s\n' "$c_dim" "$REPO_URL" "$c_off"
else
  printf '%s    auth check skipped%s\n' "$c_dim" "$c_off"
fi

# ---------------------------------------------------------------- 2. download
info "2/6 Downloading policy files"
if [[ $IS_LOCAL_SOURCE -eq 1 && -d "$REPO_URL" && ! -d "$REPO_URL/.git" && ! -f "$REPO_URL/HEAD" ]]; then
  cp -R "$REPO_URL/." "$TMP/src"           # plain directory
else
  CLONE_ARGS=(--depth 1 --quiet)
  [[ -n "$REF" ]] && CLONE_ARGS+=(--branch "$REF")
  GIT_TERMINAL_PROMPT=0 git clone "${CLONE_ARGS[@]}" "$REPO_URL" "$TMP/src" 2>"$TMP/clone.err" \
    || die 4 "git clone failed: $(tr '\n' ' ' <"$TMP/clone.err")"
fi
SRC="$TMP/src"
for f in "${POLICY_FILES[@]}"; do
  [[ -f "$SRC/$f" ]] || die 4 "source is missing required file: $f"
done
SRC_COMMIT="$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || echo local)"
printf '%s    source revision: %s%s\n' "$c_dim" "$SRC_COMMIT" "$c_off"

# ---------------------------------------------------------------- 3. install
info "3/6 Installing into $DEST/"
mkdir -p "$DEST/tasks"
for f in jev_task_routing.json jev_task_routing.schema.json models.schema.json resolve_models.py ROUTING_POLICY.md verify_routing.py repo_checks.example.json; do
  if [[ -f "$DEST/$f" ]] && ! cmp -s "$SRC/$f" "$DEST/$f"; then
    cp "$DEST/$f" "$DEST/$f.bak"; warn "updated $DEST/$f (previous copy saved as $f.bak)"
  fi
  cp "$SRC/$f" "$DEST/$f"
done
chmod +x "$DEST/verify_routing.py" "$DEST/resolve_models.py"
# models.json is user-edited: create once, keep an always-fresh example beside it
cp "$SRC/models.json" "$DEST/models.example.json"
if [[ -f "$DEST/models.json" ]]; then
  cmp -s "$SRC/models.json" "$DEST/models.json" || warn "kept your $DEST/models.json; shipped defaults changed — diff against $DEST/models.example.json"
else
  cp "$SRC/models.json" "$DEST/models.json"; printf '%s    created %s/models.json (edit to change role models)%s\n' "$c_dim" "$DEST" "$c_off"
fi
mkdir -p "$DEST/evidence"
# migrate versioned config names from <= 2.5.0
for old in "$DEST"/jev_task_routing_v*.json; do
  [[ -f "$old" ]] || continue
  mv "$old" "$old.bak"; warn "renamed legacy $(basename "$old") -> $(basename "$old").bak (config is now version-agnostic jev_task_routing.json)"
done
[[ -f "$DEST/repo_checks.json" ]] || { cp "$SRC/repo_checks.example.json" "$DEST/repo_checks.json"; warn "created $DEST/repo_checks.json from example — edit it for this repository"; }
touch "$DEST/tasks/.gitkeep"

# .gitignore: task records are local state
GI_LINE="$DEST/tasks/*.json"
GI_LINE2="$DEST/evidence/*.json"
if [[ ! -f .gitignore ]] || ! grep -qxF "$GI_LINE" .gitignore; then
  printf '\n# jev_task_routing: local task records\n%s\n' "$GI_LINE" >> .gitignore
  printf '%s    added "%s" to .gitignore%s\n' "$c_dim" "$GI_LINE" "$c_off"
fi
if ! grep -qxF "$GI_LINE2" .gitignore; then printf '%s\n' "$GI_LINE2" >> .gitignore; fi

POLICY_VERSION="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["version"])' "$DEST/jev_task_routing.json")"
write_installed() {
python3 - "$DEST/INSTALLED.json" "$POLICY_VERSION" "$REPO_URL" "$SRC_COMMIT" "$1" <<'PY'
import json, sys, datetime
json.dump({"policy_version": sys.argv[2], "source": sys.argv[3], "source_revision": sys.argv[4],
           "installed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "shadow_mode": True, "hook_scope": sys.argv[5]}, open(sys.argv[1], "w"), indent=2)
PY
}
write_installed "pending"
printf '%s    policy version %s%s\n' "$c_dim" "$POLICY_VERSION" "$c_off"

# ---------------------------------------------------------------- 4. harness instructions
info "4/6 Writing agent instructions"
detect_harness() {
  if [[ -n "${CLAUDECODE:-}" || -f CLAUDE.md || -d .claude ]]; then echo claude; return; fi
  if [[ -f AGENTS.md || -f .codex/config.toml || -f codex.toml || -f opencode.json || -d .agy ]]; then echo agents; return; fi
  if [[ -t 0 && -t 1 ]]; then
    read -r -p "Do you use Claude Code in this project? [y/N] " ans
    [[ "$ans" =~ ^[Yy] ]] && { echo claude; return; }
  fi
  echo agents
}
[[ -n "$HARNESS" ]] || HARNESS="$(detect_harness)"
case "$HARNESS" in
  claude) TARGETS=(CLAUDE.md) ;;
  agents|codex|agy|opencode|other) TARGETS=(AGENTS.md) ;;
  both)   TARGETS=(CLAUDE.md AGENTS.md) ;;
  *) die 1 "unknown --harness '$HARNESS' (claude | agents | both)" ;;
esac

install_block() {  # idempotent: replace the marked block, or append it
  local target="$1" block="$2"
  python3 - "$target" "$block" "$MARK_START" "$MARK_END" <<'PY'
import sys, pathlib
target, block_path, ms, me = sys.argv[1:5]
block = pathlib.Path(block_path).read_text(encoding="utf-8").rstrip("\n") + "\n"
p = pathlib.Path(target)
if p.exists():
    text = p.read_text(encoding="utf-8")
    i, j = text.find(ms), text.find(me)
    if i != -1 and j != -1 and j > i:
        text = text[:i] + block + text[j + len(me):].lstrip("\n")
        action = "updated"
    else:
        text = text.rstrip("\n") + "\n\n" + block
        action = "appended to"
else:
    text = f"# {p.stem}\n\n" + block
    action = "created"
p.write_text(text, encoding="utf-8")
print(f"    {action} {target}")
PY
}
for t in "${TARGETS[@]}"; do install_block "$t" "$SRC/AGENTS_ROUTING.md"; done
printf '%s    harness: %s%s\n' "$c_dim" "$HARNESS" "$c_off"

# ---------------------------------------------------------------- 4b. Claude Code ORDER-9 guard hook
case "$HOOK_SCOPE" in user|project|local|none) ;; *) die 1 "unknown --hooks '$HOOK_SCOPE' (user | project | local | none)" ;; esac
mkdir -p "$DEST/hooks"
cp "$SRC/hooks/jev_order9_guard.py" "$DEST/hooks/jev_order9_guard.py"; chmod +x "$DEST/hooks/jev_order9_guard.py"
cp "$SRC/hooks/hooks.example.json" "$DEST/hooks/hooks.example.json"
[[ -f "$DEST/hooks.json" ]] || { cp "$SRC/hooks/hooks.example.json" "$DEST/hooks.json"; printf '%s    created %s/hooks.json (mode=deny)%s\n' "$c_dim" "$DEST" "$c_off"; }
GI_LINE3="$DEST/hook_log.jsonl"
grep -qxF "$GI_LINE3" .gitignore || printf '%s\n' "$GI_LINE3" >> .gitignore

hook_settings_path() {
  case "$1" in
    user)    echo "$HOME/.claude/settings.json" ;;
    project) echo "$PROJECT/.claude/settings.json" ;;
    local)   echo "$PROJECT/.claude/settings.local.json" ;;
  esac
}
hook_command() {
  case "$1" in
    user)    echo 'python3 "$HOME/.claude/hooks/jev_order9_guard.py"' ;;
    *)       echo 'python3 "$CLAUDE_PROJECT_DIR/.routing/hooks/jev_order9_guard.py"' ;;
  esac
}
merge_hook() {  # $1 settings path, $2 command, $3 add|remove
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys, pathlib
path, cmd, action = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
MARK = "jev_order9_guard"
settings = {}
if path.exists():
    try:
        settings = json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError as e:
        sys.exit(f"cannot parse {path}: {e} — fix it or choose another --hooks scope")
hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
pre[:] = [e for e in pre if not any(MARK in (h.get("command") or "") for h in e.get("hooks", []))]
if action == "add":
    pre.append({"matcher": "Agent|Task", "hooks": [{"type": "command", "command": cmd, "timeout": 10}]})
if not pre:
    hooks.pop("PreToolUse", None)
if not hooks:
    settings.pop("hooks", None)
if action == "remove" and not settings and not path.exists():
    sys.exit(0)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"    {'registered' if action == 'add' else 'removed'} ORDER-9 guard hook {'in' if action == 'add' else 'from'} {path}")
PY
}

if [[ $UNINSTALL_HOOKS -eq 1 ]]; then
  info "4b/6 Removing ORDER-9 guard hook from all scopes"
  for sc in user project local; do p="$(hook_settings_path "$sc")"; [[ -f "$p" ]] && merge_hook "$p" "" remove; done
  HOOK_SCOPE="none"
elif [[ "$HOOK_SCOPE" != "none" ]]; then
  if [[ "$HARNESS" == "agents" && $HOOK_SCOPE_SET -eq 0 ]]; then
    HOOK_SCOPE="none"
    printf '%s    harness is not Claude Code; skipping Claude Code hook (pass --hooks <scope> to force)%s\n' "$c_dim" "$c_off"
  else
    info "4b/6 Registering Claude Code ORDER-9 guard hook (scope: $HOOK_SCOPE)"
    if [[ "$HOOK_SCOPE" == "user" ]]; then
      mkdir -p "$HOME/.claude/hooks"
      cp "$SRC/hooks/jev_order9_guard.py" "$HOME/.claude/hooks/jev_order9_guard.py"; chmod +x "$HOME/.claude/hooks/jev_order9_guard.py"
      printf '%s    copied guard to %s/.claude/hooks/ (applies to every project that has .routing/)%s\n' "$c_dim" "$HOME" "$c_off"
    fi
    merge_hook "$(hook_settings_path "$HOOK_SCOPE")" "$(hook_command "$HOOK_SCOPE")" add
    # avoid double registration: drop our entry from the other scopes
    for sc in user project local; do
      [[ "$sc" == "$HOOK_SCOPE" ]] && continue
      p="$(hook_settings_path "$sc")"; [[ -f "$p" ]] && grep -q jev_order9_guard "$p" && merge_hook "$p" "" remove
    done
  fi
fi

write_installed "$HOOK_SCOPE"

# ---------------------------------------------------------------- 5. python deps for verification
info "5/6 Checking Python packages for verification"
if ! python3 -c 'import jsonschema' 2>/dev/null; then
  warn "'jsonschema' not installed; trying to install"
  python3 -m pip install --quiet --user jsonschema 2>/dev/null \
    || python3 -m pip install --quiet --break-system-packages jsonschema 2>/dev/null \
    || warn "could not install jsonschema automatically — run: pip install jsonschema (schema validation will be skipped)"
fi
if [[ $PING -eq 1 ]] && ! python3 -c 'import requests' 2>/dev/null; then
  python3 -m pip install --quiet --user requests 2>/dev/null \
    || python3 -m pip install --quiet --break-system-packages requests 2>/dev/null \
    || warn "could not install requests — --ping will be skipped"
fi

# ---------------------------------------------------------------- 6. verify
info "6/6 Verifying installation"
VERIFY_ARGS=(--project "$PROJECT")
[[ $PING -eq 1 ]] && VERIFY_ARGS+=(--ping)
set +e
python3 "$DEST/verify_routing.py" "${VERIFY_ARGS[@]}"
RC=$?
set -e

echo
if [[ $RC -eq 0 ]]; then
  cat <<EOF
${c_grn}Installation complete.${c_off}
  Policy   : $DEST/jev_task_routing.json  (v$POLICY_VERSION, source $SRC_COMMIT)
  Models   : $DEST/models.json  (edit this to change harness/model/effort per role)
  Hook     : ORDER-9 guard scope=$HOOK_SCOPE  (config: $DEST/hooks.json, log: $DEST/hook_log.jsonl)
  Rules    : $DEST/ROUTING_POLICY.md
  Agents   : ${TARGETS[*]}  (block between jev-routing markers)
  Records  : $DEST/tasks/ and $DEST/evidence/   (git-ignored)

Next steps:
  1. Edit $DEST/repo_checks.json to match your CI, and $DEST/models.json for role models
     (check: python3 $DEST/resolve_models.py).
  2. export TYPESAFE_API_KEY=...   then: python3 $DEST/verify_routing.py --ping
  3. Run in SHADOW MODE for 30–50 real tasks before enabling dispatch (see README).
  4. git add $DEST ${TARGETS[*]} .gitignore && git commit -m "chore: install jev_task_routing v$POLICY_VERSION"
EOF
else
  printf '%sInstallation finished but verification FAILED (exit %s). Fix the [FAIL] items above and re-run:%s\n  python3 %s/verify_routing.py\n' "$c_red" "$RC" "$c_off" "$DEST"
  exit 1
fi
