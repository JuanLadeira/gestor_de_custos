# Issues

## Obsidian CLI Installation Problem

**Status:** ✅ RESOLVIDO — Instalar via `.deb` em vez de snap (ver solução abaixo)

**Issue:** O comando `obsidian` encerrava imediatamente com exit code 1 sem output visível.

**Causa Raiz Identificada:**
Dois problemas combinados com o snap do Obsidian no WSL2:

1. **MESA/GPU error** — O Electron dentro do snap não consegue inicializar o contexto gráfico:
   ```
   MESA: error: ZINK: failed to choose pdev
   glx: failed to create drisw screen
   ```
   O log real pode ser visto em `~/.config/obsidian/obsidian.log`.

2. **Snap sandbox** — O confinamento do snap intercepta flags como `--help` e `--disable-gpu` antes de repassá-las ao Electron, impedindo workarounds.

**Como foi diagnosticado:**
- Rodado `/snap/obsidian/current/obsidian` diretamente (bypassing o wrapper snap) revelou os logs de erro em stderr
- O app carregava o ASAR e verificava updates com sucesso, mas morria ao tentar criar a janela GUI
- `LIBGL_ALWAYS_SOFTWARE=1` e `--disable-gpu` foram tentados mas bloqueados pelo sandbox

**Solução:**

```bash
# 1. Baixar o .deb oficial (sem sandbox restritivo)
wget https://github.com/obsidianmd/obsidian-releases/releases/download/v1.12.4/obsidian_1.12.4_amd64.deb -O /tmp/obsidian.deb

# 2. Remover o snap
sudo snap remove obsidian

# 3. Instalar o .deb
sudo dpkg -i /tmp/obsidian.deb
sudo apt-get install -f -y  # instalar dependências se necessário

# 4. Verificar
obsidian --version
```

**Vault do projeto:** `custos/` (já criado na raiz do repositório)
