// -----------------------------------------------
// CONFIGURAÃ‡ÃƒO â€” troque pela URL do seu servidor
// em produÃ§Ã£o. Em desenvolvimento local use
// http://10.0.2.2:5000 (emulador Android)
// ou o IP da sua mÃ¡quina ex: http://192.168.1.10:5000
// -----------------------------------------------
const API_BASE = "http://192.168.15.5:5000";


// -----------------------------------------------
// Modal de Tutorial
// -----------------------------------------------
function abrirModal() {
  document.getElementById("modal-tutorial").style.display = "flex";
}

function fecharModal() {
  document.getElementById("modal-tutorial").style.display = "none";
}

// -----------------------------------------------
// Troca de abas
// -----------------------------------------------
function setTab(tab) {
  document.getElementById("modo-link").style.display    = tab === "link"    ? "block" : "none";
  document.getElementById("modo-arquivo").style.display = tab === "arquivo" ? "block" : "none";
  document.getElementById("modo-audio").style.display   = tab === "audio"   ? "block" : "none";

  document.getElementById("tab-link").classList.toggle("active",    tab === "link");
  document.getElementById("tab-arquivo").classList.toggle("active", tab === "arquivo");
  document.getElementById("tab-audio").classList.toggle("active",   tab === "audio");
}

// -----------------------------------------------
// Mostra ou esconde o loading
// -----------------------------------------------
function showLoading(visivel, texto) {
  const el = document.getElementById("loading");
  if (el) el.style.display = visivel ? "block" : "none";
  const textoEl = document.getElementById("loading-texto");
  if (textoEl && texto) textoEl.textContent = texto;
}

// -----------------------------------------------
// Mostra mensagem de erro
// -----------------------------------------------
function showError(mensagem) {
  const el = document.getElementById("erro");
  if (!el) { alert(mensagem); return; }
  el.textContent = mensagem;
  el.style.display = "block";
}

// -----------------------------------------------
// Mostra o resultado na tela
// -----------------------------------------------
function renderResult(data) {
  const resultado = document.getElementById("resultado");
  if (!resultado) return;

  const isIA = data.e_ia;
  const modoAudio = data.modo === "audio";

  const icon = document.getElementById("res-icon");
  const svg  = document.getElementById("res-svg");
  icon.className = "result-icon " + (isIA ? "ia" : "real");

  if (isIA) {
    svg.innerHTML = '<circle cx="11" cy="11" r="8" stroke="#f05c5c" stroke-width="1.5"/><path d="M11 7v5" stroke="#f05c5c" stroke-width="1.5" stroke-linecap="round"/><circle cx="11" cy="15" r="1" fill="#f05c5c"/>';
  } else {
    svg.innerHTML = '<circle cx="11" cy="11" r="8" stroke="#4cd97b" stroke-width="1.5"/><path d="M7.5 11l2.5 2.5 4.5-4.5" stroke="#4cd97b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>';
  }

  document.getElementById("res-veredito").textContent = isIA ? "Provavelmente gerado por IA" : "Parece conte\u00FAdo real";
  document.getElementById("res-confianca").textContent = "Confian\u00E7a " + data.confianca;
  document.getElementById("res-probabilidade").className  = "num " + (isIA ? "ia" : "real");
  document.getElementById("res-probabilidade").textContent = data.probabilidade_ia + "%";
  document.getElementById("res-video").textContent        = modoAudio ? "N/A" : data.score_video + "%";
  document.getElementById("res-audio").textContent        = data.score_audio === "N/A" ? "N/A" : data.score_audio + "%";
  document.getElementById("res-frames").textContent       = modoAudio ? "N/A" : data.frames_analisados;

  resultado.style.display = "block";
}

// -----------------------------------------------
// Limpa erros e resultado anterior
// -----------------------------------------------
function limparTela() {
  document.getElementById("erro").style.display      = "none";
  document.getElementById("resultado").style.display = "none";
}

