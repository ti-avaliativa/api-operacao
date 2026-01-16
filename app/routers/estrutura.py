"""
Router para endpoints de importação de estrutura (Escola, Série, Turma)
"""
from fastapi import APIRouter, UploadFile, File, Request
from app.services.estrutura_service import EstruturaService
from app.core.database import get_db_name_from_request

router = APIRouter(prefix="/{db}/import", tags=["Importação de Estrutura"])


@router.post("/completo")
async def import_completo(db: str, request: Request, file: UploadFile = File(...), dry_run: bool = False):
    """
    Importa escola, série e turma de uma só vez a partir de arquivo CSV
    Formato esperado: ESCOLA,SERIE,TURMA
    Exemplo: ANDRE FRANCO MONTORO,1ANO,A

    Para cada linha:
    1. Cria a escola se não existir
    2. Cria a série se não existir (sempre com s_instituicao = 1)
    3. Cria a turma associando aos IDs corretos

    Parâmetros:
    - file: Arquivo CSV
    - dry_run: Se True, apenas valida sem importar (default: False)
    """
    try:
        # Usar db diretamente do parâmetro de path
        db_name = db
        print(f"🗄️ Usando banco: {db_name}")

        # Lê conteúdo do arquivo
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
                "stats": {
                    "total_linhas": 0,
                    "escolas_criadas": 0,
                    "series_criadas": 0,
                    "turmas_criadas": 0,
                    "erros": 1
                }
            }

        # Se dry_run, apenas valida
        if dry_run:
            return EstruturaService.validar_estrutura_csv(file_content, db_name=db_name, dry_run=True)

        # Importação real
        return EstruturaService.importar_estrutura(file_content, db_name=db_name)

    except Exception as e:
        return {
            "success": False,
            "message": f"Erro geral na importação: {str(e)}",
            "stats": {
                "total_linhas": 0,
                "escolas_criadas": 0,
                "series_criadas": 0,
                "turmas_criadas": 0,
                "erros": 1
            }
        }


@router.get("/info")
async def get_import_info(db: str, request: Request):
    """
    Retorna informações sobre dados existentes e formato esperado do CSV
    """
    # Usar db diretamente do parâmetro de path
    db_name = db
    return EstruturaService.obter_informacoes_estrutura(db_name)

