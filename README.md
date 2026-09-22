# Guia Completo: Rodando MiniMax-H3 no SaladCloud (RTX 3090 - 24GB)

Este repositório contém a infraestrutura Docker pronta e otimizada para executar o modelo omni-modal **MiniMax-H3 (Reference-to-Video com Áudio)** no **SaladCloud** (`portal.salad.com`) utilizando uma GPU **NVIDIA GeForce RTX 3090 (24 GB VRAM)**.

O setup foi preparado especificamente para o seu workflow com:
- **Nó `MiniMaxH3ReferenceToVideo`:** Criação de vídeo orientado por referências de imagem e áudio.
- **Turbo LoRA (4 passos):** Reduz o tempo de amostragem de ~20 passos para apenas 4 passos, gerando um clipe de alta qualidade em cerca de **2 a 4 minutos** na RTX 3090.
- **Nó `Audio Duration`:** Cálculo automático da duração em segundos a partir do áudio para sincronia labial e enquadramento exato.
- **Modelos quantizados oficiais (`INT8 / NVFP4 / FP16`):** Compatíveis com a arquitetura Ampere da RTX 3090.

---

## 1. Requisitos Críticos de Hardware no SaladCloud

Ao configurar o **Container Group** no [portal.salad.com](https://portal.salad.com/), defina as seguintes configurações de hardware:

| Recurso | Configuração Obrigatória | Motivo Técnico |
| :--- | :--- | :--- |
| **GPU** | **1x NVIDIA GeForce RTX 3090 (24 GB)** | Capacidade de VRAM ideal para o modelo de difusão quantizado. |
| **System RAM** | **60 GB RAM** | ⚠️ **CRÍTICO:** O modelo de difusão (~34 GB) e o Text Encoder (~16 GB) fazem *offloading* alternado na RAM do sistema. Configurar 30 GB ou menos causará travamento imediato por OOM (*Out Of Memory*). |
| **Container Disk** | **120 GB Storage** | Os modelos somam ~58 GB de download + sistema operacional base (~15 GB) + espaço temporário para latents e vídeos gerados. |
| **vCPU** | **4 a 8 vCPUs** | Processamento das etapas de VAE decode de vídeo e áudio e decodificação ffmpeg. |

---

## 2. Passo 1: Construir e Publicar a Imagem Docker

Você precisará de um repositório no **Docker Hub** ou **GitHub Container Registry (GHCR)** para onde enviará a imagem construída.

### No seu terminal local:

```bash
# 1. Acesse o diretório do projeto
cd /home/marlon/testarossa/container_h3

# 2. Faça login no seu registro (ex: Docker Hub)
docker login

# 3. Construa a imagem Docker
# Substitua 'seu-usuario' pelo seu nome de usuário no Docker Hub
docker build -t seu-usuario/comfyui-minimax-h3:latest .

# 4. Envie a imagem para o registro
docker push seu-usuario/comfyui-minimax-h3:latest
```

> **Nota:** A imagem construída tem aproximadamente 12 GB (inclui CUDA 12.4, PyTorch, ComfyUI, SageAttention e dependências). Os pesos pesados dos modelos (~58 GB) serão baixados automaticamente em ultra-alta velocidade pelo script de inicialização do container no SaladCloud.

---

## 3. Passo 2: Configurando o Container no SaladCloud Portal

Acesse o portal da Salad: [https://portal.salad.com/](https://portal.salad.com/)

### 3.1. Criando o Container Group
1. Clique em **Container Groups** > **Deploy Container Group**.
2. **Container Group Name:** Ex: `minimax-h3-rtx3090`.
3. **Replicas:** `1` (ou quantas réplicas desejar).

### 3.2. Imagem do Container
- **Image Source:** Selecione seu registro (Docker Hub ou Private Registry).
- **Image URL:** `seu-usuario/comfyui-minimax-h3:latest`.

### 3.3. Hardware e Recursos
- **GPU Class:** Marque **RTX 3090 (24 GB)**.
- **vCPU:** `4` ou `8 vCPU`.
- **Memory (RAM):** Selecione **60 GB**.
- **Allocated Storage (Disk Space):** Defina **120 GB**.

### 3.4. Variáveis de Ambiente (Environment Variables)
Adicione as seguintes variáveis:

| Nome da Variável | Valor Recomendado | Descrição |
| :--- | :--- | :--- |
| `DOWNLOAD_MODELS` | `true` | Ativa o download automatizado dos modelos do MiniMax-H3 no boot. |
| `HF_TOKEN` | `hf_xxxxxxxxxxxxxxxxxxxx` | *(Altamente recomendado)* Seu token do Hugging Face para garantir velocidade máxima e evitar limites de taxa de download. |
| `CLI_ARGS` | `--disable-pinned-memory --highvram` | Otimizações de gerenciamento de memória da GPU e RAM no Linux. |

### 3.5. Rede (Salad Container Gateway)
- Marque **Enable Networking**.
- **Port:** `8188`
- **Protocol:** `HTTP`
- **Server Timeout:** `600` segundos (10 minutos, para cobrir gerações de vídeo mais longas).
- **Authentication:**
  - Se você deseja abrir o ComfyUI diretamente no seu navegador, marque **Unauthenticated** (sem auth do Salad, permitindo acesso direto via link web).
  - Se optar por **Authenticated**, todas as requisições exigirão o cabeçalho `Salad-Api-Key: SUA_CHAVE`.

### 3.6. Health Probes (Readiness Probe)
Como o container baixa ~58 GB no primeiro boot (levando de 5 a 10 minutos dependendo da conexão do nó), a sonda de integridade deve aguardar o download terminar:

- **Protocol:** `HTTP`
- **Path:** `/`
- **Port:** `8188`
- **Initial Delay Seconds:** `600` (10 minutos de carência para o download dos modelos).
- **Period Seconds:** `15`
- **Timeout Seconds:** `5`
- **Failure Threshold:** `6`

Clique em **Deploy Container Group**.

---

## 4. Passo 3: Monitoramento do Boot e Acesso

1. Após clicar em Deploy, acesse a aba **Logs** da sua instância no SaladCloud.
2. Você verá o script `download_models.py` reportando o progresso do download via `hf_transfer`:
   ```text
   ==============================================================
     MiniMax-H3 Model Downloader for SaladCloud (RTX 3090)
     Target Directory: /workspace/ComfyUI/models
     HF_HUB_ENABLE_HF_TRANSFER: 1
   ==============================================================
   [1/5] Checking: minimax_h3_audio_vae_fp32.safetensors
   [2/5] Checking: minimax_h3_video_vae_fp16.safetensors
   [3/5] Checking: minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors
   [4/5] Checking: qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
   [5/5] Checking: minimax_h3_ref2va_pruned_int8_convrot.safetensors
   ```
3. Quando todos os modelos forem validados, o ComfyUI iniciará:
   ```text
   Starting server
   To see the GUI go to: http://0.0.0.0:8188
   ```
4. Na página do Container Group, copie a **Access Domain URL** fornecida pela Salad (ex: `https://xxxx-8188.salad.cloud`) e abra no seu navegador.

---

## 5. Passo 4: Executando seu Workflow no ComfyUI

1. Ao abrir o ComfyUI, seu workflow já estará disponível no menu:
   - Clique em **Workflows** > **MiniMax_H3_Ref2Video**
   *(Ou simplesmente arraste o arquivo `workflows/workflow_minimax_h3_ref2va.json` para dentro da tela do ComfyUI)*.
2. Na seção **User Inputs** (Grupo 5 do canvas):
   - Faça o upload das suas 3 imagens de referência nos nós `LoadImage`:
     - `corpo_inteiro.jpeg`
     - `perfil.jpeg`
     - `Gemini_Generated_Image_5hsol35hsol35hso.jpeg`
   - Faça o upload do arquivo de voz de áudio no nó `LoadAudio`:
     - `5.mp3`
   - O nó **Audio Duration** detectará a duração do áudio e calculará automaticamente a quantidade necessária de frames (`length`) no nó matemático.
3. Certifique-se de que o nó `Boolean (Enable Lightning LoRA)` está marcado como **`true`** (ativo para 4 passos).
4. Clique no botão **Queue Prompt**.
5. Em cerca de **2 a 4 minutos**, o vídeo gerado com áudio sincronizado aparecerá no nó `SaveVideo` e você poderá assistir e baixá-lo diretamente pelo navegador!

---

## 6. Modelos e Arquivos Baixados Automaticamente

| Tipo | Nome do Arquivo | Tamanho Aprox. |
| :--- | :--- | :--- |
| **Diffusion (UNet)** | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | ~34 GB |
| **Text Encoder** | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | ~15.7 GB |
| **Video VAE** | `minimax_h3_video_vae_fp16.safetensors` | ~5.2 GB |
| **Audio VAE** | `minimax_h3_audio_vae_fp32.safetensors` | ~605 MB |
| **LoRA Turbo** | `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` | ~2.8 GB |

Todos os arquivos são baixados do repositório oficial [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3).

