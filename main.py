from __future__ import annotations

import math
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "pose_landmarker_lite.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)

app = FastAPI(title="CourtLab AI", version="1.0.0", description="Asistente de desarrollo individual de básquetbol")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

COACHING_LIBRARY = """
BASE DE CONOCIMIENTO DE COURTLAB (síntesis original de recursos públicos; no son citas ni consenso universal):
1) Perspectiva de tiro de Dave Hopla: sus recursos públicos cubren técnica básica, tiros tras bote y lectura de pantallas. CourtLab traduce esta lente en series con un objetivo claro, registrar aciertos/intentos y corregir un detalle observable por vez. No confundir volumen con práctica de calidad.
2) Perspectiva de desarrollo de habilidades de Drew Hanlen / Pure Sweat Basketball: sus programas públicos ofrecen rutinas estructuradas por posición y trabajo de habilidades con contexto de juego. CourtLab usa esa idea general para adaptar foco y desafío a la posición, y proponer progresiones medibles sin reproducir material de pago.
3) Perspectiva de Basketball Immersion / Chris Oliver y el enfoque basado en restricciones (CLA): alternar técnica útil con decisiones reales; variar pase, distancia, ritmo, ángulo, defensor y tiempo. El objetivo no es hacer un movimiento bonito, sino leer y resolver el problema de juego.
4) Progresión fundamental de USA Basketball: combinar manejo de balón, pase y recepción, tiro, juego de pies/control corporal, ataque y defensa, con progresiones que se ajustan al nivel del jugador.
5) Perspectiva de By Any Means Coaches: integrar distintos métodos, aprendizaje de habilidades y situaciones representativas del juego en lugar de imponer una única escuela rígida.
6) Manejo de balón: postura atlética equilibrada, cambios de ritmo, proteger el balón con el cuerpo, dominar ambas manos y levantar la vista. Progresar de control a velocidad y luego a lectura con oposición.
7) Finalizaciones: practicar ambos lados, diferentes alturas y ángulos, usar el tablero cuando corresponda, despegar con equilibrio y leer la ayuda; no repetir siempre la misma bandeja sin estímulo defensivo.
8) Planificación: priorizar 1–2 objetivos por sesión, dosificar carga, descansar y registrar resultados. Detenerse ante dolor agudo, mareo o síntomas preocupantes. Para lesiones o dolor persistente, consultar a un profesional sanitario.
FUENTES PÚBLICAS DE CONTEXTO:
- Dave Hopla, recursos de fundamentos de tiro y tiro tras bote: https://www.davehopla.com/shooting-videos/
- Pure Sweat Basketball / Drew Hanlen, programas de habilidades por posición y rutinas de tiro: https://puresweatbasketball.com/transform y https://puresweatbasketball.com/10kclub
- Basketball Immersion, enfoque de restricciones y toma de decisiones en tiro: https://basketballimmersion.com/how-to-use-the-constraints-led-approach-for-a-realistic-basketball-shooting-drill/
- Basketball Immersion, desarrollo de habilidades 1 contra 1 en contexto: https://basketballimmersion.com/using-the-cla-to-develop-1-on-1-skills/
- USA Basketball, biblioteca pública de fundamentos y ejercicios: https://www.usab.com/coaching/coaching-resources/skills-drills-coaching-foundational
- By Any Means Coaches, filosofía que combina enfoques y entrenamiento basado en el juego: https://byanymeanscoaches.com/about
- MediaPipe Pose Landmarker, documentación técnica para estimación de puntos corporales: https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python
""".strip()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    profile: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, str]] = Field(default_factory=list)


class LogRequest(BaseModel):
    pass


def api_key_set() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status():
    return {
        "ok": True,
        "app": "CourtLab AI",
        "ai_configured": api_key_set(),
        "video_analysis_available": _video_dependencies_available(),
        "model_downloaded": MODEL_PATH.exists(),
        "message": "IA generativa activa" if api_key_set() else "Modo guiado: configurá OPENAI_API_KEY para activar la IA generativa",
    }


