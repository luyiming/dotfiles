if command -q zoxide
    # j: smart directory jumping based on frecency
    # ji: interactive directory selection using fzf
    zoxide init fish --cmd j | source
end
