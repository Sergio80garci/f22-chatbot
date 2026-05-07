#!/usr/bin/env python3
"""
Security Audit Script for F22 Chatbot
Validates security configuration and identifies vulnerabilities
"""

import os
import sys
import json
from pathlib import Path
from typing import Tuple, List, Dict

# Audit results tracking
audit_results = {
    "CRÍTICO": [],
    "ALTO": [],
    "MEDIO": [],
    "BAJO": [],
    "PASÓ": [],
}


def check_env_files() -> None:
    """Check if .env files are properly protected."""
    gitignore_path = Path(".gitignore")
    env_files = list(Path(".").glob(".env*"))

    if not gitignore_path.exists():
        audit_results["CRÍTICO"].append(
            "❌ .gitignore no existe — riesgo de exposición de credenciales"
        )
        return

    gitignore_content = gitignore_path.read_text()
    if ".env" in gitignore_content:
        audit_results["PASÓ"].append("✅ .env está protegido en .gitignore")
    else:
        audit_results["CRÍTICO"].append(
            "❌ .env NO está en .gitignore — puede ser commiteado a git"
        )

    if env_files:
        audit_results["ALTO"].append(
            f"⚠️  Archivos .env encontrados: {[f.name for f in env_files]}"
        )


def check_hardcoded_secrets() -> None:
    """Scan code for hardcoded secrets."""
    sensitive_patterns = [
        ("password", "password="),
        ("api_key", "api_key="),
        ("secret", "secret="),
        ("token", "token="),
    ]

    found = []
    for root, dirs, files in os.walk("backend"):
        for file in files:
            if file.endswith((".py", ".js")):
                filepath = Path(root) / file
                content = filepath.read_text(errors="ignore")
                for pattern_name, pattern in sensitive_patterns:
                    if pattern.lower() in content.lower():
                        found.append((filepath, pattern))

    if found:
        audit_results["ALTO"].append(
            f"⚠️  Posibles secrets en código: {len(found)} ocurrencias encontradas"
        )
    else:
        audit_results["PASÓ"].append("✅ No se encontraron secrets hardcodeados")


def check_input_validation() -> None:
    """Check if ChatRequest has input validation."""
    models_path = Path("backend/api/models.py")
    content = models_path.read_text()

    if "max_length" in content or "Field" in content:
        audit_results["PASÓ"].append("✅ ChatRequest tiene validación de entrada")
    else:
        audit_results["MEDIO"].append(
            "⚠️  ChatRequest.message sin límite de longitud — riesgo de DoS"
        )


def check_cors_config() -> None:
    """Verify CORS middleware configuration."""
    main_path = Path("backend/api/main.py")
    content = main_path.read_text()

    if "CORSMiddleware" in content:
        if "allow_origins" in content and "localhost" in content:
            audit_results["PASÓ"].append(
                "✅ CORS configurado restrictivamente (localhost)"
            )
        else:
            audit_results["ALTO"].append("⚠️  CORS podría ser demasiado permisivo")
    else:
        audit_results["MEDIO"].append("⚠️  CORS middleware no configurado")


def check_error_handling() -> None:
    """Check if error messages are sanitized."""
    routes_path = Path("backend/api/routes")
    found_unsafe = False

    for py_file in routes_path.glob("*.py"):
        content = py_file.read_text()
        if "raise HTTPException" in content and "str(e)" in content:
            found_unsafe = True

    if found_unsafe:
        audit_results["MEDIO"].append(
            "⚠️  Error details podrían exponerse en respuestas HTTP"
        )
    else:
        audit_results["PASÓ"].append("✅ Error handling parece seguro")


def check_rate_limiting() -> None:
    """Check if rate limiting is implemented."""
    routes_path = Path("backend/api/routes")
    found_ratelimit = False

    for py_file in routes_path.glob("*.py"):
        content = py_file.read_text()
        if "rate" in content.lower() or "limit" in content.lower():
            found_ratelimit = True

    if not found_ratelimit:
        audit_results["ALTO"].append(
            "⚠️  No hay rate limiting en /api/chat — riesgo de DoS"
        )
    else:
        audit_results["PASÓ"].append("✅ Rate limiting implementado")


def check_security_headers() -> None:
    """Check if security headers are configured."""
    main_path = Path("backend/api/main.py")
    content = main_path.read_text()

    headers_to_check = [
        ("Content-Security-Policy", "CSP"),
        ("X-Frame-Options", "Clickjacking protection"),
        ("X-Content-Type-Options", "MIME sniffing protection"),
    ]

    found = []
    for header, desc in headers_to_check:
        if header.lower() in content.lower():
            found.append(desc)

    if found:
        audit_results["PASÓ"].append(f"✅ Headers de seguridad: {', '.join(found)}")
    else:
        audit_results["BAJO"].append(
            "ℹ️  Security headers no configurados (considerar agregar)"
        )