def _video_dependencies_available() -> bool:
    try:
        import cv2  # noqa: F401
        import mediapipe  # noqa: F401
        return True
    except Exception:
        return False


def _fallback_coach(message: str, profile: dict[str, Any], context: dict[str, Any]) -> str:
    msg = message.lower()
    position = str(profile.get("position", "jugador/a"))
    level = str(profile.get("level", "intermedio"))
    if any(k in msg for k in ["tiro", "lanzamiento", "mecánica", "mecanica", "triples"]):
        return (
            "**Plan de tiro para hoy (modo guiado):**\n\n"
            "1. **Cerca del aro — 20 encestes.** Una mano al principio; terminá con la muñeca relajada y sostené el follow-through.\n"
            "2. **Pies preparados — 5 zonas × 5 encestes.** Recibí el pase con los pies listos y registrá aciertos/intentos.\n"
            "3. **Tiro tras bote — 3 series de 5 por lado.** Un solo cambio de ritmo, frenada equilibrada y tiro.\n"
            "4. **Medí el resultado:** porcentaje = encestes ÷ intentos × 100. Filmá 5 tiros desde el costado y 5 desde el frente.\n\n"
            "No voy a afirmar cuál es tu error mecánico sin ver un video claro. Cuando actives la IA con una clave de API, podré adaptar la explicación a tu perfil y a tus métricas."
        )
    if any(k in msg for k in ["drib", "bote", "manejo", "balón", "balon"]):
        return (
            "**Rutina de manejo de balón (15 minutos):**\n\n"
            "- 3 min: bote bajo y alto, derecha e izquierda, sin mirar el balón.\n"
            "- 3 min: crossovers controlados; 3 × 30 s con 15 s de descanso.\n"
            "- 3 min: cambio de ritmo y salida explosiva, 5 repeticiones por lado.\n"
            "- 3 min: dos botes máximo para atacar una línea y frenar equilibrado.\n"
            "- 3 min: 1 contra 1 o ejercicio con una señal visual que te obligue a decidir.\n\n"
            "Como perfil **" + position + "** de nivel **" + level + "**, priorizá el cambio de ritmo y terminar cada acción con una decisión, no solo hacer trucos rápidos."
        )
    if any(k in msg for k in ["bandeja", "finaliz", "aro", "terminar"]):
        return (
            "**Finalizaciones — 18 minutos:**\n\n"
            "1. 10 bandejas por lado con la mano exterior.\n"
            "2. 8 finalizaciones con cambio de ángulo después de un bote.\n"
            "3. 3 × 4 repeticiones: finalización con contacto simulado y equilibrio.\n"
            "4. Cerrá con 3 × 45 s de 1 contra 1 desde una ventaja pequeña; leé al defensor en vez de elegir la finalización antes de empezar.\n\n"
            "Registrá cuántas convertís por lado. Si cae mucho la calidad, descansá y bajá la velocidad."
        )
    if any(k in msg for k in ["salto", "fuerza", "explos", "velocidad", "fisic"]):
        return (
            "**Bloque atlético prudente:** calentamiento dinámico de 8–10 min; 3 × 3 saltos de calidad con descanso amplio; 3 × 4 aceleraciones cortas si la técnica es buena; y fuerza básica 3 × 5–8 con carga controlada. No hagas saltos máximos fatigado ni aumentes volumen de golpe. Si aparece dolor, pará. Adaptá esto con tu entrenador y la carga de partidos."
        )
    return (
        "¡Vamos a trabajarlo como un entrenador! Decime tu objetivo concreto —tiro, dribbling, finalizaciones, lectura de juego, salto o preparación física—, tu nivel y cuántos días podés entrenar.\n\n"
        "Mientras la IA generativa no esté configurada, puedo ofrecerte planes guiados y ejercicios guardados en la aplicación. Para respuestas realmente conversacionales y personalizadas, agregá tu `OPENAI_API_KEY` al archivo `.env`."
    )


