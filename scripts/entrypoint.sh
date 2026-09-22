#!/usr/bin/env bash
set -e

echo "=============================================================="
echo "    Iniciando Container ComfyUI - MiniMax-H3 (SaladCloud)    "
echo "    Otimizado para NVIDIA GeForce RTX 3090 (24GB VRAM)        "
echo "=============================================================="

COMFY_DIR="/workspace/ComfyUI"
PORT="${PORT:-8188}"
DOWNLOAD_MODELS="${DOWNLOAD_MODELS:-true}"

cd "${COMFY_DIR}"

# 1. Download dos modelos caso ativado e ainda não baixados
if [ "${DOWNLOAD_MODELS}" = "true" ]; then
    echo "[INFO] Verificando e baixando modelos do MiniMax-H3..."
    python3 /workspace/scripts/download_models.py
else
    echo "[INFO] DOWNLOAD_MODELS=false. Pulando verificação automática de modelos."
fi

# 2. Configura todos os workflows disponíveis nas pastas do ComfyUI
mkdir -p "${COMFY_DIR}/user/default/workflows"
if [ -d "/workspace/workflows" ]; then
    cp -u /workspace/workflows/*.json "${COMFY_DIR}/user/default/workflows/" 2>/dev/null || true
    echo "[INFO] Workflows carregados em: user/default/workflows/ :"
    ls -1 "${COMFY_DIR}/user/default/workflows"
fi

# 3. Cria arquivos de entrada de exemplo na pasta input/ se não existirem
# Isso evita erros visuais no carregamento inicial do canvas antes do usuário subir seus arquivos
mkdir -p "${COMFY_DIR}/input"
for dummy_img in "corpo_inteiro.jpeg" "perfil.jpeg" "Gemini_Generated_Image_5hsol35hsol35hso.jpeg"; do
    if [ ! -f "${COMFY_DIR}/input/${dummy_img}" ]; then
        # Gera uma imagem 512x512 em branco/cinza via python PIL
        python3 -c "from PIL import Image; img = Image.new('RGB', (512, 512), color=(180, 180, 180)); img.save('${COMFY_DIR}/input/${dummy_img}')" 2>/dev/null || true
    fi
done

if [ ! -f "${COMFY_DIR}/input/5.mp3" ]; then
    # Cria áudio mudo de 1s via ffmpeg se não existir
    ffmpeg -f lavfi -i "anullsrc=r=44100:cl=mono" -t 1 -q:a 9 -acodec libmp3lame "${COMFY_DIR}/input/5.mp3" -y 2>/dev/null || true
fi

# 4. Parâmetros de execução otimizados para RTX 3090:
# --disable-pinned-memory: CRUCIAL para evitar travamentos de OOM de RAM no Linux
# --highvram: Mantém tensores na VRAM durante a fase de amostragem
# --preview-method auto: Pré-visualização fluida de latents
EXTRA_ARGS=""
if [ -n "${CLI_ARGS}" ]; then
    EXTRA_ARGS="${CLI_ARGS}"
fi

echo "=============================================================="
echo " [INFO] ComfyUI pronto! Iniciando na porta ${PORT}..."
echo " [INFO] Acesse pelo Salad Container Gateway ou IP externo."
echo "=============================================================="

exec python3 main.py \
    --listen 0.0.0.0 \
    --port "${PORT}" \
    --disable-pinned-memory \
    --highvram \
    --preview-method auto \
    ${EXTRA_ARGS}

