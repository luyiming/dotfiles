function ys_cmd_duration
    set -l ms $CMD_DURATION

    # Only show durations >= 1 second.
    test $ms -ge 1000; or return

    if test $ms -lt 60000
        printf " %.1fs" (math "$ms / 1000")
        return
    end

    set -l total_sec (math --scale=0 "$ms / 1000")

    if test $total_sec -lt 3600
        set -l min (math --scale=0 "$total_sec / 60")
        set -l sec (math --scale=0 "$total_sec % 60")
        printf " %dm%02ds" $min $sec
        return
    end

    set -l hour (math --scale=0 "$total_sec / 3600")
    set -l min (math --scale=0 "($total_sec % 3600) / 60")
    printf " %dh%02dm" $hour $min
end