@app.post("/api/chat")
def chat(req: ChatRequest):
    if not api_key_set():
        return {"reply": _fallback_coach(req.message, req.profile, req.context), "mode": "guided"}

    try:
        from openai import OpenAI

        model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        instructions = f"""Sos CourtLab, un asistente de desarrollo de básquetbol para jugadores y entrenadores. Respondé en español rioplatense natural, práctico, específico y alentador, sin prometer resultados mágicos.

Tu base de principios y perspectivas públicas es:
{COACHING_LIBRARY}

Reglas:
- No digas que hablás en nombre de los entrenadores/fuentes ni inventes citas o consensos. Presentá enfoques como perspectivas, y separá opinión de evidencia.
- Personalizá según el perfil y contexto aportados. Si falta un dato importante, hacé como máximo una pregunta breve, pero ofrecé un primer paso útil.
- Cada rutina debe tener objetivo, duración, series/repeticiones, descanso y forma de medir el progreso.
- Para mecánica, diferenciá lo que se observa de lo que se infiere; no diagnostiques solo por métricas aproximadas. Si no hay análisis de video en contexto, no inventes ángulos ni tiempos.
- No prometas identificar con precisión el instante de salida de la pelota: la versión actual estima la elevación de la muñeca y no detecta la pelota independientemente.
- Priorizá toma de decisiones en contexto además de repetición aislada; recomendá variar estímulos y progresar.
- No ofrezcas consejos médicos. Ante dolor agudo, mareos o lesión persistente, recomendá parar y consultar un profesional sanitario.
- No propongas dietas extremas ni entrenamientos máximos diarios. Ajustá carga si hay partidos o fatiga.
- Evitá introducciones largas. Terminá con una tarea concreta que el jugador pueda ejecutar hoy.

Perfil jugador: {req.profile}
Contexto de la app/métricas: {req.context}
"""
        history_text = "\n".join(
            f"{('Jugador' if item.get('role') == 'user' else 'CourtLab')}: {str(item.get('content', ''))[:1200]}"
            for item in req.history[-8:]
        )
        user_input = f"Conversación reciente:\n{history_text or '(sin mensajes anteriores)'}\n\nMensaje actual del jugador:\n{req.message}"
        result = client.responses.create(model=model, instructions=instructions, input=user_input)
        reply = getattr(result, "output_text", "") or "No pude generar una respuesta completa. Probá de nuevo."
        return {"reply": reply, "mode": "ai", "model": model}
    except Exception as exc:
        # Avoid returning secrets or raw provider details to the browser.
        print(f"Error in AI endpoint: {type(exc).__name__}: {exc}")
        return {
            "reply": "No pude conectar con el servicio de IA. Revisá tu clave, conexión y el nombre del modelo en el archivo .env. Mientras tanto, podés usar los ejercicios y planes guiados.",
            "mode": "error",
        }


