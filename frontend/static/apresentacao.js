// Guia por etapas: explicação à esquerda e função completa à direita.
const abas = Array.from(document.querySelectorAll('[role="tab"]'));
const paineis = Array.from(document.querySelectorAll('[role="tabpanel"]'));
const anterior = document.getElementById("anterior-aula");
const proxima = document.getElementById("proxima-aula");
const numero = document.getElementById("numero-aula");
let etapaAtual = 0;

function mostrarEtapa(indice, atualizarEndereco = true) {
    etapaAtual = indice;
    abas.forEach((aba, posicao) => {
        const selecionada = posicao === indice;
        aba.setAttribute("aria-selected", String(selecionada));
        aba.tabIndex = selecionada ? 0 : -1;
        paineis[posicao].hidden = !selecionada;
    });
    const codigo = paineis[indice].querySelector("pre");
    codigo.scrollTop = 0;
    codigo.scrollLeft = 0;
    numero.textContent = `${String(indice + 1).padStart(2, "0")} / ${String(abas.length).padStart(2, "0")}`;
    anterior.disabled = indice === 0;
    proxima.textContent = indice === abas.length - 1 ? "Voltar ao início ↻" : "Próxima etapa →";
    if (atualizarEndereco) {
        history.replaceState(null, "", `#${abas[indice].dataset.etapa}`);
    }
}

function indiceDoEndereco() {
    const antigos = { leitura: "csv", flask: "cardinalidade", "codigo-completo": "csv" };
    const hash = window.location.hash.slice(1);
    const etapa = antigos[hash] || hash;
    const indice = abas.findIndex(aba => aba.dataset.etapa === etapa);
    return indice < 0 ? 0 : indice;
}

abas.forEach((aba, indice) => {
    aba.addEventListener("click", () => mostrarEtapa(indice));
    aba.addEventListener("keydown", evento => {
        let destino;
        if (evento.key === "ArrowRight") destino = (indice + 1) % abas.length;
        if (evento.key === "ArrowLeft") destino = (indice + abas.length - 1) % abas.length;
        if (evento.key === "Home") destino = 0;
        if (evento.key === "End") destino = abas.length - 1;
        if (destino !== undefined) {
            evento.preventDefault();
            mostrarEtapa(destino);
            abas[destino].focus();
        }
    });
});

anterior.addEventListener("click", () => mostrarEtapa(Math.max(0, etapaAtual - 1)));
proxima.addEventListener("click", () => mostrarEtapa((etapaAtual + 1) % abas.length));
window.addEventListener("hashchange", () => mostrarEtapa(indiceDoEndereco(), false));
mostrarEtapa(indiceDoEndereco(), false);
