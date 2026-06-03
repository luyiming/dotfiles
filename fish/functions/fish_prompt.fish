function fish_prompt --description "ys-like fish prompt"
    set -l last_status $status

    set -l normal (set_color --reset)

    # user color: root gets yellow background
    set -l user_part
    set -l suffix '$'
    if functions -q fish_is_root_user; and fish_is_root_user
        set user_part (set_color -b yellow)(set_color black)$USER$normal
        set suffix '#'
    else
        set user_part (set_color $fish_color_user)$USER$normal
    end

    # hostname
    set -l color_host $fish_color_host
    if set -q SSH_CONNECTION; and set -q fish_color_host_remote
        set color_host $fish_color_host_remote
    end
    set -l host_part (set_color $color_host)(prompt_hostname)$normal

    # cwd
    set -l cwd_part (set_color --bold $fish_color_cwd)(prompt_pwd)$normal

    # time
    set -l time_part " ["(date "+%H:%M:%S")"]"

    # command duration
    set -l cmd_duration (set_color green)(ys_cmd_duration)$normal

    # exit code
    # Only print status codes if the job failed.
    # SIGPIPE (141 = 128 + 13) is usually not a failure.
    set -l status_part
    if not contains -- $last_status 0 141
        set status_part " C:"(set_color $fish_color_status)(fish_status_to_signal $last_status)$normal
    end

    echo
    echo -n -s \
        (set_color --bold blue) "# " $normal \
        $user_part " @ " $host_part \
        " in " $cwd_part \
        (ys_git_prompt) \
        $time_part \
        $cmd_duration \
        $status_part

    echo
    echo -n -s (set_color --bold red) $suffix " " $normal
end