def _angle(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float | None:
    """Angle ABC in degrees for normalized image-coordinate points."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    denom = math.hypot(*ba) * math.hypot(*bc)
    if denom < 1e-8:
        return None
    cosine = max(-1.0, min(1.0, (ba[0] * bc[0] + ba[1] * bc[1]) / denom))
    return math.degrees(math.acos(cosine))


def _ensure_pose_model() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists():
        return
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    except Exception as exc:
        raise RuntimeError("No se pudo descargar el modelo de postura de MediaPipe. Verificá la conexión a internet.") from exc


def _analyze_video(video_path: str, dominant_hand: str) -> dict[str, Any]:
    try:
        import cv2
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
    except Exception as exc:
        raise RuntimeError("Falta OpenCV o MediaPipe. Instalá las dependencias con `pip install -r requirements.txt`.") from exc

    _ensure_pose_model()
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir el video. Probá con MP4 (H.264) o MOV.")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps > 0 else 0
    if duration > 45:
        cap.release()
        raise RuntimeError("El video dura más de 45 segundos. Recortá un clip de 3 a 10 segundos para un análisis más útil.")

    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.35,
        min_pose_presence_confidence=0.35,
        min_tracking_confidence=0.35,
    )
    samples: list[dict[str, Any]] = []
    stride = max(1, int(fps / 15))  # sample approximately 15 frames/second
    frame_index = 0
    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % stride == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp_ms = int(frame_index * 1000 / fps)
                result = landmarker.detect_for_video(mp_image, timestamp_ms)
                if result.pose_landmarks:
                    lm = result.pose_landmarks[0]
                    def pt(idx: int) -> tuple[float, float]:
                        return (float(lm[idx].x), float(lm[idx].y))
                    # MediaPipe pose index: 11/12 shoulders, 13/14 elbows, 15/16 wrists,
                    # 23/24 hips, 25/26 knees, 27/28 ankles.
                    if dominant_hand == "left":
                        shoulder_i, elbow_i, wrist_i = 11, 13, 15
                        hip_i, knee_i, ankle_i = 23, 25, 27
                    else:
                        shoulder_i, elbow_i, wrist_i = 12, 14, 16
                        hip_i, knee_i, ankle_i = 24, 26, 28
                    visibility = float(min(lm[shoulder_i].visibility, lm[elbow_i].visibility, lm[wrist_i].visibility))
                    shoulder, elbow, wrist = pt(shoulder_i), pt(elbow_i), pt(wrist_i)
                    hip, knee, ankle = pt(hip_i), pt(knee_i), pt(ankle_i)
                    left_knee = _angle(pt(23), pt(25), pt(27))
                    right_knee = _angle(pt(24), pt(26), pt(28))
                    shoulder_mid = ((pt(11)[0] + pt(12)[0]) / 2, (pt(11)[1] + pt(12)[1]) / 2)
                    hip_mid = ((pt(23)[0] + pt(24)[0]) / 2, (pt(23)[1] + pt(24)[1]) / 2)
                    torso_dx = shoulder_mid[0] - hip_mid[0]
                    torso_dy = shoulder_mid[1] - hip_mid[1]
                    torso_lean = abs(math.degrees(math.atan2(torso_dx, -torso_dy))) if math.hypot(torso_dx, torso_dy) > 0.001 else None
                    samples.append({
                        "time": frame_index / fps,
                        "wrist_y": wrist[1],
                        "wrist_x": wrist[0],
                        "shoulder_y": shoulder[1],
                        "wrist_above_shoulder": shoulder[1] - wrist[1],
                        "elbow_angle": _angle(shoulder, elbow, wrist),
                        "knee_angle": sum(v for v in (left_knee, right_knee) if v is not None) / max(1, sum(v is not None for v in (left_knee, right_knee))),
                        "torso_lean": torso_lean,
                        "visibility": visibility,
                    })
            frame_index += 1
    cap.release()

    usable = [sample for sample in samples if sample["visibility"] >= 0.2]
    if len(usable) < 5:
        raise RuntimeError("No pude seguir bien hombro, codo y muñeca. Filmá el cuerpo completo, con buena luz y sin tapar el brazo de tiro.")

    apex_idx = min(range(len(usable)), key=lambda i: usable[i]["wrist_y"])
    apex = usable[apex_idx]
    # Approximate onset as the first sustained upward wrist movement before the apex.
    onset_idx = None
    search_start = max(0, apex_idx - int(2.5 * max(5, len(usable) / max(duration, 0.1))))
    for i in range(search_start, max(search_start, apex_idx - 2)):
        ys = [s["wrist_y"] for s in usable[i:i + 4]]
        if len(ys) == 4 and ys[0] > ys[1] > ys[2] and ys[3] <= ys[2] + 0.008 and (ys[0] - min(ys)) >= 0.025:
            onset_idx = i
            break
    estimated_raise_time = None
    if onset_idx is not None and apex_idx > onset_idx:
        estimated_raise_time = round(apex["time"] - usable[onset_idx]["time"], 2)

    def median_metric(key: str, subset: list[dict[str, Any]]) -> float | None:
        values = sorted(float(s[key]) for s in subset if s.get(key) is not None and math.isfinite(float(s[key])))
        if not values:
            return None
        mid = len(values) // 2
        return round(values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2, 1)

    pre_apex = usable[max(0, apex_idx - 2):apex_idx + 1] or [apex]
    metrics = {
        "duration_seconds": round(duration, 2),
        "sampled_frames": len(usable),
        "estimated_wrist_raise_seconds": estimated_raise_time,
        "elbow_angle_at_apex_degrees": median_metric("elbow_angle", pre_apex),
        "knee_angle_near_apex_degrees": median_metric("knee_angle", pre_apex),
        "trunk_lean_degrees": median_metric("torso_lean", pre_apex),
        "wrist_above_shoulder_normalized": round(float(apex["wrist_above_shoulder"]), 3),
        "confidence": "media" if len(usable) >= 18 else "baja",
    }

    observations: list[str] = []
    elbow = metrics["elbow_angle_at_apex_degrees"]
    if elbow is not None:
        if elbow < 125:
            observations.append("En el punto más alto observado, el codo seguía bastante flexionado. Revisá si soltás el balón con espacio y sin forzar una extensión artificial.")
        elif elbow > 178:
            observations.append("El codo aparece casi completamente extendido cerca del punto más alto. Comprobá en el video si el balón ya salió y evitá bloquear la articulación con tensión.")
        else:
            observations.append("El ángulo del codo cerca del punto más alto quedó registrado. Comparalo entre varios tiros; un solo fotograma no determina si la mecánica es buena o mala.")
    if metrics["wrist_above_shoulder_normalized"] < 0:
        observations.append("La muñeca no llegó por encima del hombro en el fotograma más alto detectado. Revisá encuadre y si el clip incluye todo el gesto: podría deberse a la perspectiva o a que el video no captó la preparación completa.")
    else:
        observations.append("La muñeca aparece por encima del hombro en el punto más alto detectado. Eso describe la posición, no confirma el instante exacto de salida del balón.")
    observations.append("Filmá también desde el frente y en cámara lenta; compará 5 tiros y mantené igual distancia, encuadre y velocidad antes de sacar conclusiones.")

    return {
        "metrics": metrics,
        "observations": observations,
        "limitations": [
            "La cámara sigue puntos del cuerpo; no detecta de forma independiente la pelota.",
            "El tiempo es una estimación del ascenso de muñeca hasta su punto más alto, no el tiempo exacto de salida del balón.",
            "Los ángulos dependen de la perspectiva, la oclusión y la calidad del video. No existe un ángulo universal perfecto para todos los tiradores.",
        ],
    }


@app.post("/api/analyze-shot")
async def analyze_shot(video: UploadFile = File(...), dominant_hand: str = Form("right")):
    if dominant_hand not in {"left", "right"}:
        raise HTTPException(status_code=400, detail="Elegí mano dominante derecha o izquierda.")
    suffix = Path(video.filename or "clip.mp4").suffix.lower()
    if suffix not in {".mp4", ".mov", ".m4v", ".avi", ".webm"}:
        raise HTTPException(status_code=400, detail="Formato no compatible. Usá MP4, MOV, M4V, AVI o WebM.")
    contents = await video.read()
    if len(contents) > 150 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo supera los 150 MB. Recortá el video e intentá de nuevo.")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            temp_path = tmp.name
        result = _analyze_video(temp_path, dominant_hand)
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        print(f"Video analysis error: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Falló el análisis del video. Probá un clip más corto y bien iluminado.") from exc
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.get("/api/health")
def health():
    return {"status": "ok"}
