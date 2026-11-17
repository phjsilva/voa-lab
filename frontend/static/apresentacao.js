// Guia por etapas: explicação à esquerda e função completa à direita.
const abas = Array.from(document.querySelectorAll('[role="tab"]'));
const paineis = Array.from(document.querySelectorAll('[role="tabpanel"]'));
const anterior = document.getElementById("anterior-aula");
const proxima = document.getElementById("proxima-aula");
const numero = document.getElementById("numero-aula");
let etapaAtual = 0;

// Colore o código já recebido do Python, sem interpretar ou executar seu conteúdo.
const palavrasPython = new Set([
    "def", "return", "if", "else", "elif", "for", "in", "not", "and", "or",
    "try", "except", "raise", "from", "import", "as", "with", "while", "break",
]);

document.querySelectorAll(".texto-codigo").forEach(elemento => {
    const texto = elemento.textContent;
    const partes = /#[^\n]*|""".*?"""|'''.*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b\d+\b|\b[a-zA-Z_]\w*\b/g;
    const fragmento = document.createDocumentFragment();
    let fim = 0;
    for (const parte of texto.matchAll(partes)) {
        const palavra = parte[0];
        const inicio = parte.index;
        fragmento.append(document.createTextNode(texto.slice(fim, inicio)));
        let classe = "";
        if (palavra.startsWith("#")) classe = "comentario";
        else if (palavra.startsWith('"') || palavra.startsWith("'")) classe = "texto";
        else if (palavrasPython.has(palavra)) classe = "palavra";
        else if (["True", "False", "None"].includes(palavra)) classe = "constante";
        else if (/^\d/.test(palavra)) classe = "numero";
        else if (texto.slice(inicio + palavra.length).trimStart().startsWith("(")) classe = "funcao";

        const trecho = document.createElement("span");
        trecho.textContent = palavra;
        if (classe) trecho.className = `sintaxe-${classe}`;
        fragmento.append(trecho);
        fim = inicio + palavra.length;
    }
    fragmento.append(document.createTextNode(texto.slice(fim)));
    elemento.replaceChildren(fragmento);
});

function focarCodigo(ativo) {
    document.body.classList.toggle("codigo-em-foco", ativo);
    document.querySelectorAll(".focar-codigo").forEach(botao => {
        botao.setAttribute("aria-pressed", String(ativo));
        botao.textContent = ativo ? "Voltar à explicação ↙" : "Ampliar código ↗";
    });
}

document.querySelectorAll(".focar-codigo").forEach(botao => {
    botao.addEventListener("click", () => {
        focarCodigo(!document.body.classList.contains("codigo-em-foco"));
    });
});

document.querySelectorAll(".copiar-codigo").forEach(botao => {
    botao.addEventListener("click", async () => {
        const bloco = botao.closest(".bloco-codigo");
        const aviso = bloco.querySelector(".aviso-codigo");
        const linhas = Array.from(bloco.querySelectorAll(".texto-codigo"));
        const texto = linhas.map(linha => linha.textContent).join("\n");
        try {
            await navigator.clipboard.writeText(texto);
            aviso.textContent = "Código copiado, sem a numeração das linhas.";
        } catch {
            aviso.textContent = "Não foi possível copiar. Selecione o código e use Ctrl+C.";
        }
    });
});

document.addEventListener("keydown", evento => {
    if (evento.key === "Escape") focarCodigo(false);
});

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
