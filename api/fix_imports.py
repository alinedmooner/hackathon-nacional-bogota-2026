import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r') as file:
        content = file.read()
    
    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w') as file:
            file.write(new_content)
        print(f"Updated {filepath}")

replacements = [
    ("from config import settings", "from src.core.config import settings"),
    ("from security import ", "from src.core.security import "),
    ("from db import ", "from src.database import "),
    ("from datasets import ", "from src.core.datasets import "),
    ("from soql_query import ", "from src.core.soql_query import "),
    
    # Specific services
    ("from services import auth_service", "from src.auth import service as auth_service"),
    ("from services import contratos_service", "from src.contracts import service as contratos_service"),
    ("from services import cache_service", "from src.core import cache_service"),
    ("from services import analytics_paso1_service", "from src.analytics import paso1_service"),
    ("from services import analytics_paso2_service", "from src.analytics import paso2_service"),
    ("from services import radar_service", "from src.analytics import radar_service"),
    ("from models import ", "from src.core.models import "),
    ("from repositories import ", "from src.core.repositories import "),
]

for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            replace_in_file(os.path.join(root, file), replacements)

