# fiscal/utils/nfce.py
# fiscal/utils/nfce.py
from pynfe.entidades.emitente import Emitente
from pynfe.entidades.cliente import Cliente
from pynfe.entidades.notafiscal import NotaFiscal
from pynfe.processamento.comunicacao import ComunicacaoSefaz
from pynfe.processamento.assinatura import AssinaturaA1
from pynfe.processamento.serializacao import SerializacaoXML
from pynfe.utils.flags import CODIGO_BRASIL

from decimal import Decimal
import datetime



def emitir_nfce(cert_path, senha, estado='SP', ambiente=2):
    ws = ComunicacaoSefaz(
        certificado_arquivo=cert_path,
        senha=senha,
        estado=estado,
        ambiente=ambiente
    )

    # Emitente
    emitente = Emitente(
        cnpj='00000000000191',
        razao_social='EMPRESA TESTE',
        nome_fantasia='LOJA TESTE',
        endereco='Rua Exemplo',
        numero='123',
        bairro='Centro',
        municipio='São Paulo',
        uf='SP',
        cep='01001000',
        telefone='1130000000',
        csc='SEU_CSC',
        csc_id='000001'
    )

    # Destinatário (opcional para NFC-e)
    destinatario = Destinatario()

    # Produtos
    produto = Produto(
        codigo='001',
        descricao='Produto Teste',
        ncm='61099000',
        cfop='5102',
        unidade='UN',
        quantidade=1,
        valor_unitario=100.00,
        icms_situacao='102',
        icms_origem='0',
        pis_situacao='07',
        cofins_situacao='07'
    )

    detalhe = Detalhe(produto=produto)

    # Totais
    totais = Totais()
    totais.valor_produtos = 100.00
    totais.valor_total_nfe = 100.00

    # Pagamento
    pagamento = Pagamento()
    pagamento.valor_pagamento = 100.00

    # Montar NFe
    nfe = NFe(
        emitente=emitente,
        destinatario=destinatario,
        detalhes=[detalhe],
        totais=totais,
        pagamento=pagamento
    )

    xml = nfe.xml()
    xml_assinado = assinar_xml(xml, cert_path, senha)
    resposta = ws.enviar_nfe(xml_assinado)

    return resposta
