"""
Router para endpoints de importação de alunos (processo multi-step)
"""
from fastapi import APIRouter, UploadFile, File, Body, Request
from app.services.alunos_service import AlunosService
from app.core.database import get_db_name_from_request
from typing import Dict, Any

router = APIRouter(prefix="/import/alunos", tags=["Importação de Alunos"])


@router.post("/step1")
async def import_alunos_step1(request: Request, file: UploadFile = File(...)):
    """
    Passo 1: Upload e validação inicial do arquivo CSV de alunos
    """
    # Extrair db_name do request
    db_name = get_db_name_from_request(request)

    content = await file.read()

    # Tenta decodificar com diferentes encodings
    file_content = None
    encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'windows-1252', 'latin1']

    for encoding in encodings:
        try:
            file_content = content.decode(encoding)
            print(f"✅ Arquivo decodificado com sucesso usando: {encoding}")
            break
        except UnicodeDecodeError:
            continue

    if file_content is None:
        return {
            "success": False,
            "message": "Não foi possível decodificar o arquivo. Certifique-se de que está em formato CSV válido.",
            "step": 1
        }

    return AlunosService.step1_upload_validacao(
        filename=file.filename,
        file_content=file_content,
        file_size=file.size,
        db_name=db_name
    )


@router.post("/step2")
async def import_alunos_step2(request: Request, request_data: Dict[str, Any] = Body(...)):
    """
    Passo 2: Validação do mapeamento de colunas
    """
    # Extrair db_name do request
    db_name = get_db_name_from_request(request)

    print(f"🔍 DEBUG ROUTER - Request data recebido: {request_data}")

    session_id = request_data.get("session_id")
    mapping = request_data.get("mapping") or request_data.get("mapeamento")

    print(f"🔍 DEBUG ROUTER - session_id: {session_id}")
    print(f"🔍 DEBUG ROUTER - mapping: {mapping}")

    return AlunosService.step2_validar_mapeamento(session_id, mapping, db_name)


@router.post("/step3")
async def import_alunos_step3(request: Request, request_data: dict = Body(...)):
    """
    Passo 3: Validação e detecção de conflitos
    """
    # Extrair db_name do request
    db_name = get_db_name_from_request(request)

    session_id = request_data.get("session_id")
    return AlunosService.step3_validar_detectar_conflitos(session_id, db_name)


@router.post("/step4")
async def import_alunos_step4(request: Request, request_data: dict = Body(...)):
    """
    Passo 4: Resolução de conflitos
    """
    # Extrair db_name do request
    db_name = get_db_name_from_request(request)

    session_id = request_data.get("session_id")
    conflict_resolutions = request_data.get("conflict_resolutions")
    return AlunosService.step4_resolver_conflitos(session_id, conflict_resolutions, db_name)


@router.post("/step5")
async def import_alunos_step5(request: Request, request_data: dict = Body(...)):
    """
    Passo 5: Importação final
    """
    # Extrair db_name do request
    db_name = get_db_name_from_request(request)

    session_id = request_data.get("session_id")
    return AlunosService.step5_importar_final(session_id, db_name)


@router.get("/status")
async def get_import_status(session_id: str):
    """
    Obtém o status de uma sessão de importação
    """
    return AlunosService.obter_status_importacao(session_id)

