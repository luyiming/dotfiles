# Same as fish's default fish_title, minus the [hostname] prefix over SSH.
function fish_title
    # Add the path only when not inside tmux
    set -l pwd
    set -q TMUX; or set pwd (prompt_pwd -d 1 -D 1)

    if set -q argv[1]
        echo -- (string sub -l 20 -- $argv[1]) $pwd
    else
        # Don't print "fish" because it's redundant
        set -l command (status current-command)
        if test "$command" = fish
            set command
        end
        echo -- (string sub -l 20 -- $command) $pwd
    end
end