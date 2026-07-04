import shutil

moves = [
    ("routes/auth.py", "src/auth/router.py"),
    ("services/auth_service.py", "src/auth/service.py"),
    ("routes/contratos.py", "src/contracts/router.py"),
    ("routes/contratos_mongo.py", "src/contracts/router_mongo.py"),
    ("routes/archivos.py", "src/contracts/router_archivos.py"),
    ("services/contratos_service.py", "src/contracts/service.py"),
    ("routes/ai.py", "src/ai/router.py"),
    ("services/ai", "src/ai/services"),
    ("routes/analytics.py", "src/analytics/router.py"),
    ("routes/analytics_paso1.py", "src/analytics/router_paso1.py"),
    ("routes/radar.py", "src/analytics/radar.py"),
    ("services/analytics_paso1_service.py", "src/analytics/paso1_service.py"),
    ("services/analytics_paso2_service.py", "src/analytics/paso2_service.py"),
    ("services/radar_service.py", "src/analytics/radar_service.py"),
    ("services/cache_service.py", "src/core/cache_service.py")
]

for src, dst in moves:
    try:
        shutil.move(src, dst)
    except Exception as e:
        print(f"Error moving {src} to {dst}: {e}")

try:
    shutil.rmtree("routes")
    shutil.rmtree("services")
except Exception:
    pass