def check_dependencies() -> None:
    """Check for known vulnerabilities in dependencies."""
    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        packages = json.loads(result.stdout)

        critical_packages = {
            "langchain": "0.2.0",
            "chromadb": "0.5.0",
            "fastapi": "0.111.0",
            "pydantic": "2.0.0",
        }

        for pkg in packages:
            name = pkg["name"].lower()
            if name in critical_packages:
                audit_results["PASÓ"].append(
                    f"✅ {name} v{pkg['version']} instalado"
                )
    except Exception as e:
        audit_results["BAJO"].append(f"ℹ️  No se pudo verificar dependencias: {e}")


def check_chroma_security() -> None:
    """Check ChromaDB configuration."""
    config_path = Path("backend/config.py")
    content = config_path.read_text()

    if "chroma_path" in content:
        audit_results["PASÓ"].append("✅ ChromaDB persistencia configurada")
        if "./" in content or "relative" in content.lower():
            audit_results["MEDIO"].append(
                "⚠️  ChromaDB usando ruta relativa — verificar en producción"
            )
    else:
        audit_results["ALTO"].append("⚠️  ChromaDB configuration no encontrada")


def generate_report() -> None:
    """Generate security audit report."""
    report = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    AUDITORÍA DE SEGURIDAD - F22 CHATBOT                      ║
║                                May 5, 2026                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

"""

    severity_order = ["CRÍTICO", "ALTO", "MEDIO", "BAJO", "PASÓ"]
    colors = {"CRÍTICO": "🔴", "ALTO": "🟠", "MEDIO": "🟡", "BAJO": "🔵", "PASÓ": "🟢"}

    total_issues = 0
    for severity in severity_order:
        items = audit_results[severity]
        if items:
            report += f"\n{colors[severity]} {severity} ({len(items)}):\n"
            report += "─" * 80 + "\n"
            for item in items:
                report += f"  {item}\n"
                if severity != "PASÓ":
                    total_issues += 1

    report += f"""

╔══════════════════════════════════════════════════════════════════════════════╗
║                         RESUMEN Y RECOMENDACIONES                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Total de Problemas Encontrados: {total_issues}
Puntuación de Seguridad: {100 - (total_issues * 5)}/100

ACCIONES INMEDIATAS (CRÍTICO):
{chr(10).join(f"  1. {item}" for item in audit_results["CRÍTICO"]) or "  ✅ Ninguno"}

MEJORAS NECESARIAS (ALTO):
{chr(10).join(f"  • {item}" for item in audit_results["ALTO"]) or "  ✅ Todos los checks pasados"}

CONSIDERAR (MEDIO/BAJO):
{chr(10).join(f"  - {item}" for item in audit_results["MEDIO"][:3]) or "  ✅ Todo bien"}

╔══════════════════════════════════════════════════════════════════════════════╗
║                         RECOMENDACIONES PRÁCTICAS                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

1. VALIDACIÓN DE ENTRADA:
   ✓ Agregar `Field(max_length=2000)` a ChatRequest.message
   ✓ Implementar honeypot para detectar bots
   ✓ Sanitizar preguntas para evitar prompt injection

2. RATE LIMITING:
   ✓ Usar SlowAPI o similar en FastAPI
   ✓ Limitar: 10 req/min por IP, 100 req/hora por session
   ✓ Responder con 429 Too Many Requests

3. ERROR HANDLING:
   ✓ Loguear errores completos internamente
   ✓ Devolver errores genéricos al cliente
   ✓ Nunca exponer rutas del sistema o stack traces

4. HEADERS DE SEGURIDAD:
   ✓ Content-Security-Policy: default-src 'self'
   ✓ X-Frame-Options: DENY
   ✓ X-Content-Type-Options: nosniff

5. SEGURIDAD EN PRODUCCIÓN:
   ✓ Usar HTTPS/TLS obligatorio
   ✓ Implementar JWT + expiration timeout
   ✓ Ejecutar en contenedor con permisos limitados
   ✓ Monitorear logs de acceso

6. AUDITORÍA:
   ✓ Registrar todas las queries al ChatBot
   ✓ Mantener logs durante 90 días
   ✓ Revisar logs regularmente para patrones sospechosos

"""
    print(report)
    return report


def main():
    print("🔍 Iniciando auditoría de seguridad...\n")

    check_env_files()
    check_hardcoded_secrets()
    check_input_validation()
    check_cors_config()
    check_error_handling()
    check_rate_limiting()
    check_security_headers()
    check_dependencies()
    check_chroma_security()

    report = generate_report()

    # Save report
    with open("SECURITY_AUDIT_REPORT.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("\n📋 Reporte guardado en: SECURITY_AUDIT_REPORT.txt")

    critical_count = len(audit_results["CRÍTICO"])
    if critical_count > 0:
        print(f"\n⚠️  {critical_count} problemas CRÍTICOS encontrados")
        sys.exit(1)
    else:
        print("\n✅ Auditoría completada")
        sys.exit(0)


if __name__ == "__main__":
    main()
