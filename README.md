# CourtLab AI — MVP de desarrollo individual de básquetbol

Una aplicación web en español para organizar el entrenamiento, registrar el progreso, consultar un asistente de básquet y analizar un clip de tiro mediante estimación de puntos corporales.

## Qué incluye

- **Inicio y perfil del jugador:** posición, nivel, mano dominante, objetivo y contexto de entrenamiento.
- **Coach IA:** asistente conversacional con el API de OpenAI cuando se configura una clave; si no, queda disponible un modo guiado con respuestas predefinidas y planes básicos.
- **Laboratorio de tiro:** carga y vista previa de un clip; análisis de puntos corporales con MediaPipe; estimación de ángulo de codo, ángulo aproximado de rodillas, inclinación de tronco, posición relativa de muñeca y tiempo aproximado de ascenso de muñeca.
- **Armador de sesiones y biblioteca:** progresiones de tiro, dribbling, finalizaciones, lectura y preparación física.
- **Seguimiento:** registro de duración, tipo de sesión, encestes/intentos, notas, tendencias semanales y exportación JSON.
- **Fuentes de coaching:** referencias públicas para explorar fundamentos de tiro y aprendizaje de habilidades en contexto.
- **Persistencia local:** perfil, historial y conversación se guardan en `localStorage` del navegador.

## Requisitos

- Python 3.11 recomendado.
- Conexión a internet la primera vez para instalar dependencias y descargar el modelo liviano de MediaPipe al analizar el primer video.
- Una clave de OpenAI y facturación/crédito del API si querés habilitar respuestas generativas reales. La aplicación no incluye una clave.

## Instalación en Windows

1. Descomprimí la carpeta `courtlab-ai`.
2. Instalá Python 3.11 desde <https://www.python.org/downloads/> y marcá la opción **Add Python to PATH**.
3. Abrí la carpeta y ejecutá `start_windows.bat`. El archivo crea el entorno virtual, instala dependencias y levanta el servidor.
4. Abrí <http://127.0.0.1:8000> en Chrome o Edge.
5. Para activar la IA generativa, abrí el archivo `.env` (se crea desde `.env.example`), pegá tu clave en `OPENAI_API_KEY=` y reiniciá el servidor. Podés crear una clave desde <https://platform.openai.com/api-keys>.

Si preferís instalar manualmente, desde una terminal en la carpeta:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env  # Windows; si ya existe .env, no lo sobrescribas
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## Limitaciones importantes del análisis de tiro

Esta versión usa MediaPipe para estimar puntos corporales; **no identifica la pelota de manera independiente**. Por eso, el tiempo reportado es una estimación del comienzo del ascenso de la muñeca hasta su punto más alto, no el instante exacto en que la pelota abandona la mano. La detección depende de la iluminación, perspectiva, oclusiones y encuadre. Una medición robusta de release real requeriría detección y seguimiento de la pelota y calibración temporal, y debería validarse contra video de alta velocidad.

Los ángulos se describen como mediciones del clip, no como una puntuación médica ni como prueba de una mecánica universalmente perfecta. Compará varios tiros con la misma cámara/distancia y usá las observaciones junto a un entrenador.

## Datos, privacidad y seguridad

- La aplicación guarda perfil, registros y conversación en el navegador actual mediante `localStorage`.
- El clip se envía solamente al servidor que ejecuta CourtLab. El servidor lo procesa en un archivo temporal y lo elimina después del análisis. El video no se envía al API generativo.
- Cuando se activa la IA, el mensaje, parte del perfil y el contexto de métricas que se le pide analizar se envían al proveedor del API configurado.
- Esta es una versión MVP local, sin registro de usuarios, roles, base de datos multiusuario ni medidas completas de privacidad. **No la publiques en un servidor accesible desde internet sin agregar autenticación, límites de carga, controles de acceso, política de privacidad y medidas de seguridad.**
- No subas claves de API a repositorios públicos. Mantené `.env` privado.

## Fuentes de contexto utilizadas

- Dave Hopla — recursos públicos sobre técnica de tiro y tiro tras bote: <https://www.davehopla.com/shooting-videos/>
- Drew Hanlen / Pure Sweat Basketball — programas públicos por posición y rutinas de tiro: <https://puresweatbasketball.com/transform> y <https://puresweatbasketball.com/10kclub>
- Basketball Immersion — ejercicios de tiro con toma de decisiones y desarrollo de 1 contra 1: <https://basketballimmersion.com/how-to-use-the-constraints-led-approach-for-a-realistic-basketball-shooting-drill/> y <https://basketballimmersion.com/using-the-cla-to-develop-1-on-1-skills/>
- USA Basketball — biblioteca pública de fundamentos y ejercicios: <https://www.usab.com/coaching/coaching-resources/skills-drills-coaching-foundational>
- By Any Means Coaches — filosofía de desarrollo y aprendizaje de habilidades: <https://byanymeanscoaches.com/about>
- Google AI Edge — MediaPipe Pose Landmarker: <https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python>
- OpenAI Responses API — referencia oficial: <https://developers.openai.com/api/reference/python/resources/responses>

Las perspectivas se resumen en lenguaje propio; no son citas textuales ni implican patrocinio o aprobación de los entrenadores o sitios enlazados.

## Desarrollo y próximos pasos

Esta versión funciona como prototipo listo para ejecutar localmente. Para convertirla en un producto público de nivel profesional, los próximos hitos serían: detección de pelota para medir el release de forma más precisa; análisis desde distintos ángulos con calibración; una base de datos con usuarios y sincronización; tests de validación con entrenadores; sistema de permisos y privacidad; y un corpus de ejercicios revisado por entrenadores reales con fuentes y versionado.
