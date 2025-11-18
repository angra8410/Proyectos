# Proyectos

Este repositorio central agrupa los proyectos de data y ML que construiremos para tu portafolio.  
Idea: cada proyecto vive en `projects/NN_<nombre>/` con su propio README, scripts, notebooks y requirements.

Cómo trabajaremos
- Iteraciones pequeñas (MVPs) por proyecto.
- Workflow: rama `main` estable + rama `dev` para trabajo diario + branches feature/issue para tareas.
- Issues por tarea; PRs desde branches feature -> dev -> main.
- Yo te guío paso a paso: tú ejecutas y pegas salidas/errores; yo te explico y corrigo.

Estructura recomendada
- projects/01_EDA_Canciones/: EDA con Spotify API (audio_features + metadata)
- projects/02_Olympics_Medals/: Medalleros, ETL y visualizaciones
- projects/03_...: siguientes proyectos

Primeros pasos locales
1. Clona el repo.
2. Crea una rama para el proyecto en el que trabajes:
   ```bash
   git checkout -b dev
   git checkout -b feature/01-eda-ingest
   ```
3. Crea issues para tareas pequeñas y abre PRs cuando completes un bloque.

Si quieres que cree este repo en GitHub con este scaffold, indícame:
- owner/repo (por ejemplo `angra8410/Proyectos`)
- visibilidad: `public` o `private`

¡Empecemos!
