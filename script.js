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

  document.getElementById("res-veredito").textContent     = isIA ? "Provavelmente gerado por IA" : "Parece conteúdo real";
  document.getElementById("res-confianca").textContent    = "Confiança " + data.confianca;
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
// Conecta os botões ao carregar a página
// -----------------------------------------------
document.addEventListener("DOMContentLoaded", () => {

  // Botão de link
  document.getElementById("analyze-btn").addEventListener("click", async () => {
    const url = document.getElementById("video-url").value.trim();
    if (!url) { showError("Por favor, insira um link de vídeo."); return; }

    limparTela();
    const btn = document.getElementById("analyze-btn");
    btn.disabled = true;
    showLoading(true, "Analisando vídeo...");

    try {
      const res = await fetch("http://127.0.0.1:5000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url })
      });

      if (!res.ok) {
        const erro = await res.json();
        throw new Error(erro.erro || "Erro do servidor: " + res.status);
      }

      let data;
      try { data = await res.json(); }
      catch { throw new Error("O servidor retornou uma resposta inválida."); }

      renderResult(data);

    } catch (err) {
      showError("Erro ao analisar: " + err.message);
      console.error("Detalhe do erro:", err);
    } finally {
      btn.disabled = false;
      showLoading(false);
    }
  });


  // Botão de arquivo MP4
  document.getElementById("analyze-file-btn").addEventListener("click", async () => {
    const input = document.getElementById("file-input");
    if (!input.files[0]) { showError("Selecione um arquivo de vídeo."); return; }

    limparTela();
    const formData = new FormData();
    formData.append("file", input.files[0]);

    const btn = document.getElementById("analyze-file-btn");
    btn.disabled = true;
    showLoading(true, "Analisando vídeo...");

    try {
      const res = await fetch("http://127.0.0.1:5000/analyze-file", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const erro = await res.json();
        throw new Error(erro.erro || "Erro do servidor: " + res.status);
      }

      let data;
      try { data = await res.json(); }
      catch { throw new Error("O servidor retornou uma resposta inválida."); }

      renderResult(data);

    } catch (err) {
      showError("Erro ao analisar: " + err.message);
      console.error("Detalhe do erro:", err);
    } finally {
      btn.disabled = false;
      showLoading(false);
    }
  });


  // Botão de áudio
  document.getElementById("analyze-audio-btn").addEventListener("click", async () => {
    const input = document.getElementById("audio-input");
    if (!input.files[0]) { showError("Selecione um arquivo de áudio."); return; }

    limparTela();
    const formData = new FormData();
    formData.append("file", input.files[0]);

    const btn = document.getElementById("analyze-audio-btn");
    btn.disabled = true;
    showLoading(true, "Analisando áudio...");

    try {
      const res = await fetch("http://127.0.0.1:5000/analyze-audio", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const erro = await res.json();
        throw new Error(erro.erro || "Erro do servidor: " + res.status);
      }

      let data;
      try { data = await res.json(); }
      catch { throw new Error("O servidor retornou uma resposta inválida."); }

      renderResult(data);

    } catch (err) {
      showError("Erro ao analisar: " + err.message);
      console.error("Detalhe do erro:", err);
    } finally {
      btn.disabled = false;
      showLoading(false);
    }
  });

});
