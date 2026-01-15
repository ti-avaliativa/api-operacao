"""
Modelos Pydantic para validação de dados
Responsabilidade: Definir estrutura e validação de requests/responses
"""

from app.models.common import (
    ErrorResponse,
    SuccessResponse,
    MessageResponse
)

from app.models.alunos import (
    Step1Response,
    Step2Request,
    Step2Response,
    Step3Request,
    Step3Response,
    Step4Request,
    Step4Response,
    AlunoConflito,
    AlunoPreview
)

from app.models.estrutura import (
    InstituicaoResponse,
    CursoResponse,
    TurmaResponse,
    DisciplinaResponse,
    AlunoResponse
)

__all__ = [
    # Common
    "ErrorResponse",
    "SuccessResponse",
    "MessageResponse",
    # Alunos
    "Step1Response",
    "Step2Request",
    "Step2Response",
    "Step3Request",
    "Step3Response",
    "Step4Request",
    "Step4Response",
    "AlunoConflito",
    "AlunoPreview",
    # Estrutura
    "InstituicaoResponse",
    "CursoResponse",
    "TurmaResponse",
    "DisciplinaResponse",
    "AlunoResponse",
]
