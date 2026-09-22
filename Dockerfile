# ==============================================================================
# Dockerfile para execução do modelo MiniMax-H3 no SaladCloud (RTX 3090 - 24GB)
# Base: CUDA 12.4.1 Devel Ubuntu 22.04 + PyTorch 2.4/2.5 cu124 + ComfyUI
# ==============================================================================

FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

LABEL maintainer="Marlon <testarossa>"
LABEL description="Container ComfyUI otimizado para MiniMax-H3 (Ref2Video) no SaladCloud"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH} \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    COMFY_MODELS_DIR=/workspace/ComfyUI/models

# 1. Instala pacotes essenciais do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    wget \
    git \
    git-lfs \
    aria2 \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    ninja-build \
    ca-certificates \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 2. Instala PyTorch, TorchVision, TorchAudio compatíveis com CUDA 12.4
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 3. Instala huggingface_hub com hf_transfer para downloads multi-gigabit
RUN python3 -m pip install --no-cache-dir "huggingface-hub[hf_transfer]"

# 4. Instala SageAttention para acelerar inferência na arquitetura Ampere (RTX 3090)
RUN python3 -m pip install --no-cache-dir sageattention || true

# 5. Clona e configura o ComfyUI (versão recente com suporte nativo a MiniMax-H3)
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI && \
    cd /workspace/ComfyUI && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# 6. Instala Nós Customizados Essenciais
WORKDIR /workspace/ComfyUI/custom_nodes

# 6.1 ComfyUI-Manager (gerenciamento e utilitários)
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git ComfyUI-Manager && \
    cd ComfyUI-Manager && \
    python3 -m pip install --no-cache-dir -r requirements.txt || true

# 6.2 ComfyUI-VideoHelperSuite (necessário para manipulação, mux e preview de vídeos)
RUN git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git ComfyUI-VideoHelperSuite && \
    cd ComfyUI-VideoHelperSuite && \
    python3 -m pip install --no-cache-dir -r requirements.txt || true

# 6.3 ComfyUI-KJNodes (otimizações e suporte a SageAttention)
RUN git clone https://github.com/kijai/ComfyUI-KJNodes.git ComfyUI-KJNodes && \
    cd ComfyUI-KJNodes && \
    python3 -m pip install --no-cache-dir -r requirements.txt || true

# 6.4 Nó Customizado Local: Audio Duration (utilizado no seu workflow para sincronismo do áudio)
COPY custom_nodes/comfy-audio-duration /workspace/ComfyUI/custom_nodes/comfy-audio-duration

# 7. Copia scripts de download, entrypoint e workflows
WORKDIR /workspace
COPY scripts/ /workspace/scripts/
COPY workflows/ /workspace/workflows/

RUN chmod +x /workspace/scripts/*.sh /workspace/scripts/*.py && \
    python3 /workspace/scripts/patch_compatibility.py || true

# Porta padrão do ComfyUI
EXPOSE 8188

# Inicialização
ENTRYPOINT ["/workspace/scripts/entrypoint.sh"]

