import cv2
import mediapipe as mp
import time
import random
import csv
import os
from datetime import datetime

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Log
LOG_PATH = os.path.join(os.path.dirname(__file__), 'rps_log.csv')
try:
    lf = open(LOG_PATH, 'a', newline='', encoding='utf-8')
    logw = csv.writer(lf)
    if os.path.getsize(LOG_PATH) == 0:
        logw.writerow(['timestamp', 'player', 'ai', 'result'])
except Exception:
    lf = None
    logw = None


class AIPredictor:
    """Predictor simple que cuenta frecuencia de jugadas del jugador y elige la que le gana con probabilidad"""
    def __init__(self):
        self.counts = {'rock':0, 'paper':0, 'scissors':0}

    def update(self, player_move):
        if player_move in self.counts:
            self.counts[player_move] += 1

    def predict(self):
        # si no hay datos, random
        total = sum(self.counts.values())
        if total == 0:
            return random.choice(['rock','paper','scissors'])
        # elegir la jugada que vence a la más frecuente con 75% prob, sino random
        most = max(self.counts, key=lambda k: self.counts[k])
        # la jugada que le gana a 'most'
        beats = {'rock':'paper', 'paper':'scissors', 'scissors':'rock'}
        if random.random() < 0.75:
            return beats[most]
        return random.choice(['rock','paper','scissors'])


def classify_hand(hand_landmarks, handedness_label='Right'):
    """Clasifica rock/paper/scissors/unknown a partir de landmarks de MediaPipe Hands.
    Reglas simples: cuenta dedos levantados (index/middle/ring/pinky) comparando tip y pip;
    scissors = index+middle arriba, ring+pinky abajo; paper = 4 dedos arriba; rock = ninguno.
    """
    if hand_landmarks is None:
        return 'unknown'

    lm = hand_landmarks.landmark
    # índices de landmarks
    tips = [4, 8, 12, 16, 20]
    pips = [3, 6, 10, 14, 18]

    fingers_up = 0
    up_map = {'thumb':False, 'index':False, 'middle':False, 'ring':False, 'pinky':False}

    # Index, middle, ring, pinky: tip.y < pip.y => dedo extendido (imagen con origen arriba)
    for name, tip_i, pip_i in [('index',8,6), ('middle',12,10), ('ring',16,14), ('pinky',20,18)]:
        try:
            if lm[tip_i].y < lm[pip_i].y:
                fingers_up += 1
                up_map[name] = True
        except Exception:
            pass

    # Thumb: comparar tip.x vs ip.x teniendo en cuenta la mano
    try:
        # para la thumb usamos comparación horizontal
        if handedness_label == 'Right':
            up_map['thumb'] = lm[4].x < lm[3].x  # en espejo puede variar, suficiente como heurística
        else:
            up_map['thumb'] = lm[4].x > lm[3].x
        if up_map['thumb']:
            fingers_up += 1
    except Exception:
        pass

    # Reglas
    if fingers_up >= 4:
        return 'paper'
    # scissors: index y middle up, ring and pinky down
    if up_map['index'] and up_map['middle'] and not up_map['ring'] and not up_map['pinky']:
        return 'scissors'
    # rock: no dedos arriba o sólo thumb
    if fingers_up <= 1:
        return 'rock'

    return 'unknown'


def decide_winner(player, ai):
    if player == ai:
        return 'tie'
    beats = {'rock':'scissors', 'scissors':'paper', 'paper':'rock'}
    if beats[player] == ai:
        return 'player'
    return 'ai'


def main():
    ai = AIPredictor()
    score = {'player':0, 'ai':0, 'tie':0}
    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(min_detection_confidence=0.6, min_tracking_confidence=0.6, max_num_hands=1)

    playing = False
    round_result = None
    # tiempo de fin de la cuenta atrás (local a main)
    ROUND_END = 0

    print("Piedra-Papel-Tijeras por visión")
    print("Presiona SPACE para iniciar una ronda (cuenta atrás 3s). q o ESC para salir.")

    last_detected = 'unknown'

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            continue

        frame = cv2.flip(frame, 1)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        detected = 'unknown'
        handedness_label = 'Right'
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            if results.multi_handedness:
                handedness_label = results.multi_handedness[0].classification[0].label
            detected = classify_hand(hand_landmarks, handedness_label)
            last_detected = detected
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Overlay
        cv2.putText(frame, f"Detectado: {detected}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(frame, f"Score P:{score['player']}  AI:{score['ai']}  Ties:{score['tie']}", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,0), 2)
        cv2.putText(frame, "SPACE=iniciar ronda  r=reset  q=salir", (10,90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

        if playing:
            # mostrar cuenta atrás
            now = time.time()
            remain = int(ROUND_END - now)
            if remain >= 0:
                cv2.putText(frame, f"Cuenta atrás: {remain+1}", (10,130), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,128,255), 3)
            else:
                # fin ronda: usar last_detected como jugada del jugador
                player_move = last_detected if last_detected in ['rock','paper','scissors'] else 'rock'
                ai_move = ai.predict()
                result = decide_winner(player_move, ai_move)
                if result == 'player':
                    score['player'] += 1
                elif result == 'ai':
                    score['ai'] += 1
                else:
                    score['tie'] += 1

                ai.update(player_move)
                round_result = (player_move, ai_move, result)
                print(f"Ronda: player={player_move}  ai={ai_move}  resultado={result}")
                if logw:
                    logw.writerow([datetime.now().isoformat(), player_move, ai_move, result])
                    lf.flush()
                playing = False

        if round_result:
            pm, am, res = round_result
            cv2.putText(frame, f"Tu: {pm}  AI: {am}  -> {res}", (10,170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

        cv2.imshow('RPS Vision', frame)

        key = cv2.waitKey(5) & 0xFF
        if key == ord('q') or key == 27:
            break
        if key == ord('r'):
            score = {'player':0, 'ai':0, 'tie':0}
            print('Score reseteado')
        if key == 32 and not playing:  # SPACE
            # iniciar ronda con cuenta atrás 3s
            ROUND_END = time.time() + 3
            playing = True
            round_result = None

    cap.release()
    cv2.destroyAllWindows()
    if lf:
        lf.close()


if __name__ == '__main__':
    main()
