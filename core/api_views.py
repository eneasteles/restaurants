from ninja import Router
from restaurants.models import CardPayment

router = Router()

@router.get("/teste/")
def teste(request):
    return {"ok": True}
