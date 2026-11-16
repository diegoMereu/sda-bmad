#!/usr/bin/env bash
# Clona e tiene allineati i repository Corriere Espresso elencati in repo-ce.tsv.
#
#   bash contesto/avvio/clona-repo-ce.sh            clona i repo che mancano
#   bash contesto/avvio/clona-repo-ce.sh --stato    branch, avanti/indietro, modifiche locali
#   bash contesto/avvio/clona-repo-ce.sh --aggiorna fetch di tutti + fast-forward dei repo puliti
#   bash contesto/avvio/clona-repo-ce.sh --elenca   repo nuovi su GitLab/GHE non ancora in repo-ce.tsv
#
# Radice locale: variabile CE_ROOT (default $HOME/gitposte/SDA).
# Credenziali: quelle di Git Credential Manager (nessun segreto in questo file).
# --elenca usa GITLAB_TOKEN (PAT GitLab con scope read_api) e, per GHE, GHE_TOKEN
# oppure il token che Git Credential Manager ha gia' per posteitaliane.ghe.com.
set -u
QUI="$(cd "$(dirname "$0")" && pwd)"
ELENCO="$QUI/repo-ce.tsv"
ROOT="${CE_ROOT:-$HOME/gitposte/SDA}"
export GIT_TERMINAL_PROMPT=0

righe() { tr -d '\r' < "$ELENCO" | grep -v '^#' | grep -v '^$'; }

clona() {
  local ok=0 ko=0 gia=0
  while IFS=$'\t' read -r origine url dest; do
    if [ -d "$ROOT/$dest/.git" ]; then gia=$((gia+1)); continue; fi
    mkdir -p "$(dirname "$ROOT/$dest")"
    if git clone -q "$url" "$ROOT/$dest"; then echo "clonato  $dest"; ok=$((ok+1))
    else echo "ERRORE   $dest ($origine)"; ko=$((ko+1)); fi
  done < <(righe)
  echo "gia' presenti: $gia, clonati: $ok, errori: $ko"
}

stato() {
  while IFS=$'\t' read -r _ _ dest; do
    local d="$ROOT/$dest"
    [ -d "$d/.git" ] || { echo "MANCA    $dest"; continue; }
    local b ab mod
    b=$(git -C "$d" branch --show-current)
    ab=$([ -n "$b" ] && git -C "$d" rev-list --left-right --count "$b...origin/$b" 2>/dev/null | tr '\t' '/')
    mod=$(git -C "$d" status --porcelain | wc -l | tr -d ' ')
    printf '%-75s %-14s avanti/indietro=%-7s modifiche=%s\n' "$dest" "${b:-(detached)}" "${ab:-n.d.}" "$mod"
  done < <(righe)
}

aggiorna() {
  while IFS=$'\t' read -r _ _ dest; do
    local d="$ROOT/$dest"
    [ -d "$d/.git" ] || continue
    git -C "$d" fetch -q --all --prune || { echo "fetch KO $dest"; continue; }
    local b; b=$(git -C "$d" branch --show-current)
    if [ -z "$b" ] || [ -n "$(git -C "$d" status --porcelain)" ]; then
      echo "saltato  $dest (detached o con modifiche locali)"; continue
    fi
    git -C "$d" merge -q --ff-only "origin/$b" 2>/dev/null || echo "no ff    $dest ($b divergente o senza upstream)"
  done < <(righe)
}

elenca() {
  local tmp; tmp=$(mktemp -d)
  if [ -n "${GITLAB_TOKEN:-}" ]; then
    for p in 1 2 3; do
      curl -s -k -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "https://gitlab.alm.poste.it/api/v4/groups/CORRIERE-ESPRESSO/projects?include_subgroups=true&per_page=100&page=$p" > "$tmp/gl$p.json"
    done
  else
    echo "GITLAB_TOKEN non impostato: salto GitLab"
  fi
  local tok="${GHE_TOKEN:-}"
  if [ -z "$tok" ]; then
    tok=$(printf 'protocol=https\nhost=posteitaliane.ghe.com\n\n' | GCM_INTERACTIVE=never git credential fill 2>/dev/null | sed -n 's/^password=//p')
  fi
  if [ -n "$tok" ]; then
    for p in 1 2 3 4 5 6; do
      curl -s -H "Authorization: Bearer $tok" "https://api.posteitaliane.ghe.com/orgs/SVILUPPO/repos?per_page=100&page=$p" > "$tmp/gh$p.json"
    done
  else
    echo "nessun token GHE: salto GitHub Enterprise"
  fi
  python -I - "$tmp" "$ELENCO" <<'EOF'
import glob, json, os, sys
tmp, elenco = sys.argv[1], sys.argv[2]
noti = {l.split('\t')[1].strip().lower().removesuffix('.git') for l in open(elenco, encoding='utf-8') if l.strip() and not l.startswith('#')}
nuovi = []
for f in glob.glob(os.path.join(tmp, '*.json')):
    try:
        dati = json.load(open(f, encoding='utf-8'))
    except ValueError:
        continue
    if not isinstance(dati, list):
        continue
    for r in dati:
        url = r.get('http_url_to_repo') or r.get('clone_url')
        nome = r.get('path_with_namespace') or r.get('name')
        if os.path.basename(f).startswith('gh') and not nome.startswith('CORRIERE-ESPRESSO_'):
            continue
        if url and url.lower().removesuffix('.git') not in noti:
            nuovi.append(f"{nome}\t{url}")
print("\n".join(sorted(nuovi)) if nuovi else "nessun repo nuovo")
EOF
  rm -rf "$tmp"
}

case "${1:-}" in
  --stato) stato ;;
  --aggiorna) aggiorna ;;
  --elenca) elenca ;;
  "") clona ;;
  *) sed -n '2,12p' "$0" ;;
esac
