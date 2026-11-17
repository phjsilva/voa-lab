// Monta apenas o texto da consulta. O cálculo dos conjuntos continua no Python.
const formulario = document.getElementById("form-consulta");

if (formulario) {
    const primeiro = document.getElementById("primeiro-filtro");
    const segundo = document.getElementById("segundo-filtro");
    const campoSegundo = document.getElementById("campo-segundo");
    const consulta = document.getElementById("consulta-enviada");
    const previa = document.getElementById("consulta-pronta");
    const explicacao = document.getElementById("explicacao-operacao");
    const descricoes = {
        "": "Mostra apenas as combinações do conjunto A.",
        e: "A ∩ B: mantém apenas as combinações presentes nos dois conjuntos.",
        ou: "A ∪ B: reúne as combinações dos dois conjuntos, sem repetir.",
        exceto: "A − B: retira de A as combinações que também estão em B.",
    };

    function atualizarConsulta() {
        const operador = formulario.querySelector('input[name="operador"]:checked').value;
        campoSegundo.hidden = !operador;
        segundo.disabled = !operador;
        consulta.value = "voos " + primeiro.value;
        if (operador) consulta.value += " " + operador + " " + segundo.value;
        previa.textContent = consulta.value;
        explicacao.textContent = descricoes[operador];
    }

    formulario.addEventListener("change", atualizarConsulta);
    atualizarConsulta();
}
