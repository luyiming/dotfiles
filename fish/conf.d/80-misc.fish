# Disk usage summary, sorted ascending
abbr -a dus --set-cursor "du -sh % | sort -h"

function last_history_item
    echo $history[1]
end
abbr -a !! --position anywhere --function last_history_item

function multicd
    echo cd (string repeat -n (math (string length -- $argv[1]) - 1) ../)
end
abbr --add dotdot --regex '^\.\.+$' --function multicd
