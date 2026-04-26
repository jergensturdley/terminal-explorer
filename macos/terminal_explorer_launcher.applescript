on launchExplorer(itemPaths)
    set bundlePath to POSIX path of (path to me)
    set binaryPath to bundlePath & "Contents/Resources/terminal-explorer-macos"
    set commandText to "exec " & quoted form of binaryPath

    repeat with itemPath in itemPaths
        set commandText to commandText & space & quoted form of itemPath
    end repeat

    set launcherPath to do shell script "/usr/bin/mktemp -t terminal-explorer-XXXXXX.command"
    set launcherScript to "#!/bin/zsh" & linefeed & "clear" & linefeed & commandText & linefeed

    set launcherFile to open for access POSIX file launcherPath with write permission
    try
        set eof launcherFile to 0
        write launcherScript to launcherFile
    end try
    close access launcherFile

    do shell script "/bin/chmod +x " & quoted form of launcherPath
    do shell script "/usr/bin/open -a Terminal " & quoted form of launcherPath
end launchExplorer

on run
    my launchExplorer({})
end run

on open droppedItems
    set itemPaths to {}
    repeat with droppedItem in droppedItems
        set end of itemPaths to POSIX path of droppedItem
    end repeat
    my launchExplorer(itemPaths)
end open