function ys_git_prompt --description "Print a simple ys-like Git prompt"
    # Return silently when Git is not available.
    command -sq git; or return

    # Return silently when the current directory is not inside a Git work tree.
    command git rev-parse --is-inside-work-tree >/dev/null 2>&1; or return

    set -l normal (set_color --reset)
    set -l blue (set_color blue)
    set -l cyan (set_color cyan)
    set -l red (set_color red)
    set -l green (set_color green)

    # Prefer branch name. Fall back to a short commit hash for detached HEAD.
    set -l branch (
        command git symbolic-ref --quiet --short HEAD 2>/dev/null
        or command git rev-parse --short HEAD 2>/dev/null
    )

    # If we still cannot get a branch/hash, do not print anything.
    test -n "$branch"; or return

    # `git status --porcelain` is stable for scripts:
    # - empty output means clean
    # - non-empty output means dirty/staged/untracked/etc.
    set -l dirty
    if test -n "$(command git status --porcelain 2>/dev/null)"
        set dirty 1
    end

    # Match ys:
    #   clean:  on git:main o
    #   dirty:  on git:main x
    set -l state
    if test -n "$dirty"
        set state (set_color red)x
    else
        set state (set_color green)o
    end

    echo -n -s " on " (set_color cyan) $branch " " $state $normal
end
