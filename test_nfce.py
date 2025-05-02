from pynfe.entidades.notafiscal import NotaFiscal
from pynfe.entidades.emitente import Emitente
from pynfe.entidades.cliente import Cliente
from pynfe.entidades.produto import Produto
from pynfe.processamento.serializador import Serializador

# Criar nota fiscal
nf = NotaFiscal()
nf.uf = 'SP'
nf.numero_nf = 1
nf.serie = 1
nf.modelo = '65'  # NFC-e
nf.tipo_documento = 'saida'
nf.natureza_operacao = 'VENDA'
nf.data_emissao = '2024-01-01T10:00:00'
nf.data_saida_entrada = '2024-01-01T10:00:00'
nf.finalidade_emissao = 'normal'
nf.forma_emissao = 'normal'
nf.tipo_impressao_danfe = 'sem_danfe'
nf.indicador_presencial = 'presencial'
nf.cliente_final = True
nf.tipo_pagamento = 'avista'
nf.indicador_destino = 'interna'

# Emitente (empresa emissora)
emitente = Emitente()
emitente.CNPJ = '12345678000195'
emitente.xNome = 'Restaurante Teste Ltda'
emitente.xFant = 'Restaurante Teste'
emitente.IE = '1234567890'
emitente.IM = '987654321'
emitente.CRT = 'simples'

# Endereço do emitente (via atributos diretos)
emitente.xLgr = 'Rua Central'
emitente.nro = '100'
emitente.xBairro = 'Centro'
emitente.cMun = '3550308'  # Código IBGE São Paulo
emitente.xMun = 'São Paulo'
emitente.UF = 'SP'
emitente.CEP = '01000000'
emitente.cPais = '1058'
emitente.xPais = 'Brasil'
emitente.fone = '11999999999'

nf.emitente = emitente

# Cliente (destinatário) – pode ser consumidor final
cliente = Cliente()
cliente.CPF = '12345678909'
cliente.xNome = 'Consumidor Final'

nf.destinatario_remetente = cliente

# Produto
produto = Produto()
produto.cProd = '001'
produto.xProd = 'Refeição Completa'
produto.NCM = '21069090'
produto.CFOP = '5102'
produto.uCom = 'UN'
produto.qCom = 1
produto.vUnCom = 20.00
produto.uTrib = 'UN'
produto.qTrib = 1
produto.vUnTrib = 20.00
produto.indTot = 1
produto.vProd = 20.00
produto.vDesc = 0.00
produto.vFrete = 0.00
produto.vOutro = 0.00
produto.orig = '0'
produto.CST = '102'  # Simples Nacional, CSOSN
produto.pICMS = 0.00

nf.adicionar_produto_servico(produto)

# Pagamento
nf.adicionar_pagamento(
    meio_pagamento='01',  # 01 = Dinheiro
    valor=20.00
)

# Gerar XML
print("✅ Nota criada com sucesso, gerando XML...")
serializador = Serializador()
xml_string = serializador.exportar(nf)

# Exibir XML
print(xml_string)
