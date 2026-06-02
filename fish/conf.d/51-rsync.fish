# Recursively copy files and directories, preserving permissions, timestamps, and symbolic links. Compression is enabled for faster transfers. Progress is displayed in a human-readable format.
abbr -a rcp "rsync -avzhP"

# Same as rcp, but removes the source files after a successful transfer (effectively performing a move).
abbr -a rmv "rsync -avzhP --remove-source-files"

# Performs bidirectional-style sync: updates files from the source and deletes files in the destination that no longer exist in the source. Useful for directory synchronization.
abbr -a rmir "rsync -avzhP --delete"
