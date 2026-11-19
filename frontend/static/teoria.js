// Os mesmos seis elementos acompanham a explicação inteira.
(() => {
    const abas = Array.from(document.querySelectorAll('.trilha [role="tab"]'));
    const paineis = abas.map((aba) => document.getElementById(aba.getAttribute('aria-controls')));
    const anterior = document.getElementById('teoria-anterior');
    const proxima = document.getElementById('teoria-proxima');
    const posicao = document.getElementById('teoria-posicao');
    let atual = 0;

    function mostrar(indice, atualizarEndereco = true, focar = false) {
        atual = indice;
        abas.forEach((aba, i) => {
            aba.setAttribute('aria-selected', String(i === atual));
            aba.tabIndex = i === atual ? 0 : -1;
            paineis[i].hidden = i !== atual;
        });
        anterior.disabled = atual === 0;
        proxima.textContent = atual === abas.length - 1 ? 'Recomeçar' : 'Próxima etapa';
        posicao.textContent = `${atual + 1} de ${abas.length}`;
        if (atualizarEndereco) history.replaceState(null, '', `#${abas[atual].dataset.etapa}`);
        if (focar) abas[atual].focus();
    }

    function lerEndereco() {
        const indice = abas.findIndex((aba) => `#${aba.dataset.etapa}` === window.location.hash);
        mostrar(indice < 0 ? 0 : indice, false);
    }

    abas.forEach((aba, indice) => aba.addEventListener('click', () => mostrar(indice)));
    anterior.addEventListener('click', () => mostrar(Math.max(0, atual - 1)));
    proxima.addEventListener('click', () => mostrar((atual + 1) % abas.length));
    document.addEventListener('keydown', (evento) => {
        if (evento.altKey || evento.ctrlKey || evento.metaKey || evento.shiftKey) return;
        if (evento.target.closest('input, textarea, select, [contenteditable="true"], details')) return;
        const naTrilha = evento.target.closest('.trilha');
        let destino;
        if (evento.key === 'ArrowRight') destino = Math.min(atual + 1, abas.length - 1);
        if (evento.key === 'ArrowLeft') destino = Math.max(atual - 1, 0);
        if (naTrilha && evento.key === 'Home') destino = 0;
        if (naTrilha && evento.key === 'End') destino = abas.length - 1;
        if (destino === undefined) return;
        evento.preventDefault();
        mostrar(destino, true, Boolean(naTrilha));
    });
    window.addEventListener('hashchange', lerEndereco);
    lerEndereco();

    // Cada linha já está no HTML; os passos revelam a conversão de texto em tabela.
    const arquivos = Array.from(document.querySelectorAll('[data-arquivo-csv]'));
    const paineisCsv = Array.from(document.querySelectorAll('[data-csv-painel]'));
    const passosLidos = Object.fromEntries(arquivos.map((botao) => [botao.dataset.arquivoCsv, 0]));
    const lerLinha = document.getElementById('ler-linha-csv');
    const reiniciar = document.getElementById('reiniciar-csv');
    const estadoLeitura = document.getElementById('estado-leitura-csv');
    let arquivoAtual = 'companhias';

    function atualizarLeitura() {
        arquivos.forEach((botao) => botao.setAttribute('aria-pressed', String(botao.dataset.arquivoCsv === arquivoAtual)));
        paineisCsv.forEach((painel) => { painel.hidden = painel.dataset.csvPainel !== arquivoAtual; });
        const painel = paineisCsv.find((item) => item.dataset.csvPainel === arquivoAtual);
        const lidos = passosLidos[arquivoAtual];
        const linhas = Array.from(painel.querySelectorAll('[data-linha-csv]'));
        const terminou = lidos === linhas.length;
        linhas.forEach((linha, i) => {
            linha.classList.toggle('linha-ativa', i === lidos - 1);
            linha.classList.toggle('linha-lida', i < lidos);
        });
        painel.querySelector('[data-espera-csv]').hidden = lidos > 0;
        painel.querySelector('[data-tabela-csv]').hidden = lidos === 0;
        painel.querySelector('[data-vazio-csv]').hidden = lidos > 1;
        painel.querySelectorAll('[data-destino-csv]').forEach((destino) => {
            const indice = Number(destino.dataset.destinoCsv);
            destino.hidden = indice >= lidos;
            destino.classList.toggle('linha-ativa', indice === lidos - 1);
        });
        lerLinha.disabled = terminou;
        lerLinha.textContent = terminou ? 'Arquivo lido' : lidos === 0 ? 'Ler cabeçalho' : 'Ler próxima linha';
        reiniciar.disabled = lidos === 0;
        if (lidos === 0) estadoLeitura.textContent = 'Nenhuma linha lida.';
        else if (lidos === 1) estadoLeitura.textContent = 'Linha 1: o cabeçalho virou os nomes das colunas.';
        else estadoLeitura.textContent = `Linha ${lidos}: cada valor ocupou sua coluna. ${lidos - 1} de ${linhas.length - 1} linhas de dados lidas.${terminou ? ' Tabela completa.' : ''}`;
    }

    arquivos.forEach((botao) => botao.addEventListener('click', () => {
        arquivoAtual = botao.dataset.arquivoCsv;
        atualizarLeitura();
    }));
    lerLinha.addEventListener('click', () => {
        const painel = paineisCsv.find((item) => item.dataset.csvPainel === arquivoAtual);
        passosLidos[arquivoAtual] = Math.min(passosLidos[arquivoAtual] + 1, painel.querySelectorAll('[data-linha-csv]').length);
        atualizarLeitura();
    });
    reiniciar.addEventListener('click', () => { passosLidos[arquivoAtual] = 0; atualizarLeitura(); });
    atualizarLeitura();

    const botoesJuncao = Array.from(document.querySelectorAll('[data-juntar]'));
    botoesJuncao.forEach((botao) => botao.addEventListener('click', () => {
        const companhia = botao.dataset.juntar;
        botoesJuncao.forEach((outro) => outro.setAttribute('aria-pressed', String(outro === botao)));
        document.querySelectorAll('[data-origem-companhia]').forEach((linha) => {
            linha.classList.toggle('linha-ativa', companhia === 'todas' || linha.dataset.origemCompanhia === companhia);
        });
        document.querySelectorAll('[data-resultado-companhia]').forEach((linha) => {
            linha.hidden = companhia !== 'todas' && linha.dataset.resultadoCompanhia !== companhia;
        });
        document.getElementById('estado-juncao').textContent = companhia === 'todas'
            ? '2 companhias em SJC × 3 turnos em SJC = 6 combinações: V1 a V6.'
            : companhia === 'latam' ? 'Latam em SJC encontra 3 turnos: V1, V2 e V3.'
                : 'Azul em SJC encontra 3 turnos: V4, V5 e V6.';
    }));
})();