// -----------------------------------------------
// FunÃ§Ã£o genÃ©rica de fetch com tratamento de erro
// -----------------------------------------------
async function enviarRequisicao(endpoint, opcoes) {
  const res = await fetch(API_BASE + endpoint, opcoes);
  if (!res.ok) {
    const erro = await res.json().catch(() => ({}));
    throw new Error(erro.erro || "Erro do servidor: " + res.status);
  }
  return res.json();
}

// -----------------------------------------------
// Conecta os botÃµes ao carregar a pÃ¡gina
// -----------------------------------------------
document.addEventListener("DOMContentLoaded", () => {

  // BotÃµes de tutorial
  ["help-btn-link", "help-btn-arquivo", "help-btn-audio"].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.addEventListener("click", abrirModal);
  });

  // Fechar modal pelo X
  const fechar = document.getElementById("modal-fechar");
  if (fechar) fechar.addEventListener("click", fecharModal);

  // Fechar modal clicando fora
  const overlay = document.getElementById("modal-tutorial");
  if (overlay) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) fecharModal();
    });
  }

  // BotÃµes de limpar
  document.querySelectorAll(".clean-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const urlInput   = document.getElementById("video-url");
      const fileInput  = document.getElementById("file-input");
      const audioInput = document.getElementById("audio-input");
      if (urlInput)   urlInput.value  = "";
      if (fileInput)  fileInput.value = "";
      if (audioInput) audioInput.value = "";
      limparTela();
    });
  });

  // â”€â”€ BotÃ£o de link â”€â”€
  document.getElementById("analyze-btn").addEventListener("click", async () => {
    const url = document.getElementById("video-url").value.trim();
    if (!url) { showError("Por favor, insira um link de vi­deo."); return; }

    limparTela();
    const btn = document.getElementById("analyze-btn");
    btn.disabled = true;
    showLoading(true, "Analisando vi­deo...");

    try {
      const data = await enviarRequisicao("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });
      renderResult(data);
    } catch (err) {
      showError("Erro ao analisar: " + err.message);
    } finally {
      btn.disabled = false;
      showLoading(false);
    }
  });

  // â”€â”€ BotÃ£o de arquivo MP4 â”€â”€
  document.getElementById("analyze-file-btn").addEventListener("click", async () => {
    const input = document.getElementById("file-input");
    if (!input.files[0]) { showError("Selecione um arquivo de vi­deo."); return; }

    limparTela();
    const formData = new FormData();
    formData.append("file", input.files[0]);

    const btn = document.getElementById("analyze-file-btn");
    btn.disabled = true;
    showLoading(true, "Analisando vi­deo...");

    try {
      const data = await enviarRequisicao("/analyze-file", {
        method: "POST",
        body: formData
      });
      renderResult(data);
    } catch (err) {
      showError("Erro ao analisar: " + err.message);
    } finally {
      btn.disabled = false;
      showLoading(false);
    }
  });

  // â”€â”€ BotÃ£o de Ã¡udio â”€â”€
  document.getElementById("analyze-audio-btn").addEventListener("click", async () => {
    const input = document.getElementById("audio-input");
    if (!input.files[0]) { showError("Selecione um arquivo de Ã¡udio."); return; }

    limparTela();
    const formData = new FormData();
    formData.append("file", input.files[0]);

    const btn = document.getElementById("analyze-audio-btn");
    btn.disabled = true;
    showLoading(true, "Analisando audio...");

    try {
      const data = await enviarRequisicao("/analyze-audio", {
        method: "POST",
        body: formData
      });
      renderResult(data);
    } catch (err) {
      showError("Erro ao analisar: " + err.message);
    } finally {
      btn.disabled = false;
      showLoading(false);
    }
  });

  // Registra o Service Worker para PWA
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(err => {
      console.log("Service Worker nÃ£o registrado:", err);
    });
  }

});



