"""
Testes para constantes e helpers globais do dashboard.
"""

from src.constants import (
    LABELS_DOENCA,
    PREFIXOS_ARQUIVO_DOENCA,
    mensagem_sem_dados_doenca,
    obter_icone_doenca,
    obter_nome_doenca,
    obter_prefixo_doenca,
)


def test_labels_doenca_contem_arboviroses_suportadas():
    assert LABELS_DOENCA["dengue"] == "🦟 Dengue"
    assert LABELS_DOENCA["chikungunya"] == "🤒 Chikungunya"
    assert LABELS_DOENCA["zika"] == "🧬 Zika"


def test_helpers_doenca_usam_fallback_seguro():
    assert obter_nome_doenca("zika") == "Zika"
    assert obter_icone_doenca("chikungunya") == "🤒"
    assert obter_prefixo_doenca("doenca-desconhecida") == PREFIXOS_ARQUIVO_DOENCA["dengue"]


def test_mensagem_sem_dados_explica_disponibilidade_limitada():
    mensagem = mensagem_sem_dados_doenca("zika")

    assert "Zika" in mensagem
    assert "disponibilidade limitada" in mensagem
    assert "API InfoDengue" in mensagem
