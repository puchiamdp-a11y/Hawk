"""
Test de integración SYNA Tracking en Hawk
Verifica que el botón y la pantalla están correctamente integrados
"""

import ast
import re


def verificar_integracion():
    """Verifica que la integración SYNA en app.py es correcta."""

    print("=" * 60)
    print("TEST DE INTEGRACIÓN: SYNA Tracking en Hawk")
    print("=" * 60)
    print()

    # Leer app.py
    with open('app.py', 'r') as f:
        contenido = f.read()

    checks = []

    # CHECK 1: Importes
    print("✓ Verificando imports...")
    checks.append((
        "Import syna_db",
        "from syna_db import inicializar_db" in contenido
    ))
    checks.append((
        "Import syna_ui",
        "from syna_ui import pantalla_syna_admin" in contenido
    ))
    checks.append((
        "Import syna_viewer",
        "from syna_viewer import pantalla_syna_viewer, pantalla_syna_con_autenticacion" in contenido
    ))

    # CHECK 2: Botón en sidebar
    print("✓ Verificando botón en sidebar...")
    boton_pattern = r'st\.button\("📊 Cobranzas SYNA".*key="btn_syna"'
    checks.append((
        "Botón '📊 Cobranzas SYNA' existe",
        bool(re.search(boton_pattern, contenido))
    ))

    # Verificar que está dentro del bloque sidebar
    sidebar_section = re.search(r'with st\.sidebar:(.*?)(?=# )', contenido, re.DOTALL)
    if sidebar_section:
        checks.append((
            "Botón está dentro de 'with st.sidebar'",
            bool(re.search(boton_pattern, sidebar_section.group(1)))
        ))

    # CHECK 3: Pantalla SYNA
    print("✓ Verificando pantalla en switch de navegación...")
    pantalla_pattern = r'elif pantalla_actual == "Cobranzas SYNA":'
    checks.append((
        "Condición 'Cobranzas SYNA' existe",
        bool(re.search(pantalla_pattern, contenido))
    ))

    # Verificar que llama a pantalla_syna_admin()
    checks.append((
        "Llama a pantalla_syna_admin()",
        "pantalla_syna_admin()" in contenido
    ))

    # CHECK 4: Inicialización de BD
    print("✓ Verificando inicialización de BD...")
    checks.append((
        "Llama a inicializar_db()",
        "inicializar_db()" in contenido
    ))

    # CHECK 5: Detección de role=viewer
    print("✓ Verificando autenticación Cintia...")
    checks.append((
        "Detecta role=viewer",
        'query_params.get("role") == "viewer"' in contenido
    ))
    checks.append((
        "Llama a pantalla_syna_con_autenticacion()",
        "pantalla_syna_con_autenticacion()" in contenido
    ))
    checks.append((
        "Llama a pantalla_syna_viewer()",
        "pantalla_syna_viewer()" in contenido
    ))

    # CHECK 6: Sintaxis
    print("✓ Verificando sintaxis...")
    try:
        ast.parse(contenido)
        checks.append(("Sintaxis válida", True))
    except SyntaxError as e:
        checks.append(("Sintaxis válida", False))

    # Mostrar resultados
    print()
    print("=" * 60)
    print("RESULTADOS")
    print("=" * 60)
    print()

    for desc, resultado in checks:
        estado = "✅" if resultado else "❌"
        print(f"{estado} {desc}")

    total = len(checks)
    pasadas = sum(1 for _, r in checks if r)

    print()
    print("=" * 60)
    print(f"RESUMEN: {pasadas}/{total} checks pasados")
    print("=" * 60)
    print()

    if pasadas == total:
        print("🎉 INTEGRACIÓN CORRECTA")
        print()
        print("Si el botón no aparece:")
        print("1. Limpia cache del navegador (Ctrl+Shift+Delete)")
        print("2. Recarga la página (Ctrl+R o F5)")
        print("3. Detén Streamlit: Ctrl+C")
        print("4. Reinicia: streamlit run app.py")
        print()
        print("El botón '📊 Cobranzas SYNA' debería estar en el sidebar")
        print("después de 'Post Emisión' y antes de 'Actualizar'")
    else:
        print(f"⚠️ {total - pasadas} checks fallaron - Revisar arriba")

    return pasadas == total


if __name__ == "__main__":
    exito = verificar_integracion()
    exit(0 if exito else 1)
