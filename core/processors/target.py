# core/processors/target.py
"""
Target Capture System - Captura de informações configurável por tenant
NOVO: Sistema flexível para capturar dados específicos de cada tenant
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path
import json

@dataclass
class TargetField:
    """Define um campo a ser capturado"""
    field_name: str              # Nome interno do campo (ex: 'tipo_negocio')
    display_name: str            # Nome para exibição (ex: 'Tipo de Negócio')
    field_type: str              # 'text', 'choice', 'number', 'email', 'phone'
    required: bool = False       # Se é obrigatório
    choices: List[str] = field(default_factory=list)  # Para tipo 'choice'
    validation_pattern: Optional[str] = None  # Regex para validação
    prompt_triggers: List[str] = field(default_factory=list)  # Palavras que ativam captura
    
    def __post_init__(self):
        """Validação básica"""
        if self.field_type == 'choice' and not self.choices:
            raise ValueError(f"Campo {self.field_name} tipo 'choice' precisa de opções")


@dataclass 
class TargetCapture:
    """Configuração completa de captura para um tenant"""
    tenant_id: str
    target_name: str                              # Nome do target (ex: 'cliente_vendas', 'paciente_medico')
    description: str                              # Descrição do propósito
    fields: List[TargetField] = field(default_factory=list)
    completion_triggers: List[str] = field(default_factory=list)  # Quando considerar completo
    auto_capture: bool = True                     # Se deve tentar capturar automaticamente
    
    def get_field_by_name(self, field_name: str) -> Optional[TargetField]:
        """Busca campo por nome"""
        return next((f for f in self.fields if f.field_name == field_name), None)
    
    def get_required_fields(self) -> List[TargetField]:
        """Retorna apenas campos obrigatórios"""
        return [f for f in self.fields if f.required]
    
    def is_complete(self, captured_data: Dict[str, Any]) -> bool:
        """Verifica se todos os campos obrigatórios foram capturados"""
        required_fields = [f.field_name for f in self.get_required_fields()]
        return all(field in captured_data and captured_data[field] for field in required_fields)


class TargetProcessor(ABC):
    """Interface para processadores de target específicos"""
    
    @abstractmethod
    def extract_from_message(self, message: str, target_config: TargetCapture) -> Dict[str, Any]:
        """Extrai informações da mensagem baseado na configuração"""
        pass
    
    @abstractmethod
    def validate_field(self, field: TargetField, value: Any) -> tuple[bool, str]:
        """Valida um campo específico"""
        pass


class SmartTargetProcessor(TargetProcessor):
    """Processador inteligente usando LLM para extrair informações"""
    
    def extract_from_message(self, message: str, target_config: TargetCapture) -> Dict[str, Any]:
        """
        Extrai informações usando análise inteligente
        """
        extracted = {}
        
        # Para cada campo configurado, tenta extrair
        for field in target_config.fields:
            value = self._extract_field_value(message, field)
            if value:
                is_valid, error_msg = self.validate_field(field, value)
                if is_valid:
                    extracted[field.field_name] = value
                    
        return extracted
    
    def _extract_field_value(self, message: str, field: TargetField) -> Optional[str]:
        """Extrai valor de um campo específico da mensagem"""
        message_lower = message.lower()
        
        # Verifica triggers específicos do campo
        for trigger in field.prompt_triggers:
            if trigger.lower() in message_lower:
                # TODO: Implementar extração mais sofisticada com LLM
                # Por enquanto, busca padrões simples
                return self._simple_pattern_extract(message, field, trigger)
        
        return None
    
    def _simple_pattern_extract(self, message: str, field: TargetField, trigger: str) -> Optional[str]:
        """Extração simples baseada em padrões"""
        import re
        
        # Padrões específicos por tipo de campo
        if field.field_type == 'choice':
            # Busca por uma das opções válidas
            for choice in field.choices:
                if choice.lower() in message.lower():
                    return choice
        
        elif field.field_type == 'text':
            # Busca texto após o trigger
            pattern = rf"{re.escape(trigger)}\s*[:=]?\s*([^.!?;]+)"
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def validate_field(self, field: TargetField, value: Any) -> tuple[bool, str]:
        """Valida campo conforme configuração"""
        
        if field.field_type == 'choice':
            if value not in field.choices:
                return False, f"Valor deve ser uma das opções: {', '.join(field.choices)}"
        
        elif field.field_type == 'email':
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                return False, "Email inválido"
        
        elif field.field_type == 'phone':
            # Validação básica de telefone brasileiro
            clean_phone = re.sub(r'[^\d]', '', str(value))
            if len(clean_phone) not in [10, 11]:
                return False, "Telefone deve ter 10 ou 11 dígitos"
        
        elif field.validation_pattern:
            import re
            if not re.match(field.validation_pattern, str(value)):
                return False, f"Valor não atende ao padrão esperado"
        
        return True, ""


class TargetConfigManager:
    """Gerenciador de configurações de target por tenant"""
    
    def __init__(self):
        self._configs: Dict[str, TargetCapture] = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Carrega configurações de todos os tenants"""
        tenants_dir = Path("tenants")
        if not tenants_dir.exists():
            return
        
        for tenant_dir in tenants_dir.iterdir():
            if tenant_dir.is_dir():
                self._load_tenant_config(tenant_dir.name)
    
    def _load_tenant_config(self, tenant_id: str):
        """Carrega configuração de um tenant específico"""
        config_file = Path(f"tenants/{tenant_id}/target_config.json")
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Converte para objetos
                fields = []
                for field_data in config_data.get('fields', []):
                    field = TargetField(**field_data)
                    fields.append(field)
                
                target_config = TargetCapture(
                    tenant_id=tenant_id,
                    target_name=config_data.get('target_name', f'{tenant_id}_target'),
                    description=config_data.get('description', ''),
                    fields=fields,
                    completion_triggers=config_data.get('completion_triggers', []),
                    auto_capture=config_data.get('auto_capture', True)
                )
                
                self._configs[tenant_id] = target_config
                print(f"[TARGET] Configuração carregada para {tenant_id}: {len(fields)} campos")
                
            except Exception as e:
                print(f"[ERROR] Erro ao carregar config de target para {tenant_id}: {e}")
    
    def get_config(self, tenant_id: str) -> Optional[TargetCapture]:
        """Retorna configuração de target para um tenant"""
        return self._configs.get(tenant_id)
    
    def create_default_config(self, tenant_id: str, target_type: str = "generic") -> TargetCapture:
        """Cria configuração padrão baseada no tipo"""
        
        if target_type == "vendas":
            fields = [
                TargetField(
                    field_name="tipo_negocio",
                    display_name="Tipo de Negócio",
                    field_type="text",
                    required=True,
                    prompt_triggers=["negócio", "empresa", "trabalho", "atividade", "ramo"]
                ),
                TargetField(
                    field_name="numero_funcionarios",
                    display_name="Número de Funcionários",
                    field_type="choice",
                    required=False,
                    choices=["1-5", "6-20", "21-50", "51-100", "100+"],
                    prompt_triggers=["funcionários", "colaboradores", "equipe", "pessoas"]
                ),
                TargetField(
                    field_name="dor_principal",
                    display_name="Principal Desafio",
                    field_type="text",
                    required=True,
                    prompt_triggers=["problema", "dificuldade", "desafio", "precisando"]
                )
            ]
            
        elif target_type == "medico":
            fields = [
                TargetField(
                    field_name="especialidade_interesse",
                    display_name="Especialidade de Interesse",
                    field_type="choice",
                    required=False,
                    choices=["Cardiologia", "Dermatologia", "Ortopedia", "Pediatria", "Ginecologia", "Neurologia"],
                    prompt_triggers=["especialidade", "médico", "doutor", "especialista"]
                ),
                TargetField(
                    field_name="tipo_consulta",
                    display_name="Tipo de Consulta",
                    field_type="choice",
                    required=False,
                    choices=["Primeira consulta", "Retorno", "Exame", "Emergência"],
                    prompt_triggers=["consulta", "atendimento", "ver médico"]
                ),
                TargetField(
                    field_name="sintomas_principais",
                    display_name="Sintomas Principais",
                    field_type="text",
                    required=False,
                    prompt_triggers=["sintoma", "sentindo", "dor", "problema de saúde"]
                )
            ]
        else:
            # Configuração genérica
            fields = [
                TargetField(
                    field_name="interesse_principal",
                    display_name="Principal Interesse",
                    field_type="text",
                    required=True,
                    prompt_triggers=["interesse", "procurando", "preciso", "quero"]
                )
            ]
        
        config = TargetCapture(
            tenant_id=tenant_id,
            target_name=f"{tenant_id}_{target_type}",
            description=f"Configuração {target_type} para {tenant_id}",
            fields=fields,
            auto_capture=True
        )
        
        return config
    
    def save_config(self, config: TargetCapture):
        """Salva configuração no arquivo"""
        config_file = Path(f"tenants/{config.tenant_id}/target_config.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Converte para dict serializável
        config_dict = {
            "target_name": config.target_name,
            "description": config.description,
            "auto_capture": config.auto_capture,
            "completion_triggers": config.completion_triggers,
            "fields": []
        }
        
        for field in config.fields:
            field_dict = {
                "field_name": field.field_name,
                "display_name": field.display_name,
                "field_type": field.field_type,
                "required": field.required,
                "choices": field.choices,
                "validation_pattern": field.validation_pattern,
                "prompt_triggers": field.prompt_triggers
            }
            config_dict["fields"].append(field_dict)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        # Atualiza cache
        self._configs[config.tenant_id] = config
        print(f"[TARGET] Configuração salva para {config.tenant_id}")


# Instância global do gerenciador
target_manager = TargetConfigManager()


def get_target_config(tenant_id: str) -> Optional[TargetCapture]:
    """Função helper para obter configuração de target"""
    return target_manager.get_config(tenant_id)


def create_target_config(tenant_id: str, target_type: str = "generic") -> TargetCapture:
    """Função helper para criar configuração padrão"""
    config = target_manager.create_default_config(tenant_id, target_type)
    target_manager.save_config(config)
    return config
