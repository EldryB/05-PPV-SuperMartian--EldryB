# Super Martian

## Bloque Especial y Llave

Comportamiento del bloque: En PlayState.py, se lee el área del bloque desde el mapa (key_block_rect). Se valida que el jugador lo golpee desde abajo comprobando que haya colisión mientras el jugador sube (self.player.vy < 0).
Animación de aparición: Al activarse, se agrega el objeto "llave" y de inmediato se usa Timer.tween para desplazar su posición y 16 píxeles hacia arriba durante 0.5 segundos, simulando que brota del bloque.
Finalización del nivel: Al recoger la llave (has_key = True), inicia un efecto de fade-out. Se usa otro Timer.tween de 5 segundos para animar el canal Alpha (transparencia) de un fondo negro hasta oscurecer la pantalla, llamando a la función finish_level() al terminar.

## Condición de Puntaje y Evento de Victoria

Puntaje objetivo: En GameLevel.py se definió la meta (self.goal_score = 250). El bloque sólo libera la llave si se cumple la condición: self.player.score >= self.game_level.goal_score.
Retroalimentación sonora: Justo al recoger la llave e iniciar el fade-out, se dispara el audio correspondiente con settings.SOUNDS["victory"].play().
Bloqueo del estado: Cuando el jugador obtiene la llave, ocurren 3 cosas:
Se detiene el temporizador (countdown_timer ignora los tics si el jugador tiene la llave).
Se desactiva la recolección de monedas (if self.player.has_key: continue en el bucle de colisión de items).
Se detienen las físicas y actualizaciones de pantalla (if self.is_fading_out: return), y las velocidades del jugador se congelan a 0 para que no caiga mientras se oscurece la pantalla.