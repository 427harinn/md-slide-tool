_slidegen_completion() {
  local cur prev cmd
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  cmd="${COMP_WORDS[1]}"

  local commands="new list-templates"

  if [[ ${COMP_CWORD} -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
    return
  fi

  case "${cmd}" in
    new)
      case "${prev}" in
        --type)
          local types
          types=$(find /work/templates -mindepth 1 -maxdepth 1 -type d -printf "%f\n" 2>/dev/null)
          COMPREPLY=( $(compgen -W "${types}" -- "${cur}") )
          return
          ;;
        --template)
          local selected_type=""
          local i

          for (( i=0; i<${#COMP_WORDS[@]}; i++ )); do
            if [[ "${COMP_WORDS[i]}" == "--type" && $((i+1)) -lt ${#COMP_WORDS[@]} ]]; then
              selected_type="${COMP_WORDS[i+1]}"
              break
            fi
          done

          if [[ -z "${selected_type}" ]]; then
            return
          fi

          if [[ -d "/work/templates/${selected_type}" ]]; then
            local templates
            templates=$(find "/work/templates/${selected_type}" -maxdepth 1 -type f -name "*.qmd" -printf "%f\n" 2>/dev/null | sed 's/\.qmd$//')
            COMPREPLY=( $(compgen -W "${templates}" -- "${cur}") )
          fi
          return
          ;;
      esac

      if [[ "${cur}" == --* ]]; then
        COMPREPLY=( $(compgen -W "--type --template --help" -- "${cur}") )
        return
      fi
      ;;
  esac
}

complete -F _slidegen_completion slidegen