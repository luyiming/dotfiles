function codex
    set -l root (git rev-parse --show-toplevel 2>/dev/null)

    # Skills that may have project-local copies.
    set -l common_skills \
        coding-guidelines \
        codebase-design \
        simplify \
        implement \
        research \
        code-review \
        commit-message \
        writing-for-agents \
        resolving-merge-conflicts

    set -l disabled_skills
    set -l disabled_skill_names

    if test -n "$root"; and test -d "$root/.agents/skills"
        for skill in $common_skills
            set -l project_skill "$root/.agents/skills/$skill/SKILL.md"
            set -l global_skill "$HOME/.agents/skills/$skill/SKILL.md"

            if test -f "$project_skill"; and test -f "$global_skill"
                set -a disabled_skills \
                    "{path=\"~/.agents/skills/$skill/SKILL.md\",enabled=false}"
                set -a disabled_skill_names $skill
            end
        end
    end

    if test (count $disabled_skills) -gt 0
        echo "Codex: shadowing global skills: "(string join ", " $disabled_skill_names)

        set -l config "skills.config=["(string join "," $disabled_skills)"]"
        command codex -c "$config" $argv
    else
        command codex $argv
    end
end
