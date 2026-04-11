#!/bin/bash
# Claude Code Status Line Script
# Displays: skills, MCP, context, tokens, cost, model, branch

# ANSI color codes
BLUE='\033[34m'
GREEN='\033[32m'
YELLOW='\033[33m'
CYAN='\033[36m'
MAGENTA='\033[35m'
RED='\033[31m'
RESET='\033[0m'
BOLD='\033[1m'

# Read JSON input from stdin
input=$(cat)

# Extract values using jq
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
project_dir=$(echo "$input" | jq -r '.workspace.project_dir')
model_name=$(echo "$input" | jq -r '.model.display_name')
model_id=$(echo "$input" | jq -r '.model.id')
worktree_name=$(echo "$input" | jq -r '.worktree.name // empty')
worktree_branch=$(echo "$input" | jq -r '.worktree.branch // empty')
git_worktree=$(echo "$input" | jq -r '.workspace.git_worktree // empty')

# Context window information
context_used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
context_remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // empty')
total_output=$(echo "$input" | jq -r '.context_window.total_output_tokens // empty')

# Rate limits (if available)
rate_5h=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
rate_7d=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

# Output style
output_style=$(echo "$input" | jq -r '.output_style.name // empty')

# Vim mode
vim_mode=$(echo "$input" | jq -r '.vim.mode // empty')

# Agent info
agent_name=$(echo "$input" | jq -r '.agent.name // empty')

# Count skills (look for skill directories/files)
skills_count=0
skills_dir="$HOME/.claude/skills"
skills_list=""
if [ -d "$skills_dir" ]; then
    # Get all top-level skills (not sub-skills like phase files)
    skills_list=$(find "$skills_dir" -maxdepth 2 -name "skill.md" -o -name "SKILL.md" 2>/dev/null | \
        xargs -I {} dirname {} | \
        xargs -I {} basename {} | \
        sort | tr '\n' ' ')
    skills_count=$(echo "$skills_list" | wc -w | tr -d ' ')
fi

# Count MCP servers (check mcp.json or similar configs)
mcp_count=0
mcp_config="$HOME/.claude/mcp.json"
if [ -f "$mcp_config" ]; then
    mcp_count=$(jq '.mcpServers | length // 0' "$mcp_config" 2>/dev/null || echo "0")
fi

# Calculate cost in RMB (Chinese Yuan)
# Pricing per million tokens (as of 2025)
# Sonnet 4: Input ~$3/M, Output ~$15/M
# Sonnet 4.6: Input ~$3/M, Output ~$15/M (estimated)
# Exchange rate: 1 USD ≈ 7.2 CNY
cost_rmb=0
if [ -n "$total_input" ] && [ -n "$total_output" ] && [ "$total_input" != "null" ] && [ "$total_output" != "null" ]; then
    # Determine pricing based on model
    input_price_per_m=3    # USD per million input tokens
    output_price_per_m=15  # USD per million output tokens

    case "$model_id" in
        *opus*)
            input_price_per_m=15
            output_price_per_m=75
            ;;
        *haiku*)
            input_price_per_m=0.25
            output_price_per_m=1.25
            ;;
    esac

    # Calculate cost: (input_tokens / 1M * input_price) + (output_tokens / 1M * output_price)
    cost_usd=$(awk "BEGIN {printf \"%.4f\", ($total_input / 1000000 * $input_price_per_m) + ($total_output / 1000000 * $output_price_per_m)}")
    cost_rmb=$(awk "BEGIN {printf \"%.2f\", $cost_usd * 7.2}")
fi

# Build status line parts
parts=()

# Add model name (shortened) - Blue color
if [ -n "$model_name" ] && [ "$model_name" != "null" ]; then
    short_model=$(echo "$model_name" | sed 's/Claude //' | sed 's/ Sonnet//' | sed 's/ Opus//' | sed 's/ Haiku//')
    parts+=("${BLUE}${BOLD}Model:${RESET} ${BLUE}${short_model}${RESET}")
fi

# Add context window usage - Yellow/Red based on usage level
if [ -n "$context_remaining" ] && [ "$context_remaining" != "null" ]; then
    # Use different colors based on remaining context
    if [ "$context_remaining" -gt 50 ]; then
        color=$GREEN
    elif [ "$context_remaining" -gt 20 ]; then
        color=$YELLOW
    else
        color=$RED
    fi
    parts+=("${YELLOW}${BOLD}Context:${RESET} ${color}${context_remaining}% left${RESET}")
