"""
Modelos para importação de alunos (processo multi-step)
Responsabilidade: Validar estrutura de dados de importação de alunos
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any


class AlunoPreview(BaseModel):
    """Modelo para preview de um aluno no CSV"""
    linha: int = Field(..., description="Número da linha no CSV")
    dados: Dict[str, Any] = Field(..., description="Dados do aluno")
    
    class Config:
        json_schema_extra = {
            "example": {
                "linha": 1,
                "dados": {
                    "nome": "João Silva",
                    "email": "joao@example.com",
                    "cpf": "12345678901"
                }
            }
        }


class AlunoConflito(BaseModel):
    """Modelo para conflito detectado na importação"""
    tipo: str = Field(..., description="Tipo de conflito (duplicado, email_existente, etc)")
    linha: int = Field(..., description="Linha do CSV onde ocorreu o conflito")
    campo: str = Field(..., description="Campo que causou o conflito")
    valor: str = Field(..., description="Valor conflitante")
    mensagem: str = Field(..., description="Descrição do conflito")
    aluno_existente: Optional[Dict[str, Any]] = Field(None, description="Dados do aluno existente (se aplicável)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tipo": "email_existente",
                "linha": 5,
                "campo": "email",
                "valor": "joao@example.com",
                "mensagem": "Email já cadastrado no sistema",
                "aluno_existente": {
                    "id": 123,
                    "nome": "João Silva",
                    "turma": "3º Ano A"
                }
            }
        }


# ========================================
# STEP 1: Upload e Validação Inicial
# ========================================

class Step1Response(BaseModel):
    """Resposta do Step 1 - Upload e validação inicial"""
    success: bool = Field(..., description="Se o upload foi bem-sucedido")
    message: str = Field(..., description="Mensagem descritiva")
    step: int = Field(1, description="Número do step atual")
    session_id: Optional[str] = Field(None, description="ID da sessão de importação")
    total_linhas: Optional[int] = Field(None, description="Total de linhas no CSV")
    colunas_detectadas: Optional[List[str]] = Field(None, description="Colunas detectadas no CSV")
    preview: Optional[List[AlunoPreview]] = Field(None, description="Preview das primeiras linhas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Arquivo validado com sucesso",
                "step": 1,
                "session_id": "abc123xyz",
                "total_linhas": 150,
                "colunas_detectadas": ["nome", "email", "cpf", "turma"],
                "preview": [
                    {
                        "linha": 1,
                        "dados": {
                            "nome": "João Silva",
                            "email": "joao@example.com"
                        }
                    }
                ]
            }
        }


# ========================================
# STEP 2: Validação de Mapeamento
# ========================================

class Step2Request(BaseModel):
    """Request do Step 2 - Mapeamento de colunas"""
    session_id: str = Field(..., description="ID da sessão de importação")
    mapping: Dict[str, str] = Field(..., description="Mapeamento de colunas CSV -> Sistema")
    
    @validator('session_id')
    def session_id_nao_vazio(cls, v):
        if not v or not v.strip():
            raise ValueError('session_id não pode ser vazio')
        return v.strip()
    
    @validator('mapping')
    def mapping_nao_vazio(cls, v):
        if not v:
            raise ValueError('mapping não pode ser vazio')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123xyz",
                "mapping": {
                    "nome": "Nome Completo",
                    "email": "E-mail",
                    "cpf": "CPF",
                    "turma": "Turma"
                }
            }
        }


class Step2Response(BaseModel):
    """Resposta do Step 2 - Validação de mapeamento"""
    success: bool = Field(..., description="Se o mapeamento foi validado")
    message: str = Field(..., description="Mensagem descritiva")
    step: int = Field(2, description="Número do step atual")
    campos_obrigatorios_faltando: Optional[List[str]] = Field(None, description="Campos obrigatórios não mapeados")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Mapeamento validado com sucesso",
                "step": 2,
                "campos_obrigatorios_faltando": []
            }
        }


# ========================================
# STEP 3: Validação e Detecção de Conflitos
# ========================================

class Step3Request(BaseModel):
    """Request do Step 3 - Validação de conflitos"""
    session_id: str = Field(..., description="ID da sessão de importação")

    @validator('session_id')
    def session_id_nao_vazio(cls, v):
        if not v or not v.strip():
            raise ValueError('session_id não pode ser vazio')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123xyz"
            }
        }


class Step3Response(BaseModel):
    """Resposta do Step 3 - Detecção de conflitos"""
    success: bool = Field(..., description="Se a validação foi bem-sucedida")
    message: str = Field(..., description="Mensagem descritiva")
    step: int = Field(3, description="Número do step atual")
    total_conflitos: Optional[int] = Field(None, description="Total de conflitos detectados")
    conflitos: Optional[List[AlunoConflito]] = Field(None, description="Lista de conflitos detectados")
    total_validos: Optional[int] = Field(None, description="Total de registros válidos")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Validação concluída",
                "step": 3,
                "total_conflitos": 2,
                "conflitos": [
                    {
                        "tipo": "email_existente",
                        "linha": 5,
                        "campo": "email",
                        "valor": "joao@example.com",
                        "mensagem": "Email já cadastrado"
                    }
                ],
                "total_validos": 148
            }
        }


# ========================================
# STEP 4: Confirmação e Importação Final
# ========================================

class Step4Request(BaseModel):
    """Request do Step 4 - Confirmação e importação"""
    session_id: str = Field(..., description="ID da sessão de importação")
    confirmar_importacao: bool = Field(..., description="Se confirma a importação mesmo com conflitos")
    ignorar_conflitos: bool = Field(False, description="Se deve ignorar registros com conflitos")

    @validator('session_id')
    def session_id_nao_vazio(cls, v):
        if not v or not v.strip():
            raise ValueError('session_id não pode ser vazio')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123xyz",
                "confirmar_importacao": True,
                "ignorar_conflitos": True
            }
        }


class Step4Response(BaseModel):
    """Resposta do Step 4 - Resultado da importação"""
    success: bool = Field(..., description="Se a importação foi bem-sucedida")
    message: str = Field(..., description="Mensagem descritiva")
    step: int = Field(4, description="Número do step atual")
    total_importados: Optional[int] = Field(None, description="Total de alunos importados")
    total_ignorados: Optional[int] = Field(None, description="Total de registros ignorados")
    total_erros: Optional[int] = Field(None, description="Total de erros")
    detalhes: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais da importação")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Importação concluída com sucesso",
                "step": 4,
                "total_importados": 148,
                "total_ignorados": 2,
                "total_erros": 0,
                "detalhes": {
                    "tempo_processamento": "5.2s",
                    "instituicao_id": 10
                }
            }
        }

