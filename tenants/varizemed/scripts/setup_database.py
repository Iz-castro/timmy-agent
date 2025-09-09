# tenants/varizemed/scripts/setup_database.py
from core.database.models import *
from core.database.connection import TenantDatabase

def setup_varizemed_database():
    print("[SETUP] Iniciando configuração do banco da Varizemed...")
    session = TenantDatabase.get_session("varizemed")
    
    try:
        # ========================================
        # ESPECIALIDADES
        # ========================================
        print("[SETUP] Criando especialidades...")
        angiologia = Specialty(
            name="Angiologia",
            symptoms='["varizes", "microvarizes", "dor nas pernas", "inchaço", "vasinhos", "safena", "doenças venosas", "circulação"]',
            treatments='["microespuma ecoguiada", "escleroterapia", "laser transdérmico", "glicose escleroterapia"]',
            exams='["doppler venoso", "doppler arterial", "pletismografia", "ultrassom vascular"]'
        )
        
        coloproctologia = Specialty(
            name="Coloproctologia", 
            symptoms='["hemorroidas", "fissura anal", "sangramento anal", "dor anal", "coceira anal", "incontinência"]',
            treatments='["microespuma ecoguiada para hemorroidas"]',
            exams='["colonoscopia", "anuscopia", "retossigmoidoscopia"]'
        )
        
        fisioterapia = Specialty(
            name="Fisioterapia",
            symptoms='["lipedema", "linfedema", "retenção de líquido", "inchaço braços", "inchaço pernas", "drenagem"]',
            treatments='["drenagem linfática", "fisioterapia especializada"]',
            exams='["avaliação fisioterapêutica"]'
        )
        
        endocrinologia = Specialty(
            name="Endocrinologia",
            symptoms='["diabetes", "tireoide", "hormônios", "metabolismo", "obesidade", "resistência insulina"]',
            treatments='["acompanhamento endocrinológico", "controle hormonal"]',
            exams='["exames hormonais", "glicemia", "TSH", "T3", "T4"]'
        )
        
        medicina_funcional = Specialty(
            name="Medicina Funcional e Estilo de Vida",
            symptoms='["fadiga", "estresse", "imunidade baixa", "digestão", "sono", "medicina integrativa"]',
            treatments='["medicina funcional", "medicina do estilo de vida", "abordagem integrativa"]',
            exams='["exames funcionais", "avaliação integrativa"]'
        )
        
        # ========================================
        # MÉDICOS INDIVIDUAIS
        # ========================================
        print("[SETUP] Criando médicos...")
        
        # ANGIOLOGIA - Dra. Solange (Diretora)
        dra_solange = Doctor(
            name="Dra. Solange Evangelista",
            crm="",
            consultation_price="890",
            is_director=True,
            scheduling_type="doctoralia_human",
            description="Diretora da clínica, referência nacional no tratamento de varizes e pioneira na técnica de Microespuma no Brasil",
            insurance_note="Atende particular e Unimed"
        )
        
        # ANGIOLOGIA - Dr. Cristovam
        dr_cristovam = Doctor(
            name="Dr. Cristovam Galli Jr",
            crm="40.932",
            consultation_price="475",
            is_director=False,
            scheduling_type="doctoralia_human",
            description="Angiologista da equipe",
            insurance_note="Atende apenas particular"
        )
        
        # ANGIOLOGIA - Dr. Leonardo
        dr_leonardo = Doctor(
            name="Dr. Leonardo Paolinelli",
            crm="38.317", 
            consultation_price="475",
            is_director=False,
            scheduling_type="doctoralia_human",
            description="Angiologista da equipe",
            insurance_note="Atende apenas particular"
        )
        
        # ANGIOLOGIA - Dr. Luiz Antônio
        dr_luiz = Doctor(
            name="Dr. Luiz Antônio Cardoso",
            crm="15.324",
            consultation_price="475", 
            is_director=False,
            scheduling_type="doctoralia_human",
            description="Angiologista da equipe",
            insurance_note="Atende Unimed e demais convênios"
        )
        
        # ANGIOLOGIA - Dra. Tatiana
        dra_tatiana = Doctor(
            name="Dra. Tatiana Ferreira",
            crm="37.791",
            consultation_price="475",
            is_director=False, 
            scheduling_type="doctoralia_human",
            description="Angiologista da equipe",
            insurance_note="Atende Unimed e demais convênios"
        )
        
        # COLOPROCTOLOGIA - Dr. Matheus
        dr_matheus = Doctor(
            name="Dr. Matheus Massaud",
            crm="",
            consultation_price="600",
            is_director=False,
            scheduling_type="human_only",
            description="Especialista em Coloproctologia",
            insurance_note="Somente particular"
        )
        
        # ENDOCRINOLOGIA - Dra. Jane
        dra_jane = Doctor(
            name="Dra. Jane Reis de Carvalho",
            crm="",
            consultation_price="550",
            is_director=False,
            scheduling_type="doctoralia_human", 
            description="Especialista em Endocrinologia",
            insurance_note="Somente particular"
        )
        
        # FISIOTERAPIA - Dra. Luciane
        dra_luciane = Doctor(
            name="Dra. Luciane Hoepers", 
            crm="",
            consultation_price="275",
            is_director=False,
            scheduling_type="doctoralia_human",
            description="Especialista em Fisioterapia para Lipedema e Linfedema",
            insurance_note="Somente particular. Valor inclui uma sessão de fisioterapia"
        )
        
        # MEDICINA FUNCIONAL - Dr. Celso
        dr_celso = Doctor(
            name="Dr. Celso Homero",
            crm="",
            consultation_price="1000", 
            is_director=False,
            scheduling_type="human_only",
            description="Especialista em Medicina Funcional e Estilo de Vida",
            insurance_note="Somente particular"
        )
        
        # ========================================
        # CONVÊNIOS
        # ========================================
        print("[SETUP] Criando convênios...")
        
        convênios_aceitos = [
            "UNIMED", "CASSI", "BRADESCO", "VALE/PASA", "SUL AMÉRICA", "IPSEMG", 
            "NOTREDAME INTERMÉDICA", "FUNDAFFEMG", "SAÚDE CAIXA", "DESBAN",
            "FUNDAÇÃO ASSEFAZ", "FUNDAÇÃO SAÚDE ITAU", "FUNDAÇÃO LIBERTAS",
            "CEMIG SAÚDE", "AMIL", "AMAGIS SAÚDE", "COPASS SAÚDE"
        ]
        
        insurance_objects = []
        for conv_name in convênios_aceitos:
            rules = '{"cobertura": "consultas e exames de angiologia apenas", "tratamentos": "não coberto"}'
            
            if conv_name == "UNIMED":
                rules = '{"cobertura": "consultas e exames", "autorização": "não necessária"}'
            
            insurance_obj = InsurancePlan(
                name=conv_name,
                covers_consultation=True,
                covers_treatments=False,
                covers_exams='["doppler", "ultrassom vascular", "pletismografia"]',
                rules=rules
            )
            insurance_objects.append(insurance_obj)
        
        # Particular
        particular = InsurancePlan(
            name="Particular",
            covers_consultation=True,
            covers_treatments=True,
            covers_exams='["todos"]',
            rules='{"pagamento": "à vista ou parcelado até 3x", "desconto_pix": "5%"}'
        )
        insurance_objects.append(particular)
        
        # ========================================
        # ADICIONANDO AO BANCO
        # ========================================
        print("[SETUP] Salvando no banco...")
        
        session.add_all([
            # Especialidades
            angiologia, coloproctologia, fisioterapia, endocrinologia, medicina_funcional,
            
            # Médicos
            dra_solange, dr_cristovam, dr_leonardo, dr_luiz, dra_tatiana,
            dr_matheus, dra_jane, dra_luciane, dr_celso,
            
            # Convênios
            *insurance_objects
        ])
        
        session.commit()
        
        # ========================================
        # RELACIONAMENTOS MÉDICO-ESPECIALIDADE
        # ========================================
        print("[SETUP] Criando relacionamentos...")
        
        # Angiologia: Todos os angiologistas
        angio_doctors = [dra_solange, dr_cristovam, dr_leonardo, dr_luiz, dra_tatiana]
        for doctor in angio_doctors:
            session.add(DoctorSpecialty(doctor=doctor, specialty=angiologia))
        
        # Coloproctologia: Dr. Matheus
        session.add(DoctorSpecialty(doctor=dr_matheus, specialty=coloproctologia))
        
        # Fisioterapia: Dra. Luciane  
        session.add(DoctorSpecialty(doctor=dra_luciane, specialty=fisioterapia))
        
        # Endocrinologia: Dra. Jane
        session.add(DoctorSpecialty(doctor=dra_jane, specialty=endocrinologia))
        
        # Medicina Funcional: Dr. Celso
        session.add(DoctorSpecialty(doctor=dr_celso, specialty=medicina_funcional))
        
        # ========================================
        # RELACIONAMENTOS MÉDICO-CONVÊNIO
        # ========================================
        
        # Dra. Solange: Particular + Unimed
        for insurance in insurance_objects:
            if insurance.name in ["Particular", "UNIMED"]:
                session.add(DoctorInsurance(doctor=dra_solange, insurance=insurance))
        
        # Dr. Luiz e Dra. Tatiana: Todos os convênios + Particular
        for doctor in [dr_luiz, dra_tatiana]:
            for insurance in insurance_objects:
                session.add(DoctorInsurance(doctor=doctor, insurance=insurance))
        
        # Dr. Cristovam e Dr. Leonardo: Apenas Particular
        for doctor in [dr_cristovam, dr_leonardo]:
            for insurance in insurance_objects:
                if insurance.name == "Particular":
                    session.add(DoctorInsurance(doctor=doctor, insurance=insurance))
        
        # Outras especialidades: Apenas Particular
        other_doctors = [dr_matheus, dra_jane, dra_luciane, dr_celso]
        for doctor in other_doctors:
            for insurance in insurance_objects:
                if insurance.name == "Particular":
                    session.add(DoctorInsurance(doctor=doctor, insurance=insurance))
        
        session.commit()
        session.close()
        
        print("✅ Banco da Varizemed configurado com TODOS os dados reais!")
        print(f"📊 Médicos: {len(angio_doctors + [dr_matheus, dra_jane, dra_luciane, dr_celso])}")
        print(f"📊 Convênios: {len(insurance_objects)}")
        print(f"📊 Especialidades: 5")
        
    except Exception as e:
        print(f"❌ Erro durante setup: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        session.rollback()
        session.close()

if __name__ == "__main__":
    setup_varizemed_database()