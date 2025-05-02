from django.shortcuts import render
from django.http import JsonResponse
from .utils.nfce import emitir_nfce
from restaurants.models import CardPayment
from .utils.emissao import emitir_nfce_cardpayment


def emitir_nfce_view(request):
    resposta = emitir_nfce(
        cert_path='/caminho/do/seu/certificado.pfx',
        senha='sua-senha',
        estado='SP',  # ou outro estado
        ambiente=2  # 2 = homologação, 1 = produção
    )

    return JsonResponse(resposta.dict())

# fiscal/views.py



# fiscal/views.py

def emitir_nfce(request, pk):
    pagamento = CardPayment.objects.get(pk=pk)
    restaurante = pagamento.restaurant

    cert_path = restaurante.certificate_file.path
    senha = restaurante.certificate_password
    ambiente = 2 if restaurante.emit_nfce else 1  # ou deixe sempre 2 para homologação

    resposta = emitir_nfce_cardpayment(pagamento, cert_path, senha, ambiente)

    return JsonResponse(resposta.dict())