elif [ -n "$context_used" ] && [ "$context_used" != "null" ]; then
    # Use different colors based on used context
    if [ "$context_used" -lt 50 ]; then
        color=$GREEN
    elif [ "$context_used" -lt 80 ]; then
        color=$YELLOW
    else
        color=$RED
    fi
    parts+=("${YELLOW}${BOLD}Context:${RESET} ${color}${context_used}% used${RESET}")
fi

# Add skills count - Magenta color
if [ "$skills_count" -gt 0 ]; then
    parts+=("${MAGENTA}${BOLD}Skills:${RESET} ${MAGENTA}${skills_count}${RESET}")
fi

# Add MCP count - Cyan color
if [ "$mcp_count" -gt 0 ]; then
    parts+=("${CYAN}${BOLD}MCP:${RESET} ${CYAN}${mcp_count}${RESET}")
fi

# Add git branch information - Green color
if [ -n "$worktree_branch" ]; then
    parts+=("${GREEN}${BOLD}Git:${RESET} ${GREEN}${worktree_branch}${RESET}")
elif [ -n "$git_worktree" ]; then
    parts+=("${GREEN}${BOLD}Git:${RESET} ${GREEN}${git_worktree}${RESET}")
else
    # Try to get git branch from current directory
    if [ -d "$current_dir/.git" ] || git -C "$current_dir" rev-parse --git-dir > /dev/null 2>&1; then
        branch=$(git -C "$current_dir" --no-optional-locks branch --show-current 2>/dev/null)
        if [ -n "$branch" ]; then
            parts+=("${GREEN}${BOLD}Git:${RESET} ${GREEN}${branch}${RESET}")
        fi
    fi
fi

# Add token summary and cost if available - Cyan/Yellow color
if [ -n "$total_input" ] && [ -n "$total_output" ] && [ "$total_input" != "null" ] && [ "$total_output" != "null" ]; then
    # Format with K for thousands
    if [ "$total_input" -gt 1000 ]; then
        input_k=$((total_input / 1000))
        output_k=$((total_output / 1000))
        token_str="${CYAN}${input_k}K in / ${output_k}K out${RESET}"
    else
        token_str="${CYAN}${total_input} in / ${total_output} out${RESET}"
    fi

    # Add cost if available (more than 0.01 RMB)
    if [ -n "$cost_rmb" ] && [ "$(echo "$cost_rmb > 0.01" | awk '{print ($1 > 0.01)}')" -eq 1 ]; then
        token_str="${token_str} ${YELLOW}(¥${cost_rmb})${RESET}"
    fi

    parts+=("${CYAN}${BOLD}Tokens:${RESET} ${token_str}")
fi

# Add rate limits if available
if [ -n "$rate_5h" ] && [ "$rate_5h" != "null" ]; then
    if [ "$rate_5h" -gt 80 ]; then
        color=$RED
    elif [ "$rate_5h" -gt 60 ]; then
        color=$YELLOW
    else
        color=$GREEN
    fi
    parts+=("${color}${BOLD}5h:${RESET} ${color}${rate_5h}%${RESET}")
fi

if [ -n "$rate_7d" ] && [ "$rate_7d" != "null" ]; then
    if [ "$rate_7d" -gt 80 ]; then
        color=$RED
    elif [ "$rate_7d" -gt 60 ]; then
        color=$YELLOW
    else
        color=$GREEN
    fi
    parts+=("${color}${BOLD}7d:${RESET} ${color}${rate_7d}%${RESET}")
fi

# Add output style if not default
if [ -n "$output_style" ] && [ "$output_style" != "default" ] && [ "$output_style" != "null" ]; then
    parts+=("${MAGENTA}Style: ${output_style}${RESET}")
fi

# Add vim mode if active
if [ -n "$vim_mode" ] && [ "$vim_mode" != "null" ]; then
    parts+=("${BLUE}Vim: ${vim_mode}${RESET}")
fi

# Add agent name if active
if [ -n "$agent_name" ] && [ "$agent_name" != "null" ]; then
    parts+=("${YELLOW}Agent: ${agent_name}${RESET}")
fi

# Join all parts with separator
result=$(IFS='｜'; echo "${parts[*]}")

# Output the status line with colors
echo -e "$result"