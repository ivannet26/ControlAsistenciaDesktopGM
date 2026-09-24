from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import schemas
from database import get_db
from equipo_models import Etiqueta
from security import get_usuario_actual


router = APIRouter(
    prefix="/etiquetas",
    tags=["Etiquetas"]
)


# ============================================================
# LISTAR ETIQUETAS
# ============================================================

@router.get(
    "",
    response_model=list[schemas.EtiquetaSimple]
)
def listar_etiquetas(
    estado: str = "activo",
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_actual)
):
    """
    Lista las etiquetas del sistema.
    
    - estado=activo (default): solo etiquetas no archivadas
    - estado=archivado: solo etiquetas archivadas
    - estado=todo: todas las etiquetas
    """

    query = db.query(Etiqueta)

    if estado == "activo":
        query = query.filter(Etiqueta.archivado == False)
    elif estado == "archivado":
        query = query.filter(Etiqueta.archivado == True)
    # estado == "todo" → sin filtro

    return query.order_by(Etiqueta.nombre.asc()).all()