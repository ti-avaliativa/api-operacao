"""
Modelos comuns usados em toda a API
Responsabilidade: Definir estruturas de resposta padrão
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class ErrorResponse(BaseModel):
    """Modelo padrão para respostas de erro"""
    success: bool = Field(False, description="Sempre False para erros")
    error: str = Field(..., description="Mensagem de erro")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais do erro")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Arquivo inválido",
                "details": {
                    "formato_esperado": "CSV",
                    "formato_recebido": "TXT"
                }
            }
        }


class SuccessResponse(BaseModel):
    """Modelo padrão para respostas de sucesso"""
    success: bool = Field(True, description="Sempre True para sucesso")
    message: str = Field(..., description="Mensagem de sucesso")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados adicionais")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operação realizada com sucesso",
                "data": {
                    "total_processado": 100
                }
            }
        }


class MessageResponse(BaseModel):
    """Modelo simples para mensagens"""
    message: str = Field(..., description="Mensagem")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "API está funcionando corretamente"
            }
        }

