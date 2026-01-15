"""
Modelos para estrutura organizacional (instituições, cursos, turmas, etc)
Responsabilidade: Validar estrutura de dados de entidades organizacionais
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class InstituicaoResponse(BaseModel):
    """Modelo de resposta para instituição"""
    id: int = Field(..., description="ID da instituição")
    nome: str = Field(..., description="Nome da instituição")
    codigo: Optional[str] = Field(None, description="Código da instituição")
    ativa: bool = Field(True, description="Se a instituição está ativa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 10,
                "nome": "Escola Exemplo",
                "codigo": "ESC001",
                "ativa": True
            }
        }


class CursoResponse(BaseModel):
    """Modelo de resposta para curso"""
    id: int = Field(..., description="ID do curso")
    nome: str = Field(..., description="Nome do curso")
    codigo: Optional[str] = Field(None, description="Código do curso")
    instituicao_id: int = Field(..., description="ID da instituição")
    instituicao_nome: Optional[str] = Field(None, description="Nome da instituição")
    ativo: bool = Field(True, description="Se o curso está ativo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 5,
                "nome": "Ensino Médio",
                "codigo": "EM",
                "instituicao_id": 10,
                "instituicao_nome": "Escola Exemplo",
                "ativo": True
            }
        }


class TurmaResponse(BaseModel):
    """Modelo de resposta para turma"""
    id: int = Field(..., description="ID da turma")
    nome: str = Field(..., description="Nome da turma")
    codigo: Optional[str] = Field(None, description="Código da turma")
    curso_id: int = Field(..., description="ID do curso")
    curso_nome: Optional[str] = Field(None, description="Nome do curso")
    instituicao_id: int = Field(..., description="ID da instituição")
    instituicao_nome: Optional[str] = Field(None, description="Nome da instituição")
    ano: Optional[int] = Field(None, description="Ano da turma")
    periodo: Optional[str] = Field(None, description="Período (manhã, tarde, noite)")
    total_alunos: Optional[int] = Field(None, description="Total de alunos na turma")
    ativa: bool = Field(True, description="Se a turma está ativa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 25,
                "nome": "3º Ano A",
                "codigo": "3A",
                "curso_id": 5,
                "curso_nome": "Ensino Médio",
                "instituicao_id": 10,
                "instituicao_nome": "Escola Exemplo",
                "ano": 2025,
                "periodo": "manhã",
                "total_alunos": 35,
                "ativa": True
            }
        }


class DisciplinaResponse(BaseModel):
    """Modelo de resposta para disciplina"""
    id: int = Field(..., description="ID da disciplina")
    nome: str = Field(..., description="Nome da disciplina")
    codigo: Optional[str] = Field(None, description="Código da disciplina")
    curso_id: Optional[int] = Field(None, description="ID do curso")
    curso_nome: Optional[str] = Field(None, description="Nome do curso")
    carga_horaria: Optional[int] = Field(None, description="Carga horária em horas")
    ativa: bool = Field(True, description="Se a disciplina está ativa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 15,
                "nome": "Matemática",
                "codigo": "MAT",
                "curso_id": 5,
                "curso_nome": "Ensino Médio",
                "carga_horaria": 80,
                "ativa": True
            }
        }


class AlunoResponse(BaseModel):
    """Modelo de resposta para aluno"""
    id: int = Field(..., description="ID do aluno")
    nome: str = Field(..., description="Nome completo do aluno")
    email: Optional[str] = Field(None, description="Email do aluno")
    cpf: Optional[str] = Field(None, description="CPF do aluno")
    matricula: Optional[str] = Field(None, description="Matrícula do aluno")
    turma_id: Optional[int] = Field(None, description="ID da turma")
    turma_nome: Optional[str] = Field(None, description="Nome da turma")
    instituicao_id: Optional[int] = Field(None, description="ID da instituição")
    instituicao_nome: Optional[str] = Field(None, description="Nome da instituição")
    data_nascimento: Optional[str] = Field(None, description="Data de nascimento (YYYY-MM-DD)")
    telefone: Optional[str] = Field(None, description="Telefone do aluno")
    ativo: bool = Field(True, description="Se o aluno está ativo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1234,
                "nome": "João Silva",
                "email": "joao@example.com",
                "cpf": "12345678901",
                "matricula": "2025001",
                "turma_id": 25,
                "turma_nome": "3º Ano A",
                "instituicao_id": 10,
                "instituicao_nome": "Escola Exemplo",
                "data_nascimento": "2007-05-15",
                "telefone": "11999999999",
                "ativo": True
            }
        }


class ListaInstituicoesResponse(BaseModel):
    """Modelo de resposta para lista de instituições"""
    total: int = Field(..., description="Total de instituições")
    instituicoes: List[InstituicaoResponse] = Field(..., description="Lista de instituições")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "instituicoes": [
                    {
                        "id": 10,
                        "nome": "Escola Exemplo",
                        "codigo": "ESC001",
                        "ativa": True
                    }
                ]
            }
        }

