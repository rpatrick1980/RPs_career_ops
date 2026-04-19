# Modo: pipeline — Inbox de URLs (Second Brain)

Procesa URLs de ofertas acumuladas en `data/pipeline.md`. El usuario agrega URLs cuando quiera y luego ejecuta `/career-ops pipeline` para procesarlas todas.

## Workflow

1. **Leer** `data/pipeline.md` → buscar items `- [ ]` en la sección "Pendientes"
2. **Para cada URL pendiente**:
   a. Calcular siguiente `REPORT_NUM` secuencial (leer `reports/`, tomar el número más alto + 1)
   b. **Extraer JD** usando Playwright (browser_navigate + browser_snapshot) → WebFetch → WebSearch
   c. Si la URL no es accesible → marcar como `- [!]` con nota y continuar
   d. **Ejecutar auto-pipeline completo**: Evaluación A-F → Report .md → PDF (si score >= 3.0) → Tracker
   e. **Mover de "Pendientes" a "Procesadas"**: `- [x] #NNN | URL | Empresa | Rol | Score/5 | PDF ✅/❌`
3. **Si hay 3+ URLs pendientes**, lanzar agentes en paralelo (Agent tool con `run_in_background`) para maximizar velocidad.
4. **Al terminar**, mostrar tabla resumen:

```
| # | Empresa | Rol | Score | PDF | Acción recomendada |
```

## Formato de pipeline.md

```markdown
## Pendientes
- [ ] https://jobs.example.com/posting/123
- [ ] https://boards.greenhouse.io/company/jobs/456 | Company Inc | Senior PM
- [!] https://private.url/job — Error: login required

## Procesadas
- [x] #143 | https://jobs.example.com/posting/789 | Acme Corp | AI PM | 4.2/5 | PDF ✅
- [x] #144 | https://boards.greenhouse.io/xyz/jobs/012 | BigCo | SA | 2.1/5 | PDF ❌
```

## Detección inteligente de JD desde URL

1. **`local:` prefix (NUEVO):** Si la URL comienza con `local:`, leer el archivo local desde el proyecto.
   - Ejemplo: `local:jds/bank-julius-baer-it-service-owner.md` → leer `jds/bank-julius-baer-it-service-owner.md`
   - Ventaja: Sin re-fetching, JD ya capturado durante scan. Más rápido.
   - Fallback: Si archivo no existe o está dañado, marcar `[!]` y avisar al usuario
   
2. **Playwright (preferido para URLs web):** `browser_navigate` + `browser_snapshot`. Funciona con todas las SPAs.
   - Si JD se extrae exitosamente:
     - **NUEVO**: Generar slug (ver `modes/jd-slug-generator.md`)
     - **NUEVO**: Guardar JD a `jds/{slug}.md` para futuras referencias
     - Actualizar `pipeline.md` para usar `local:jds/` en futuras ejecuciones

3. **WebFetch (fallback):** Para páginas estáticas o cuando Playwright no está disponible.
   - Si JD extraído exitosamente: También guardar a `jds/{slug}.md`

4. **WebSearch (último recurso):** Buscar en portales secundarios que indexan el JD.
   - Usar después de fallos con métodos anteriores

**Casos especiales:**
- **LinkedIn**: Puede requerir login → marcar `[!]` y pedir al usuario que pegue el texto
- **PDF**: Si la URL apunta a un PDF, leerlo directamente con Read tool
- **Archivos locales con `local:` prefix**: Soportados desde scan.md (JDs guardados)

## Numeración automática

1. Listar todos los archivos en `reports/`
2. Extraer el número del prefijo (e.g., `142-medispend...` → 142)
3. Nuevo número = máximo encontrado + 1

## Sincronización de fuentes

Antes de procesar cualquier URL, verificar sync:
```bash
node cv-sync-check.mjs
```
Si hay desincronización, advertir al usuario antes de continuar.
