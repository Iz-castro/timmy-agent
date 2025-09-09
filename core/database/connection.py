# core/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from .models import Base

class TenantDatabase:
    _connections = {}
    
    @classmethod
    def get_session(cls, tenant_id: str):
        if tenant_id not in cls._connections:
            # Garante que o diretório existe
            tenant_dir = Path(f"tenants/{tenant_id}")
            tenant_dir.mkdir(parents=True, exist_ok=True)
            
            db_path = tenant_dir / "database.db"
            print(f"[DATABASE] Criando conexão para {tenant_id}: {db_path}")
            
            engine = create_engine(f"sqlite:///{db_path}")
            
            # Cria tabelas se não existirem
            Base.metadata.create_all(engine)
            print(f"[DATABASE] Tabelas criadas/verificadas para {tenant_id}")
            
            SessionLocal = sessionmaker(bind=engine)
            cls._connections[tenant_id] = SessionLocal
        
        return cls._connections[tenant_id]()