# core/workflows/medical_base.py
from core.database.connection import TenantDatabase
from core.database.models import Doctor, Specialty, InsurancePlan, MedicalExam
from sqlalchemy.orm import joinedload

class MedicalWorkflow:
    def __init__(self, tenant_id: str, config: dict):
        self.tenant_id = tenant_id
        self.config = config
        self.business_rules = config.get("business_rules", {})
        self.scripts = config.get("scripts", {})
    
    def get_db_session(self):
        """Retorna sessão do banco do tenant"""
        return TenantDatabase.get_session(self.tenant_id)
    
    def classify_symptoms(self, text: str) -> dict:
        """Classifica sintomas usando dados do banco"""
        session = self.get_db_session()
        
        try:
            # Busca todas as especialidades e seus sintomas
            specialties = session.query(Specialty).all()
            
            text_lower = text.lower()
            best_match = {"specialty": "geral", "confidence": 0.0, "symptoms_found": []}
            
            for specialty in specialties:
                # Converte JSON string para lista
                import json
                symptoms = json.loads(specialty.symptoms or '[]')
                
                found_symptoms = []
                for symptom in symptoms:
                    if symptom.lower() in text_lower:
                        found_symptoms.append(symptom)
                
                # Calcula confiança baseada em quantos sintomas foram encontrados
                confidence = len(found_symptoms) / max(len(symptoms), 1)
                
                if confidence > best_match["confidence"]:
                    best_match = {
                        "specialty": specialty.name,
                        "confidence": confidence,
                        "symptoms_found": found_symptoms
                    }
            
            return best_match
            
        finally:
            session.close()
    
    def recommend_doctor(self, specialty: str, insurance: str = None, preference: str = None) -> dict:
        """Recomenda médico baseado em critérios"""
        session = self.get_db_session()
        
        try:
            # Query base: médicos da especialidade
            query = session.query(Doctor).join(
                Doctor.specialties
            ).filter(
                Specialty.name == specialty
            )
            
            # Filtro por convênio se informado
            if insurance and insurance.lower() != "particular":
                query = query.join(Doctor.insurance_plans).filter(
                    InsurancePlan.name.ilike(f"%{insurance}%")
                )
            
            doctors = query.all()
            
            if not doctors:
                return {"error": "Nenhum médico encontrado para os critérios"}
            
            # Lógica de preferência (configurável por tenant)
            director_keywords = self.business_rules.get("director_keyword", [])
            if preference and any(kw in preference.lower() for kw in director_keywords):
                # Prioriza diretores
                directors = [d for d in doctors if d.is_director]
                if directors:
                    return self._format_doctor_response(directors[0], "director")
            
            # Retorna opções (equipe + diretor se houver)
            team_doctors = [d for d in doctors if not d.is_director]
            directors = [d for d in doctors if d.is_director]
            
            return {
                "team_options": [self._format_doctor_response(d, "team") for d in team_doctors],
                "director_options": [self._format_doctor_response(d, "director") for d in directors]
            }
            
        finally:
            session.close()
    
    def check_insurance_coverage(self, insurance_name: str, service_type: str = "consultation") -> dict:
        """Verifica cobertura de convênio"""
        session = self.get_db_session()
        
        try:
            plan = session.query(InsurancePlan).filter(
                InsurancePlan.name.ilike(f"%{insurance_name}%")
            ).first()
            
            if not plan:
                return {
                    "covered": False,
                    "message": "Convênio não aceito na clínica"
                }
            
            # Regras específicas por tipo de serviço
            if service_type == "consultation" and plan.covers_consultation:
                return {
                    "covered": True,
                    "message": "Consulta coberta pelo convênio",
                    "rules": plan.rules
                }
            elif service_type == "treatment" and plan.covers_treatments:
                return {
                    "covered": True, 
                    "message": "Tratamento coberto pelo convênio"
                }
            else:
                return {
                    "covered": False,
                    "message": f"Convênio não cobre {service_type}s - atendimento particular"
                }
                
        finally:
            session.close()
    
    def get_pricing_info(self, specialty: str, doctor_preference: str = None) -> dict:
        """Retorna informações de preço (só quando solicitado)"""
        
        # Política de valores configurável
        if self.business_rules.get("pricing_policy") != "only_when_asked":
            return {"message": "Valores informados apenas mediante solicitação"}
        
        session = self.get_db_session()
        
        try:
            doctors = self.recommend_doctor(specialty, preference=doctor_preference)
            
            terminology = self.business_rules.get("terminology", "consulta")
            
            # Formata resposta com preços
            if "team_options" in doctors and doctors["team_options"]:
                team_price = doctors["team_options"][0]["price"]
                response = f"O {terminology} da consulta com nossa equipe é R$ {team_price}."
                
                if "director_options" in doctors and doctors["director_options"]:
                    director_price = doctors["director_options"][0]["price"]
                    response += f" Com nossa diretora, o {terminology} é R$ {director_price}."
                
                return {"message": response}
            
            return {"message": "Valores sob consulta"}
            
        finally:
            session.close()
    
    def _format_doctor_response(self, doctor: Doctor, category: str) -> dict:
        """Formata resposta do médico"""
        return {
            "name": doctor.name,
            "price": doctor.consultation_price,
            "category": category,
            "is_director": doctor.is_director,
            "description": doctor.description,
            "scheduling": doctor.scheduling_type,
            "insurance_note": doctor.insurance_note
        }
    
    def collect_name(self, attempt_number: int, context: dict) -> str:
        """Coleta nome com scripts configuráveis"""
        scripts = self.scripts.get("name_collection", [])
        
        if attempt_number < len(scripts):
            script = scripts[attempt_number]
            if "{summary}" in script:
                summary = context.get("last_message_summary", "sua situação")
                script = script.format(summary=summary)
            return script
        
        return "Vou te chamar de 'senhor(a)' por enquanto, tudo bem?"
    
    def process_message(self, message, conversation_context) -> str:
        """Processa mensagem usando dados do banco + regras de negócio"""
        
        # 1. Classifica sintomas
        symptom_analysis = self.classify_symptoms(message.text)
        
        # 2. Se sintomas encontrados, recomenda médicos
        if symptom_analysis["confidence"] > 0.3:
            specialty = symptom_analysis["specialty"]
            doctors = self.recommend_doctor(specialty)
            
            # Formata resposta personalizada
            response = f"Pelos sintomas que você mencionou ({', '.join(symptom_analysis['symptoms_found'])}), "
            response += f"nossa especialidade de {specialty} pode te ajudar. "
            
            if doctors.get("team_options"):
                response += f"Temos uma excelente equipe disponível."
            
            return response
        
        # 3. Resposta genérica ou outros fluxos
        return "Como posso ajudar você hoje?"